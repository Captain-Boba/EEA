from __future__ import annotations

import base64
import csv
import hashlib
import io
import math
import re
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .config import (
    ATLAS_COUNTRIES,
    COUNTRIES,
    JRC_SOURCE_NAME,
    JRC_STORAGE_DASHBOARD_ENDPOINT,
    JRC_STORAGE_ENDPOINT,
    JRC_STORAGE_SOURCE_LABEL,
)


EXPECTED_COLUMNS = (
    "Country Code",
    "Snapshot Date",
    "Project Status",
    "Technology",
    "Subtechnology",
    "Power (MW)",
    "Capacity (MWh)",
)
ELECTRICITY_STORAGE_TECHNOLOGIES = frozenset({"Electrochemical", "Mechanical"})
JRC_EXPORT_COUNTRIES = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Switzerland": "CH",
    "Czechia": "CZ", "Germany": "DE", "Denmark": "DK", "Spain": "ES",
    "Estonia": "EE", "Finland": "FI", "France": "FR", "United Kingdom": "UK",
    "Greece": "GR", "Croatia": "HR", "Hungary": "HU", "Ireland": "IE",
    "Italy": "IT", "Lithuania": "LT", "Luxembourg": "LU", "Latvia": "LV",
    "Montenegro": "ME", "North Macedonia": "MK", "Netherlands": "NL",
    "Norway": "NO", "Poland": "PL", "Portugal": "PT", "Romania": "RO",
    "Serbia": "RS", "Slovakia": "SK", "Slovenia": "SI", "Sweden": "SE",
}
KNOWN_NON_ATLAS_EXPORT_COUNTRIES = frozenset(
    {"Albania", "Bosnia and Herzegovina", "Turkey", "Ukraine"}
)
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
JRC_INVENTORY_SERIES = "tracked_project_inventory"
JRC_DASHBOARD_EXPORTS = {
    ("battery", "power"): f"{JRC_STORAGE_DASHBOARD_ENDPOINT}/electrochemical-power-xlsx",
    ("battery", "capacity"): f"{JRC_STORAGE_DASHBOARD_ENDPOINT}/electrochemical-capacity-xlsx",
    ("pumped_storage", "power"): f"{JRC_STORAGE_DASHBOARD_ENDPOINT}/pumped-hydro-power-xlsx",
    ("pumped_storage", "capacity"): f"{JRC_STORAGE_DASHBOARD_ENDPOINT}/pumped-hydro-capacity-xlsx",
}


class StorageImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class StorageAggregate:
    country_code: str
    snapshot_date: str
    power_gw: float | None
    energy_gwh: float | None


@dataclass(frozen=True)
class StorageCachePayload:
    endpoint: str
    path: Path
    payload_bytes: bytes
    request_url: str | None = None
    fetched_at: str | None = None
    status_code: int = 200
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None


class JrcStorageImporter:
    """Import a user-downloaded, explicitly shaped JRC export without web scraping."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def import_file(self, path: Path | str) -> dict[str, Any]:
        source_path = Path(path)
        payload_bytes = source_path.read_bytes()
        try:
            payload_text = payload_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise StorageImportError("JRC storage CSV is not valid UTF-8") from exc
        rows = self._validate(payload_text)
        snapshot_dates = {row.snapshot_date for row in rows}
        if len(snapshot_dates) != 1:
            raise StorageImportError("JRC storage CSV must contain exactly one snapshot date")
        snapshot_date = next(iter(snapshot_dates))
        normalized: list[tuple[Any, ...]] = []
        for row in rows:
            if row.power_gw is not None:
                normalized.append((row.country_code, snapshot_date, snapshot_date, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_electricity_storage", "storage_power_gw", row.power_gw, "GW", "source_reported_including_estimates"))
            if row.energy_gwh is not None:
                normalized.append((row.country_code, snapshot_date, snapshot_date, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_electricity_storage", "storage_energy_gwh", row.energy_gwh, "GWh", "source_reported_including_estimates"))
            if row.power_gw and row.energy_gwh:
                normalized.append((row.country_code, snapshot_date, snapshot_date, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_electricity_storage", "storage_duration_hours", row.energy_gwh / row.power_gw, "h", "derived_from_jrc_power_and_energy"))
        if not normalized:
            raise StorageImportError("JRC storage CSV contains no operational electricity-storage values")

        cache = StorageCachePayload(JRC_STORAGE_ENDPOINT, source_path, payload_bytes)
        replaced = self._replace(normalized, [cache], text_payloads={cache.endpoint: payload_text})
        sha256 = hashlib.sha256(payload_bytes).hexdigest()
        return {
            "source": JRC_SOURCE_NAME,
            "endpoint": JRC_STORAGE_ENDPOINT,
            "snapshot_date": snapshot_date,
            "countries_with_values": len({row.country_code for row in rows}),
            "rows": len(normalized),
            "replaced_rows": replaced,
            "sha256": sha256,
        }

    def import_exports(
        self,
        power_path: Path | str,
        capacity_path: Path | str,
        snapshot_date: str,
    ) -> dict[str, Any]:
        try:
            snapshot = date.fromisoformat(snapshot_date).isoformat()
        except ValueError as exc:
            raise StorageImportError("JRC snapshot date must use YYYY-MM-DD") from exc
        power_source = Path(power_path)
        capacity_source = Path(capacity_path)
        power_bytes = power_source.read_bytes()
        capacity_bytes = capacity_source.read_bytes()
        power = self._read_dashboard_export(power_bytes, "Power (GW)")
        capacity = self._read_dashboard_export(capacity_bytes, "Capacity (GWh)")
        countries = sorted(set(power) | set(capacity))
        normalized: list[tuple[Any, ...]] = []
        for code in countries:
            if code in power:
                normalized.append((code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_mechanical_and_electrochemical", "storage_power_gw", power[code], "GW", "source_reported_including_estimates"))
            if code in capacity:
                normalized.append((code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_mechanical_and_electrochemical", "storage_energy_gwh", capacity[code], "GWh", "source_reported_including_estimates"))
            if code in power and code in capacity and power[code] > 0:
                normalized.append((code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, "operational_mechanical_and_electrochemical", "storage_duration_hours", capacity[code] / power[code], "h", "derived_from_jrc_power_and_energy"))
        if not normalized:
            raise StorageImportError("JRC dashboard exports contain no Atlas storage values")
        cache_payloads = [
            StorageCachePayload(f"{JRC_STORAGE_ENDPOINT}/power-xlsx", power_source, power_bytes),
            StorageCachePayload(f"{JRC_STORAGE_ENDPOINT}/capacity-xlsx", capacity_source, capacity_bytes),
        ]
        replaced = self._replace(normalized, cache_payloads)
        return {
            "source": JRC_SOURCE_NAME,
            "endpoint": JRC_STORAGE_ENDPOINT,
            "snapshot_date": snapshot,
            "countries_with_values": len(countries),
            "countries_missing": sorted(set(ATLAS_COUNTRIES) - set(countries)),
            "rows": len(normalized),
            "replaced_rows": replaced,
            "power_sha256": hashlib.sha256(power_bytes).hexdigest(),
            "capacity_sha256": hashlib.sha256(capacity_bytes).hexdigest(),
        }

    def import_dashboard_categories(
        self,
        exports: dict[tuple[str, str], StorageCachePayload],
        snapshot_date: str,
    ) -> dict[str, Any]:
        """Atomically import the four filtered official-dashboard exports.

        The dashboard is used only for aggregation and download.  The four raw
        XLSX responses are retained verbatim so a later refresh remains
        traceable without keeping short-lived Qlik download URLs.
        """
        try:
            snapshot = date.fromisoformat(snapshot_date).isoformat()
        except ValueError as exc:
            raise StorageImportError("JRC snapshot date must use YYYY-MM-DD") from exc
        expected = set(JRC_DASHBOARD_EXPORTS)
        if set(exports) != expected:
            missing = sorted("/".join(item) for item in expected - set(exports))
            extra = sorted("/".join(item) for item in set(exports) - expected)
            raise StorageImportError(
                "JRC dashboard exports must contain exactly battery/pumped_storage power/capacity"
                + (f"; missing: {', '.join(missing)}" if missing else "")
                + (f"; unexpected: {', '.join(extra)}" if extra else "")
            )

        parsed: dict[tuple[str, str], dict[str, float]] = {}
        for key, cache in exports.items():
            kind, dimension = key
            expected_endpoint = JRC_DASHBOARD_EXPORTS[key]
            if cache.endpoint != expected_endpoint:
                raise StorageImportError(f"JRC dashboard export endpoint is invalid for {kind}/{dimension}")
            header = "Power (GW)" if dimension == "power" else "Capacity (GWh)"
            parsed[key] = self._read_dashboard_export(cache.payload_bytes, header)

        normalized: list[tuple[Any, ...]] = []
        coverage: dict[str, dict[str, list[str]]] = {}
        for kind in ("battery", "pumped_storage"):
            power = parsed[(kind, "power")]
            capacity = parsed[(kind, "capacity")]
            codes = sorted(set(power) | set(capacity))
            coverage[kind] = {
                "countries_with_values": codes,
                "countries_missing": sorted(set(ATLAS_COUNTRIES) - set(codes)),
            }
            for code in codes:
                # Germany uses the national Battery-Charts total exclusively.
                if kind == "battery" and code == "DE":
                    continue
                series = f"{JRC_INVENTORY_SERIES}:{kind}"
                if code in power:
                    normalized.append((
                        code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME,
                        JRC_STORAGE_DASHBOARD_ENDPOINT, series, f"{kind}_power_gw",
                        power[code], "GW", "source_reported_including_estimates",
                    ))
                if code in capacity:
                    normalized.append((
                        code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME,
                        JRC_STORAGE_DASHBOARD_ENDPOINT, series, f"{kind}_energy_gwh",
                        capacity[code], "GWh", "source_reported_including_estimates",
                    ))
                if code in power and code in capacity and power[code] > 0:
                    normalized.append((
                        code, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME,
                        JRC_STORAGE_DASHBOARD_ENDPOINT, series, f"{kind}_duration_hours",
                        capacity[code] / power[code], "h", "derived_from_jrc_power_and_energy",
                    ))
        if not normalized:
            raise StorageImportError("JRC dashboard exports contain no operational Atlas storage values")

        replaced = self._replace_dashboard_categories(normalized, list(exports.values()))
        return {
            "source": JRC_SOURCE_NAME,
            "endpoint": JRC_STORAGE_DASHBOARD_ENDPOINT,
            "snapshot_date": snapshot,
            "rows": len(normalized),
            "replaced_rows": replaced,
            "exports": len(exports),
            "battery": coverage["battery"],
            "pumped_storage": coverage["pumped_storage"],
        }

    def _replace(
        self,
        normalized: list[tuple[Any, ...]],
        cache_payloads: list[StorageCachePayload],
        *,
        text_payloads: dict[str, str] | None = None,
    ) -> int:
        fetched_at = datetime.now(UTC).isoformat()
        self.connection.execute("SAVEPOINT jrc_storage_import")
        try:
            replaced = self.connection.execute(
                "SELECT COUNT(*) FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT),
            ).fetchone()[0]
            self.connection.execute(
                "DELETE FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT),
            )
            self.connection.execute(
                "DELETE FROM source_cache WHERE source=? AND (endpoint=? OR endpoint LIKE ?)",
                (JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, f"{JRC_STORAGE_ENDPOINT}/%"),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                normalized,
            )
            for cache in cache_payloads:
                is_text = text_payloads is not None and cache.endpoint in text_payloads
                payload_text = (
                    text_payloads[cache.endpoint]
                    if is_text
                    else "base64:" + base64.b64encode(cache.payload_bytes).decode("ascii")
                )
                content_type = "text/csv" if is_text else XLSX_CONTENT_TYPE
                self.connection.execute(
                    """INSERT INTO source_cache
                       (source,endpoint,request_url,fetched_at,status_code,content_type,etag,last_modified,sha256,payload_text)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(source,endpoint) DO UPDATE SET
                         request_url=excluded.request_url,fetched_at=excluded.fetched_at,
                         status_code=excluded.status_code,content_type=excluded.content_type,
                         etag=excluded.etag,last_modified=excluded.last_modified,
                         sha256=excluded.sha256,payload_text=excluded.payload_text""",
                    (JRC_SOURCE_NAME, cache.endpoint, f"manual-file:{cache.path.name}", fetched_at, 200, content_type, None, None, hashlib.sha256(cache.payload_bytes).hexdigest(), payload_text),
                )
            self.connection.execute("RELEASE SAVEPOINT jrc_storage_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT jrc_storage_import")
            self.connection.execute("RELEASE SAVEPOINT jrc_storage_import")
            raise
        return replaced

    def _replace_dashboard_categories(
        self,
        normalized: list[tuple[Any, ...]],
        cache_payloads: list[StorageCachePayload],
    ) -> int:
        """Replace only JRC's resolved battery/pumped-storage observations.

        This deliberately leaves JRC hydro inventory observations alone.  It
        also removes values from the previously used undocumented JSON route
        in the same short transaction, so a failed dashboard refresh can never
        produce a mixed old/new storage snapshot.
        """
        metrics = (
            "battery_power_gw", "battery_energy_gwh", "battery_duration_hours",
            "pumped_storage_power_gw", "pumped_storage_energy_gwh", "pumped_storage_duration_hours",
        )
        placeholders = ",".join("?" for _ in metrics)
        self.connection.execute("SAVEPOINT jrc_dashboard_import")
        try:
            replaced = self.connection.execute(
                f"SELECT COUNT(*) FROM period_observation WHERE source=? AND metric IN ({placeholders})",
                (JRC_SOURCE_NAME, *metrics),
            ).fetchone()[0]
            self.connection.execute(
                f"DELETE FROM period_observation WHERE source=? AND metric IN ({placeholders})",
                (JRC_SOURCE_NAME, *metrics),
            )
            self.connection.execute(
                "DELETE FROM source_cache WHERE source=? AND endpoint LIKE ?",
                (JRC_SOURCE_NAME, "european-energy-storage-inventory/%"),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                normalized,
            )
            self._write_cache_payloads(cache_payloads)
            self.connection.execute("RELEASE SAVEPOINT jrc_dashboard_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT jrc_dashboard_import")
            self.connection.execute("RELEASE SAVEPOINT jrc_dashboard_import")
            raise
        return replaced

    def _write_cache_payloads(
        self,
        cache_payloads: list[StorageCachePayload],
        *,
        text_payloads: dict[str, str] | None = None,
    ) -> None:
        default_fetched_at = datetime.now(UTC).isoformat()
        for cache in cache_payloads:
            is_text = text_payloads is not None and cache.endpoint in text_payloads
            payload_text = (
                text_payloads[cache.endpoint]
                if is_text
                else "base64:" + base64.b64encode(cache.payload_bytes).decode("ascii")
            )
            content_type = cache.content_type or ("text/csv" if is_text else XLSX_CONTENT_TYPE)
            request_url = cache.request_url or f"manual-file:{cache.path.name}"
            self.connection.execute(
                """INSERT INTO source_cache
                   (source,endpoint,request_url,fetched_at,status_code,content_type,etag,last_modified,sha256,payload_text)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(source,endpoint) DO UPDATE SET
                     request_url=excluded.request_url,fetched_at=excluded.fetched_at,
                     status_code=excluded.status_code,content_type=excluded.content_type,
                     etag=excluded.etag,last_modified=excluded.last_modified,
                     sha256=excluded.sha256,payload_text=excluded.payload_text""",
                (
                    JRC_SOURCE_NAME, cache.endpoint, request_url,
                    cache.fetched_at or default_fetched_at, cache.status_code, content_type,
                    cache.etag, cache.last_modified, hashlib.sha256(cache.payload_bytes).hexdigest(), payload_text,
                ),
            )

    def _read_dashboard_export(self, payload_bytes: bytes, value_header: str) -> dict[str, float]:
        rows = self._xlsx_rows(payload_bytes)
        if not rows or rows[0] != ["Country", "Project status", value_header]:
            raise StorageImportError(
                f"JRC dashboard export header changed; expected Country, Project status, {value_header}"
            )
        values: dict[str, float] = {}
        for line_number, row in enumerate(rows[1:], start=2):
            if len(row) != 3:
                raise StorageImportError(f"JRC dashboard export row {line_number} has the wrong field count")
            country_name = str(row[0]).strip()
            status = str(row[1]).strip()
            if status != "Operational":
                raise StorageImportError(f"JRC dashboard export row {line_number} is not Operational")
            if country_name in KNOWN_NON_ATLAS_EXPORT_COUNTRIES:
                continue
            code = JRC_EXPORT_COUNTRIES.get(country_name)
            if code is None:
                raise StorageImportError(f"JRC dashboard export row {line_number} has unknown country {country_name!r}")
            if code in values:
                raise StorageImportError(f"JRC dashboard export contains duplicate country {country_name}")
            number = self._number(row[2], line_number, value_header)
            values[code] = number
        return values

    @staticmethod
    def _xlsx_rows(payload_bytes: bytes) -> list[list[Any]]:
        try:
            with zipfile.ZipFile(io.BytesIO(payload_bytes)) as archive:
                shared_strings: list[str] = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                    shared_strings = ["".join(node.itertext()) for node in root]
                sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
            raise StorageImportError("JRC dashboard export is not a readable XLSX workbook") from exc
        namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        rows: list[list[Any]] = []
        for row_node in sheet.iter(f"{namespace}row"):
            cells: dict[int, Any] = {}
            for cell in row_node.findall(f"{namespace}c"):
                reference = cell.attrib.get("r", "")
                match = re.match(r"([A-Z]+)", reference)
                if not match:
                    raise StorageImportError("JRC dashboard export contains an invalid cell reference")
                column = 0
                for character in match.group(1):
                    column = column * 26 + ord(character) - 64
                cell_type = cell.attrib.get("t")
                if cell_type == "inlineStr":
                    inline = cell.find(f"{namespace}is")
                    value: Any = "" if inline is None else "".join(inline.itertext())
                else:
                    value_node = cell.find(f"{namespace}v")
                    raw = "" if value_node is None else value_node.text or ""
                    if cell_type == "s":
                        try:
                            value = shared_strings[int(raw)]
                        except (ValueError, IndexError) as exc:
                            raise StorageImportError("JRC dashboard export has an invalid shared string") from exc
                    elif cell_type == "str":
                        value = raw
                    else:
                        try:
                            value = float(raw)
                        except ValueError:
                            value = raw
                cells[column - 1] = value
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(index, "") for index in range(width)])
        return rows

    @staticmethod
    def _number(value: Any, line_number: int, label: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise StorageImportError(f"JRC dashboard export row {line_number} has non-numeric {label}") from exc
        if not math.isfinite(number) or number < 0:
            raise StorageImportError(f"JRC dashboard export row {line_number} has invalid {label}")
        return number

    def _validate(self, payload_text: str) -> list[StorageAggregate]:
        if not payload_text.strip():
            raise StorageImportError("JRC storage CSV is empty")
        reader = csv.DictReader(io.StringIO(payload_text, newline=""))
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise StorageImportError(f"JRC storage CSV header changed; expected {', '.join(EXPECTED_COLUMNS)}")
        totals: dict[tuple[str, str], dict[str, float | None]] = {}
        seen_projects: set[tuple[str, str, str, str, str, str, str]] = set()
        for line_number, record in enumerate(reader, start=2):
            if None in record or any(record[column] is None for column in EXPECTED_COLUMNS):
                raise StorageImportError(f"JRC storage CSV row {line_number} has the wrong field count")
            code = record["Country Code"].strip().upper()
            if code not in ATLAS_COUNTRIES:
                raise StorageImportError(f"JRC storage CSV row {line_number} has unknown country code {code!r}")
            try:
                snapshot = date.fromisoformat(record["Snapshot Date"].strip()).isoformat()
            except ValueError as exc:
                raise StorageImportError(f"JRC storage CSV row {line_number} has an invalid snapshot date") from exc
            key = tuple(record[column].strip() for column in EXPECTED_COLUMNS)
            if key in seen_projects:
                raise StorageImportError(f"JRC storage CSV contains a duplicate row at line {line_number}")
            seen_projects.add(key)
            if record["Project Status"].strip().casefold() != "operational":
                continue
            if record["Technology"].strip() not in ELECTRICITY_STORAGE_TECHNOLOGIES:
                continue
            power = self._optional_number(record["Power (MW)"], line_number, "power")
            energy = self._optional_number(record["Capacity (MWh)"], line_number, "capacity")
            aggregate = totals.setdefault((code, snapshot), {"power": None, "energy": None})
            if power is not None:
                aggregate["power"] = (aggregate["power"] or 0.0) + power / 1000
            if energy is not None:
                aggregate["energy"] = (aggregate["energy"] or 0.0) + energy / 1000
        return [StorageAggregate(code, snapshot, values["power"], values["energy"]) for (code, snapshot), values in totals.items()]

    @staticmethod
    def _optional_number(value: str, line_number: int, label: str) -> float | None:
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError as exc:
            raise StorageImportError(f"JRC storage CSV row {line_number} has non-numeric {label}") from exc
        if not math.isfinite(number) or number < 0:
            raise StorageImportError(f"JRC storage CSV row {line_number} has invalid {label}")
        return number


def latest_storage(connection: sqlite3.Connection) -> dict[str, Any]:
    snapshot = connection.execute(
        "SELECT MAX(period_start) FROM period_observation WHERE source=? AND source_endpoint=?",
        (JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT),
    ).fetchone()[0]
    if snapshot is None:
        return {
            "snapshot_date": None,
            "source": JRC_SOURCE_NAME,
            "source_label": JRC_STORAGE_SOURCE_LABEL,
            "source_endpoint": JRC_STORAGE_ENDPOINT,
            "countries": [],
        }
    rows = connection.execute(
        """SELECT country_code,metric,value,unit,quality_status FROM period_observation
           WHERE source=? AND source_endpoint=? AND period_start=? ORDER BY country_code,metric""",
        (JRC_SOURCE_NAME, JRC_STORAGE_ENDPOINT, snapshot),
    )
    countries: dict[str, dict[str, Any]] = {
        code: {
            "country_code": code,
            "country_name": country.name,
            "quality_status": "missing",
            "storage_power_gw": None,
            "storage_energy_gwh": None,
            "storage_duration_hours": None,
        }
        for code, country in COUNTRIES.items()
    }
    for row in rows:
        country = countries[row["country_code"]]
        country[row["metric"]] = row["value"]
        if row["metric"] != "storage_duration_hours":
            country["quality_status"] = row["quality_status"]
    countries_with_values = sum(
        country["storage_power_gw"] is not None or country["storage_energy_gwh"] is not None
        for country in countries.values()
    )
    return {
        "snapshot_date": snapshot,
        "source": JRC_SOURCE_NAME,
        "source_label": JRC_STORAGE_SOURCE_LABEL,
        "source_endpoint": JRC_STORAGE_ENDPOINT,
        "countries_with_values": countries_with_values,
        "countries_missing": [
            code
            for code, country in countries.items()
            if country["storage_power_gw"] is None and country["storage_energy_gwh"] is None
        ],
        "countries": list(countries.values()),
    }
