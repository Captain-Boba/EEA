from __future__ import annotations

import csv
import hashlib
import io
import math
import sqlite3
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import (
    ATLAS_COUNTRIES,
    JRC_HYDRO_ENDPOINT,
    JRC_HYDRO_RELEASE_DATE,
    JRC_HYDRO_URL,
    JRC_SOURCE_NAME,
)


class HydroImportError(RuntimeError):
    pass


HYDRO_METRICS = (
    "hydro_plant_capacity_gw",
    "hydro_pumping_power_gw",
    "hydro_reservoir_energy_gwh",
)


class JrcHydroImporter:
    def __init__(self, connection: sqlite3.Connection, url: str = JRC_HYDRO_URL, timeout: int = 90):
        self.connection = connection
        self.url = url
        self.timeout = timeout

    def import_release(self) -> dict[str, Any]:
        request = Request(self.url, headers={"User-Agent": "European-Electricity-Atlas/0.1 (annual open-data importer)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                status = response.status
                content_type = response.headers.get("Content-Type")
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
        except (HTTPError, URLError) as exc:
            raise HydroImportError(f"JRC hydro download failed: {exc}") from exc
        fetched_at = datetime.now(UTC).isoformat()
        sha256 = hashlib.sha256(payload).hexdigest()
        normalized = self._normalize(payload)
        if not normalized:
            raise HydroImportError("JRC hydro response contained no Atlas data")

        self.connection.execute("SAVEPOINT jrc_hydro_import")
        try:
            replaced = self.connection.execute(
                "SELECT COUNT(*) FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_HYDRO_ENDPOINT),
            ).fetchone()[0]
            self.connection.execute(
                "DELETE FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_HYDRO_ENDPOINT),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,'snapshot',?,?,?,?,?,?,?)""",
                normalized,
            )
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
                    JRC_SOURCE_NAME,
                    JRC_HYDRO_ENDPOINT,
                    self.url,
                    fetched_at,
                    status,
                    content_type,
                    etag,
                    last_modified,
                    sha256,
                    payload.decode("utf-8-sig"),
                ),
            )
            self.connection.execute("RELEASE SAVEPOINT jrc_hydro_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT jrc_hydro_import")
            self.connection.execute("RELEASE SAVEPOINT jrc_hydro_import")
            raise
        return {
            "source": JRC_SOURCE_NAME,
            "rows": len(normalized),
            "countries_with_values": len({row[0] for row in normalized}),
            "countries_missing": sorted(set(ATLAS_COUNTRIES) - {row[0] for row in normalized}),
            "release_date": JRC_HYDRO_RELEASE_DATE,
            "sha256": sha256,
            "replaced_rows": replaced,
        }

    def _normalize(self, payload: bytes) -> list[tuple[Any, ...]]:
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HydroImportError("JRC hydro response is not UTF-8 CSV") from exc
        reader = csv.DictReader(io.StringIO(text))
        required = {
            "installed_capacity_MW",
            "pumping_MW",
            "country_code",
            "storage_capacity_MWh",
        }
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise HydroImportError("JRC hydro CSV structure changed")
        totals: dict[str, dict[str, float]] = {}
        counts: dict[str, dict[str, int]] = {}
        for row in reader:
            code = (row.get("country_code") or "").strip().upper()
            code = {"EL": "GR", "GB": "UK"}.get(code, code)
            if code not in ATLAS_COUNTRIES:
                continue
            country_totals = totals.setdefault(code, {metric: 0.0 for metric in HYDRO_METRICS})
            country_counts = counts.setdefault(code, {metric: 0 for metric in HYDRO_METRICS})
            for column, metric, scale in (
                ("installed_capacity_MW", "hydro_plant_capacity_gw", 0.001),
                ("pumping_MW", "hydro_pumping_power_gw", 0.001),
                ("storage_capacity_MWh", "hydro_reservoir_energy_gwh", 0.001),
            ):
                raw = (row.get(column) or "").strip()
                if not raw:
                    continue
                try:
                    value = float(raw) * scale
                except ValueError as exc:
                    raise HydroImportError(f"JRC hydro {column} contains a non-numeric value") from exc
                if not math.isfinite(value) or value < 0:
                    raise HydroImportError(f"JRC hydro {column} contains an invalid value")
                country_totals[metric] += value
                country_counts[metric] += 1

        rows: list[tuple[Any, ...]] = []
        units = {
            "hydro_plant_capacity_gw": "GW",
            "hydro_pumping_power_gw": "GW",
            "hydro_reservoir_energy_gwh": "GWh",
        }
        for code, country_totals in totals.items():
            for metric in HYDRO_METRICS:
                if counts[code][metric] == 0:
                    continue
                rows.append(
                    (
                        code,
                        JRC_HYDRO_RELEASE_DATE,
                        JRC_HYDRO_RELEASE_DATE,
                        JRC_SOURCE_NAME,
                        JRC_HYDRO_ENDPOINT,
                        "release-01:reported-plants",
                        metric,
                        country_totals[metric],
                        units[metric],
                        "source_inventory_incomplete",
                    )
                )
        return rows
