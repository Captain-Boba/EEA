from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .config import (
    ATLAS_COUNTRIES,
    ATLAS_MIN_YEAR,
    BATTERY_CHARTS_API_URL,
    BATTERY_CHARTS_COMBINED_ENDPOINT,
    BATTERY_CHARTS_ENERGY_ENDPOINT,
    BATTERY_CHARTS_POWER_ENDPOINT,
    BATTERY_CHARTS_SOURCE_LABEL,
    BATTERY_CHARTS_SOURCE_NAME,
    JRC_STORAGE_API_ENDPOINT,
    JRC_STORAGE_API_URL,
    JRC_STORAGE_SOURCE_LABEL,
    JRC_SOURCE_NAME,
)
from .storage_importer import JRC_EXPORT_COUNTRIES, KNOWN_NON_ATLAS_EXPORT_COUNTRIES


STORAGE_METRICS = (
    "battery_power_gw",
    "battery_energy_gwh",
    "battery_duration_hours",
    "pumped_storage_power_gw",
    "pumped_storage_energy_gwh",
    "pumped_storage_duration_hours",
)
BATTERY_SEGMENTS = ("home", "industrial", "grossspeicher")
BATTERY_TOTAL_SERIES = "national_registry_total"
JRC_INVENTORY_SERIES = "tracked_project_inventory"
BATTERY_CHARTS_ONLINE_ACCESS_ENABLED = False


class StorageOnlineError(RuntimeError):
    pass


class BatteryChartsKeyError(StorageOnlineError):
    pass


@dataclass(frozen=True)
class SourceDownload:
    source: str
    endpoint: str
    request_url: str
    fetched_at: str
    status_code: int
    content_type: str | None
    etag: str | None
    last_modified: str | None
    sha256: str
    payload_text: str


def load_battery_charts_api_key(path: Path | str = "BATTERY_CHARTS_API_KEY.txt") -> str:
    value = os.environ.get("BATTERY_CHARTS_API_KEY")
    if value is None:
        key_path = Path(path)
        if key_path.is_file():
            value = key_path.read_text(encoding="utf-8")
    value = value.strip() if value is not None else ""
    if not value:
        raise BatteryChartsKeyError(
            "BATTERY_CHARTS_API_KEY is missing; set the environment variable or use BATTERY_CHARTS_API_KEY.txt"
        )
    return value


def _redact_url(url: str) -> str:
    parts = urlsplit(url)
    query = [(key, "REDACTED" if key.casefold() == "api_key" else value) for key, value in parse_qsl(parts.query)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class ConservativeJsonClient:
    def __init__(
        self,
        *,
        timeout: float = 60,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] | None = None,
    ):
        self.timeout = timeout
        self.opener = opener
        self.sleeper = sleeper
        self.now = now or (lambda: datetime.now(UTC))

    def _fetch(
        self,
        *,
        source: str,
        endpoint: str,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> SourceDownload:
        headers = {
            "Accept": "application/json",
            "User-Agent": "European-Electricity-Atlas/0.1 (conservative monthly storage importer)",
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        request = Request(url, headers=headers)
        for attempt in range(2):
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    payload = response.read()
                    status = response.status
                    response_headers = response.headers
                break
            except HTTPError as exc:
                if exc.code == 304:
                    return SourceDownload(
                        source, endpoint, _redact_url(url), self.now().isoformat(), 304,
                        exc.headers.get("Content-Type"), exc.headers.get("ETag") or etag,
                        exc.headers.get("Last-Modified") or last_modified, "", "",
                    )
                if exc.code in {403, 429}:
                    retry_after = self._retry_after(exc.headers.get("Retry-After"))
                    suffix = f"; retry after {math.ceil(retry_after)} seconds" if retry_after is not None else ""
                    raise StorageOnlineError(f"{source} {endpoint} returned HTTP {exc.code}{suffix}") from exc
                if exc.code not in {500, 502, 503, 504} or attempt == 1:
                    raise StorageOnlineError(f"{source} {endpoint} returned HTTP {exc.code}") from exc
                self.sleeper(max(10.0, self._retry_after(exc.headers.get("Retry-After")) or 0.0))
            except TimeoutError as exc:
                if attempt == 1:
                    raise StorageOnlineError(f"{source} {endpoint} timed out") from exc
                self.sleeper(10.0)
            except URLError as exc:
                if not isinstance(exc.reason, TimeoutError):
                    raise StorageOnlineError(f"{source} {endpoint} could not be reached") from exc
                if attempt == 1:
                    raise StorageOnlineError(f"{source} {endpoint} timed out") from exc
                self.sleeper(10.0)
        else:  # pragma: no cover
            raise StorageOnlineError(f"{source} {endpoint} download failed")

        if status != 200:
            raise StorageOnlineError(f"{source} {endpoint} returned HTTP {status}")
        try:
            payload_text = payload.decode("utf-8-sig")
            json.loads(payload_text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageOnlineError(f"{source} {endpoint} returned invalid JSON") from exc
        return SourceDownload(
            source=source,
            endpoint=endpoint,
            request_url=_redact_url(url),
            fetched_at=self.now().isoformat(),
            status_code=status,
            content_type=response_headers.get("Content-Type"),
            etag=response_headers.get("ETag"),
            last_modified=response_headers.get("Last-Modified"),
            sha256=hashlib.sha256(payload).hexdigest(),
            payload_text=payload_text,
        )

    def _retry_after(self, value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(float(value), 0.0)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return max((parsed - self.now()).total_seconds(), 0.0)
            except (TypeError, ValueError):
                return None


class JrcStorageClient(ConservativeJsonClient):
    def __init__(self, url: str = JRC_STORAGE_API_URL, **kwargs: Any):
        super().__init__(**kwargs)
        self.url = url

    def fetch(self, *, etag: str | None = None, last_modified: str | None = None) -> SourceDownload:
        return self._fetch(
            source=JRC_SOURCE_NAME,
            endpoint=JRC_STORAGE_API_ENDPOINT,
            url=self.url,
            etag=etag,
            last_modified=last_modified,
        )


class BatteryChartsClient(ConservativeJsonClient):
    def __init__(
        self,
        api_key: str,
        url: str = BATTERY_CHARTS_API_URL,
        minimum_delay: float = 2.0,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if not api_key.strip():
            raise BatteryChartsKeyError("BATTERY_CHARTS_API_KEY is empty")
        self.api_key = api_key.strip()
        self.url = url
        self.minimum_delay = max(2.0, minimum_delay)

    def fetch_pair(self, cached: dict[str, sqlite3.Row] | None = None) -> tuple[SourceDownload, SourceDownload]:
        if not BATTERY_CHARTS_ONLINE_ACCESS_ENABLED:
            raise StorageOnlineError(
                "Battery-Charts online access is disabled; use import-battery-storage with local JSON files"
            )
        cached = cached or {}
        energy = self._fetch_query(BATTERY_CHARTS_ENERGY_ENDPOINT, cached.get(BATTERY_CHARTS_ENERGY_ENDPOINT))
        self.sleeper(self.minimum_delay)
        power = self._fetch_query(BATTERY_CHARTS_POWER_ENDPOINT, cached.get(BATTERY_CHARTS_POWER_ENDPOINT))
        return energy, power

    def _fetch_query(self, endpoint: str, cached: sqlite3.Row | None) -> SourceDownload:
        url = f"{self.url}?{urlencode({'api_key': self.api_key, 'query_id': endpoint})}"
        return self._fetch(
            source=BATTERY_CHARTS_SOURCE_NAME,
            endpoint=endpoint,
            url=url,
            etag=cached["etag"] if cached else None,
            last_modified=cached["last_modified"] if cached else None,
        )


def _cache_write(connection: sqlite3.Connection, download: SourceDownload) -> None:
    connection.execute(
        """INSERT INTO source_cache
           (source,endpoint,request_url,fetched_at,status_code,content_type,etag,last_modified,sha256,payload_text)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(source,endpoint) DO UPDATE SET
             request_url=excluded.request_url,fetched_at=excluded.fetched_at,
             status_code=excluded.status_code,content_type=excluded.content_type,
             etag=excluded.etag,last_modified=excluded.last_modified,
             sha256=excluded.sha256,payload_text=excluded.payload_text""",
        (
            download.source, download.endpoint, download.request_url, download.fetched_at,
            download.status_code, download.content_type, download.etag, download.last_modified,
            download.sha256, download.payload_text,
        ),
    )


class BatteryChartsImporter:
    def __init__(self, connection: sqlite3.Connection, today: date | None = None):
        self.connection = connection
        self.today = today or date.today()

    def import_files(self, energy_path: Path | str, power_path: Path | str) -> dict[str, Any]:
        energy = self._local_download(Path(energy_path), BATTERY_CHARTS_ENERGY_ENDPOINT)
        power = self._local_download(Path(power_path), BATTERY_CHARTS_POWER_ENDPOINT)
        result = self.import_downloads(energy, power)
        result["import_mode"] = "manual_json_files"
        return result

    def import_downloads(self, energy: SourceDownload, power: SourceDownload) -> dict[str, Any]:
        if energy.status_code not in {200, 304} or power.status_code not in {200, 304}:
            raise StorageOnlineError("Battery-Charts responses must be successful JSON responses")
        if not energy.payload_text or not power.payload_text:
            raise StorageOnlineError("Battery-Charts conditional response is missing its cached payload")
        energy_rows = self._series(energy, "energy")
        power_rows = self._series(power, "power")
        if set(energy_rows) != set(power_rows):
            raise StorageOnlineError("Battery-Charts energy and power do not cover identical monthly dates")
        if not energy_rows:
            raise StorageOnlineError(f"Battery-Charts contains no data from {ATLAS_MIN_YEAR}")

        normalized: list[tuple[Any, ...]] = []
        for raw_date in sorted(energy_rows):
            point_date = date.fromisoformat(raw_date)
            month_start = point_date.replace(day=1)
            month_end = month_start.replace(day=calendar.monthrange(point_date.year, point_date.month)[1])
            quality = "provisional_current_month" if point_date != month_end else "observed"
            energy_segments = energy_rows[raw_date]
            power_segments = power_rows[raw_date]
            for segment in (*BATTERY_SEGMENTS, BATTERY_TOTAL_SERIES):
                energy_value = sum(energy_segments.values()) if segment == BATTERY_TOTAL_SERIES else energy_segments[segment]
                power_value = sum(power_segments.values()) if segment == BATTERY_TOTAL_SERIES else power_segments[segment]
                normalized.append(self._row(month_start, point_date, energy.endpoint, segment, "battery_energy_gwh", energy_value / 1_000_000, "GWh", quality))
                normalized.append(self._row(month_start, point_date, power.endpoint, segment, "battery_power_gw", power_value / 1_000_000, "GW", quality))
                if power_value > 0:
                    duration_quality = "derived_provisional" if quality != "observed" else "derived"
                    normalized.append(self._row(month_start, point_date, BATTERY_CHARTS_COMBINED_ENDPOINT, segment, "battery_duration_hours", energy_value / power_value, "h", duration_quality))

        self.connection.execute("SAVEPOINT battery_charts_import")
        try:
            replaced = self.connection.execute(
                "SELECT COUNT(*) FROM period_observation WHERE source=?",
                (BATTERY_CHARTS_SOURCE_NAME,),
            ).fetchone()[0]
            self.connection.execute("DELETE FROM period_observation WHERE source=?", (BATTERY_CHARTS_SOURCE_NAME,))
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                normalized,
            )
            self.connection.execute("DELETE FROM source_cache WHERE source=?", (BATTERY_CHARTS_SOURCE_NAME,))
            _cache_write(self.connection, energy)
            _cache_write(self.connection, power)
            self.connection.execute("RELEASE SAVEPOINT battery_charts_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT battery_charts_import")
            self.connection.execute("RELEASE SAVEPOINT battery_charts_import")
            raise
        latest = max(energy_rows)
        return {
            "source": BATTERY_CHARTS_SOURCE_NAME,
            "rows": len(normalized),
            "months": len(energy_rows),
            "latest_date": latest,
            "replaced_rows": replaced,
            "segments": list(BATTERY_SEGMENTS),
            "not_modified": energy.status_code == 304 and power.status_code == 304,
        }

    def _series(self, download: SourceDownload, label: str) -> dict[str, dict[str, float]]:
        try:
            payload = json.loads(download.payload_text)
        except json.JSONDecodeError as exc:
            raise StorageOnlineError(f"Battery-Charts {label} returned invalid JSON") from exc
        if not isinstance(payload, list) or not payload:
            raise StorageOnlineError(f"Battery-Charts {label} JSON must be a non-empty array")
        parsed: dict[str, dict[str, float]] = {}
        previous: date | None = None
        for index, item in enumerate(payload):
            if not isinstance(item, dict) or not {"date", *BATTERY_SEGMENTS}.issubset(item):
                raise StorageOnlineError(f"Battery-Charts {label} row {index} has an unexpected schema")
            try:
                point = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S").date()
            except (TypeError, ValueError) as exc:
                raise StorageOnlineError(f"Battery-Charts {label} row {index} has an invalid date") from exc
            if previous is not None and point <= previous:
                raise StorageOnlineError(f"Battery-Charts {label} dates are not strictly increasing")
            previous = point
            month_end = point.replace(day=calendar.monthrange(point.year, point.month)[1])
            if index + 1 < len(payload) and point != month_end:
                raise StorageOnlineError(f"Battery-Charts {label} contains an incomplete non-final month")
            values: dict[str, float] = {}
            for segment in BATTERY_SEGMENTS:
                try:
                    value = float(item[segment])
                except (TypeError, ValueError) as exc:
                    raise StorageOnlineError(f"Battery-Charts {label} row {index} has non-numeric {segment}") from exc
                if not math.isfinite(value) or value < 0:
                    raise StorageOnlineError(f"Battery-Charts {label} row {index} has invalid {segment}")
                values[segment] = value
            if point.year >= ATLAS_MIN_YEAR:
                key = point.isoformat()
                if key in parsed:
                    raise StorageOnlineError(f"Battery-Charts {label} contains duplicate date {key}")
                parsed[key] = values
        return parsed

    @staticmethod
    def _local_download(path: Path, endpoint: str) -> SourceDownload:
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise StorageOnlineError(f"Battery-Charts file could not be read: {path.name}") from exc
        try:
            payload_text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise StorageOnlineError(f"Battery-Charts file is not valid UTF-8: {path.name}") from exc
        return SourceDownload(
            source=BATTERY_CHARTS_SOURCE_NAME,
            endpoint=endpoint,
            request_url=f"manual-file:{path.name}",
            fetched_at=datetime.now(UTC).isoformat(),
            status_code=200,
            content_type="application/json",
            etag=None,
            last_modified=None,
            sha256=hashlib.sha256(payload).hexdigest(),
            payload_text=payload_text,
        )

    @staticmethod
    def _row(
        month_start: date,
        point_date: date,
        endpoint: str,
        series: str,
        metric: str,
        value: float,
        unit: str,
        quality: str,
    ) -> tuple[Any, ...]:
        return (
            "DE", month_start.isoformat(), point_date.isoformat(), "monthly",
            BATTERY_CHARTS_SOURCE_NAME, endpoint, series, metric, value, unit, quality,
        )


class JrcOnlineImporter:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def import_download(self, download: SourceDownload) -> dict[str, Any]:
        if download.status_code not in {200, 304} or not download.payload_text:
            raise StorageOnlineError("JRC response is missing a usable JSON payload")
        projects = self._projects(download.payload_text)
        aggregates: dict[tuple[str, str], dict[str, Any]] = {}
        for index, project in enumerate(projects):
            if not isinstance(project, dict):
                raise StorageOnlineError(f"JRC project {index} is not an object")
            status = self._nested_text(project, "status", "name")
            if status.casefold() != "operational":
                continue
            parent = self._nested_text(project, "technology", "parentName")
            technology = self._nested_text(project, "technology", "name")
            if parent.casefold() == "electrochemical":
                kind = "battery"
            elif technology.casefold() == "pumped hydro storage (phs)".casefold():
                kind = "pumped_storage"
            else:
                continue
            country = self._country_code(project, index)
            if country is None:
                continue
            if kind == "battery" and country == "DE":
                continue
            power = self._measurement(project, ("power", "power_mw", "powerMW"), "power", "MW")
            energy = self._measurement(project, ("capacity", "capacity_mwh", "capacityMWh", "energy"), "capacity", "MWh")
            estimated = self._boolean(project.get("estimated_capacity", False), index)
            if power is None and energy is None:
                continue
            aggregate = aggregates.setdefault(
                (country, kind),
                {"power": 0.0, "has_power": False, "energy": 0.0, "energy_complete": True, "estimated": False},
            )
            if power is not None:
                aggregate["power"] += power
                aggregate["has_power"] = True
            if energy is None:
                aggregate["energy_complete"] = False
            else:
                aggregate["energy"] += energy
                aggregate["estimated"] = aggregate["estimated"] or estimated

        snapshot = datetime.fromisoformat(download.fetched_at).date().isoformat()
        normalized: list[tuple[Any, ...]] = []
        for (country, kind), values in sorted(aggregates.items()):
            prefix = "battery" if kind == "battery" else "pumped_storage"
            if values["has_power"] and values["power"] > 0:
                normalized.append(self._row(country, snapshot, kind, f"{prefix}_power_gw", values["power"] / 1000, "GW", "observed"))
            if values["energy_complete"] and values["energy"] > 0:
                quality = "observed_with_estimates" if values["estimated"] else "observed"
                normalized.append(self._row(country, snapshot, kind, f"{prefix}_energy_gwh", values["energy"] / 1000, "GWh", quality))
                if values["has_power"] and values["power"] > 0:
                    duration_quality = "derived_with_estimates" if values["estimated"] else "derived"
                    normalized.append(self._row(country, snapshot, kind, f"{prefix}_duration_hours", values["energy"] / values["power"], "h", duration_quality))
        if not normalized:
            raise StorageOnlineError("JRC response contains no operational Atlas battery or pumped-storage values")

        self.connection.execute("SAVEPOINT jrc_online_import")
        try:
            replaced = self.connection.execute(
                "SELECT COUNT(*) FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_STORAGE_API_ENDPOINT),
            ).fetchone()[0]
            self.connection.execute(
                "DELETE FROM period_observation WHERE source=? AND source_endpoint=?",
                (JRC_SOURCE_NAME, JRC_STORAGE_API_ENDPOINT),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                normalized,
            )
            self.connection.execute(
                "DELETE FROM source_cache WHERE source=? AND endpoint=?",
                (JRC_SOURCE_NAME, JRC_STORAGE_API_ENDPOINT),
            )
            _cache_write(self.connection, download)
            self.connection.execute("RELEASE SAVEPOINT jrc_online_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT jrc_online_import")
            self.connection.execute("RELEASE SAVEPOINT jrc_online_import")
            raise
        return {
            "source": JRC_SOURCE_NAME,
            "rows": len(normalized),
            "projects": len(projects),
            "snapshot_date": snapshot,
            "replaced_rows": replaced,
            "countries_with_values": len({row[0] for row in normalized}),
            "not_modified": download.status_code == 304,
        }

    @staticmethod
    def _projects(payload_text: str) -> list[Any]:
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise StorageOnlineError("JRC returned invalid JSON") from exc
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("projects"), list):
            return payload["projects"]
        raise StorageOnlineError("JRC project response schema changed")

    @staticmethod
    def _nested_text(project: dict[str, Any], outer: str, inner: str) -> str:
        value = project.get(outer)
        return str(value.get(inner, "")).strip() if isinstance(value, dict) else ""

    @staticmethod
    def _country_code(project: dict[str, Any], index: int) -> str | None:
        country = project.get("country")
        candidates: Iterable[Any]
        if isinstance(country, dict):
            candidates = (country.get("code"), country.get("iso2"), country.get("name"))
        else:
            candidates = (country, project.get("country_code"), project.get("countryCode"))
        for candidate in candidates:
            text = str(candidate or "").strip()
            code = text.upper()
            if code in ATLAS_COUNTRIES:
                return code
            if len(code) == 2 and code.isalpha():
                return None
            if text in JRC_EXPORT_COUNTRIES:
                return JRC_EXPORT_COUNTRIES[text]
            if text in KNOWN_NON_ATLAS_EXPORT_COUNTRIES:
                return None
        raise StorageOnlineError(f"JRC project {index} has an unknown country")

    @staticmethod
    def _measurement(project: dict[str, Any], keys: tuple[str, ...], label: str, default_unit: str) -> float | None:
        raw: Any = None
        for key in keys:
            if key in project:
                raw = project[key]
                break
        if raw is None or raw == "":
            return None
        unit = default_unit
        if isinstance(raw, dict):
            unit = str(raw.get("unit") or default_unit)
            raw = raw.get("value")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise StorageOnlineError(f"JRC project has non-numeric {label}") from exc
        if not math.isfinite(value) or value < 0:
            raise StorageOnlineError(f"JRC project has invalid {label}")
        if value == 0:
            return None
        factors = {"kw": 0.001, "mw": 1.0, "gw": 1000.0, "kwh": 0.001, "mwh": 1.0, "gwh": 1000.0}
        factor = factors.get(unit.casefold())
        if factor is None:
            raise StorageOnlineError(f"JRC project has unsupported {label} unit")
        return value * factor

    @staticmethod
    def _boolean(value: Any, index: int) -> bool:
        if isinstance(value, bool):
            return value
        if value in (None, "", 0, "0", "false", "False"):
            return False
        if value in (1, "1", "true", "True"):
            return True
        raise StorageOnlineError(f"JRC project {index} has invalid estimated_capacity")

    @staticmethod
    def _row(country: str, snapshot: str, kind: str, metric: str, value: float, unit: str, quality: str) -> tuple[Any, ...]:
        return (
            country, snapshot, snapshot, "snapshot", JRC_SOURCE_NAME, JRC_STORAGE_API_ENDPOINT,
            f"{JRC_INVENTORY_SERIES}:{kind}", metric, value, unit, quality,
        )


class OnlineStorageUpdater:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        refresh: bool = False,
        today: date | None = None,
        jrc_client: JrcStorageClient | None = None,
    ):
        self.connection = connection
        self.refresh = refresh
        self.today = today or date.today()
        self.jrc_client = jrc_client or JrcStorageClient()

    def update(self) -> dict[str, Any]:
        return {"jrc": self._update_jrc()}

    def _update_jrc(self) -> dict[str, Any]:
        cached = self._cache_rows(JRC_SOURCE_NAME, (JRC_STORAGE_API_ENDPOINT,))
        if not self.refresh and self._fresh(cached, (JRC_STORAGE_API_ENDPOINT,)):
            return {"source": JRC_SOURCE_NAME, "cached": True, "network_requests": 0}
        row = cached.get(JRC_STORAGE_API_ENDPOINT)
        download = self.jrc_client.fetch(
            etag=row["etag"] if row and self.refresh else None,
            last_modified=row["last_modified"] if row and self.refresh else None,
        )
        if download.status_code == 304:
            download = self._with_cached_payload(download, row)
        result = JrcOnlineImporter(self.connection).import_download(download)
        result["network_requests"] = 1
        return result

    def _cache_rows(self, source: str, endpoints: tuple[str, ...]) -> dict[str, sqlite3.Row]:
        placeholders = ",".join("?" for _ in endpoints)
        rows = self.connection.execute(
            f"SELECT * FROM source_cache WHERE source=? AND endpoint IN ({placeholders})",
            (source, *endpoints),
        )
        return {row["endpoint"]: row for row in rows}

    def _fresh(self, rows: dict[str, sqlite3.Row], endpoints: tuple[str, ...]) -> bool:
        if set(rows) != set(endpoints):
            return False
        for row in rows.values():
            try:
                fetched = datetime.fromisoformat(row["fetched_at"]).date()
            except (TypeError, ValueError):
                return False
            if (fetched.year, fetched.month) != (self.today.year, self.today.month):
                return False
        return True

    @staticmethod
    def _with_cached_payload(download: SourceDownload, cached: sqlite3.Row | None) -> SourceDownload:
        if download.status_code != 304:
            return download
        if cached is None or not cached["payload_text"]:
            raise StorageOnlineError(f"{download.source} {download.endpoint} returned 304 without a cached payload")
        return SourceDownload(
            source=download.source,
            endpoint=download.endpoint,
            request_url=download.request_url,
            fetched_at=download.fetched_at,
            status_code=304,
            content_type=download.content_type or cached["content_type"],
            etag=download.etag or cached["etag"],
            last_modified=download.last_modified or cached["last_modified"],
            sha256=cached["sha256"],
            payload_text=cached["payload_text"],
        )


def latest_storage(connection: sqlite3.Connection) -> dict[str, Any]:
    countries: dict[str, dict[str, Any]] = {
        code: {
            "country_code": code,
            "country_name": country.name,
            **{metric: None for metric in STORAGE_METRICS},
            "metric_provenance": {},
            "quality_status": "missing",
        }
        for code, country in ATLAS_COUNTRIES.items()
    }
    rows = connection.execute(
        """SELECT country_code,period_start,period_end,source,source_endpoint,source_series,
                  metric,value,unit,quality_status
           FROM period_observation
           WHERE metric IN (?,?,?,?,?,?)
           ORDER BY period_end,period_start""",
        STORAGE_METRICS,
    )
    for row in rows:
        code = row["country_code"]
        if code not in countries:
            continue
        if row["metric"].startswith("battery_"):
            if code == "DE":
                if row["source"] != BATTERY_CHARTS_SOURCE_NAME or row["source_series"] != BATTERY_TOTAL_SERIES:
                    continue
                coverage_type = "national_registry_total"
                source_label = BATTERY_CHARTS_SOURCE_LABEL
            else:
                if row["source"] != JRC_SOURCE_NAME or not row["source_series"].endswith(":battery"):
                    continue
                coverage_type = "tracked_project_inventory"
                source_label = JRC_STORAGE_SOURCE_LABEL
        else:
            if row["source"] != JRC_SOURCE_NAME or not row["source_series"].endswith(":pumped_storage"):
                continue
            coverage_type = "tracked_project_inventory"
            source_label = JRC_STORAGE_SOURCE_LABEL
        metric = row["metric"]
        previous = countries[code]["metric_provenance"].get(metric)
        if previous and previous["date"] > row["period_end"]:
            continue
        countries[code][metric] = row["value"]
        countries[code]["metric_provenance"][metric] = {
            "source": row["source"],
            "source_label": source_label,
            "source_endpoint": row["source_endpoint"],
            "date": row["period_end"],
            "coverage_type": coverage_type,
            "quality_status": row["quality_status"],
            "unit": row["unit"],
        }
    for country in countries.values():
        qualities = [item["quality_status"] for item in country["metric_provenance"].values()]
        if qualities:
            country["quality_status"] = "observed_with_estimates" if any("estimate" in value for value in qualities) else "observed"
    country_rows = list(countries.values())
    dates = sorted({item["date"] for country in country_rows for item in country["metric_provenance"].values()})
    with_values = sum(any(country[metric] is not None for metric in STORAGE_METRICS) for country in country_rows)
    return {
        "snapshot_date": dates[-1] if dates else None,
        "snapshot_dates": dates,
        "source": "resolved_storage_sources",
        "source_label": f"{BATTERY_CHARTS_SOURCE_LABEL}; {JRC_STORAGE_SOURCE_LABEL}",
        "countries_with_values": with_values,
        "countries_missing": [country["country_code"] for country in country_rows if not country["metric_provenance"]],
        "countries": country_rows if dates else [],
    }
