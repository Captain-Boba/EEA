from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import (
    ATLAS_COUNTRIES,
    ATLAS_MIN_YEAR,
    EUROSTAT_API_BASE_URL,
    EUROSTAT_GEO,
    EUROSTAT_GEO_TO_ATLAS,
    EUROSTAT_SOURCE_NAME,
)


class EurostatImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class EurostatDataset:
    code: str
    metric: str
    unit: str
    filters: dict[str, str]
    scale: float = 1.0


DATASETS = (
    EurostatDataset("demo_gind", "population", "people", {"freq": "A", "indic_de": "JAN"}),
    EurostatDataset("nama_10_gdp", "gdp_current_billion_eur", "billion EUR", {"freq": "A", "na_item": "B1GQ", "unit": "CP_MEUR"}, 0.001),
    EurostatDataset("nama_10_pc", "gdp_per_capita_pps", "PPS/person", {"freq": "A", "na_item": "B1GQ", "unit": "CP_PPS_EU27_2020_HAB"}),
)


@dataclass(frozen=True)
class EurostatDownload:
    dataset: EurostatDataset
    request_url: str
    fetched_at: str
    status_code: int
    content_type: str | None
    etag: str | None
    last_modified: str | None
    sha256: str
    payload_text: str


class EurostatClient:
    def __init__(
        self,
        base_url: str = EUROSTAT_API_BASE_URL,
        timeout: int = 90,
        retries: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.sleeper = sleeper

    def fetch(self, dataset: EurostatDataset, start_year: int, end_year: int) -> EurostatDownload:
        params: list[tuple[str, str]] = [("lang", "en")]
        params.extend(dataset.filters.items())
        params.extend(("geo", geo) for geo in EUROSTAT_GEO.values())
        params.extend((("sinceTimePeriod", str(start_year)), ("untilTimePeriod", str(end_year))))
        url = f"{self.base_url}/{dataset.code}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "European-Electricity-Atlas/0.1 (conservative annual importer)"})
        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = response.read()
                    status = response.status
                    headers = response.headers
                break
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == self.retries:
                    raise EurostatImportError(f"Eurostat {dataset.code} returned HTTP {exc.code}") from exc
                self.sleeper(self._retry_delay(exc.headers.get("Retry-After"), attempt))
            except URLError as exc:
                if attempt + 1 == self.retries:
                    raise EurostatImportError(f"Eurostat {dataset.code} could not be reached: {exc.reason}") from exc
                self.sleeper(min(2**attempt, 30))
        else:  # pragma: no cover - loop always returns or raises
            raise EurostatImportError(f"Eurostat {dataset.code} download failed")
        try:
            payload_text = payload.decode("utf-8")
            json.loads(payload_text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EurostatImportError(f"Eurostat {dataset.code} returned invalid JSON") from exc
        return EurostatDownload(
            dataset=dataset,
            request_url=url,
            fetched_at=datetime.now(UTC).isoformat(),
            status_code=status,
            content_type=headers.get("Content-Type"),
            etag=headers.get("ETag"),
            last_modified=headers.get("Last-Modified"),
            sha256=hashlib.sha256(payload).hexdigest(),
            payload_text=payload_text,
        )

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return min(max(float(retry_after), 0), 60)
            except ValueError:
                try:
                    seconds = (parsedate_to_datetime(retry_after) - datetime.now(UTC)).total_seconds()
                    return min(max(seconds, 0), 60)
                except (TypeError, ValueError):
                    pass
        return min(2**attempt, 30)


class EurostatImporter:
    def __init__(self, connection: sqlite3.Connection, client: EurostatClient | None = None):
        self.connection = connection
        self.client = client or EurostatClient()

    def import_years(self, start_year: int = ATLAS_MIN_YEAR, end_year: int | None = None) -> dict[str, Any]:
        current_year = datetime.now().year
        last_year = current_year if end_year is None else end_year
        if start_year < ATLAS_MIN_YEAR or last_year < start_year or last_year > current_year:
            raise ValueError(f"Eurostat years must be between {ATLAS_MIN_YEAR} and {current_year}")
        downloads = [self.client.fetch(dataset, start_year, last_year) for dataset in DATASETS]
        normalized: list[tuple[Any, ...]] = []
        for download in downloads:
            normalized.extend(self._normalize(download, start_year, last_year))
        if not normalized:
            raise EurostatImportError("Eurostat responses contained no Atlas data")

        self.connection.execute("SAVEPOINT eurostat_import")
        try:
            replaced = self.connection.execute(
                """SELECT COUNT(*) FROM period_observation
                   WHERE source=? AND granularity='yearly' AND period_start>=? AND period_start<=?""",
                (EUROSTAT_SOURCE_NAME, f"{start_year:04d}-01-01", f"{last_year:04d}-01-01"),
            ).fetchone()[0]
            self.connection.execute(
                """DELETE FROM period_observation
                   WHERE source=? AND granularity='yearly' AND period_start>=? AND period_start<=?""",
                (EUROSTAT_SOURCE_NAME, f"{start_year:04d}-01-01", f"{last_year:04d}-01-01"),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,'yearly',?,?,?,?,?,?,?)""",
                normalized,
            )
            for download in downloads:
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
                        EUROSTAT_SOURCE_NAME,
                        download.dataset.code,
                        download.request_url,
                        download.fetched_at,
                        download.status_code,
                        download.content_type,
                        download.etag,
                        download.last_modified,
                        download.sha256,
                        download.payload_text,
                    ),
                )
            self.connection.execute("RELEASE SAVEPOINT eurostat_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT eurostat_import")
            self.connection.execute("RELEASE SAVEPOINT eurostat_import")
            raise
        return {
            "source": EUROSTAT_SOURCE_NAME,
            "rows": len(normalized),
            "countries_with_values": len({row[0] for row in normalized}),
            "datasets": [download.dataset.code for download in downloads],
            "replaced_rows": replaced,
            "period": f"{start_year}..{last_year}",
        }

    def _normalize(self, download: EurostatDownload, start_year: int, end_year: int) -> list[tuple[Any, ...]]:
        payload = json.loads(download.payload_text)
        ids = payload.get("id")
        sizes = payload.get("size")
        dimensions = payload.get("dimension")
        values = payload.get("value")
        if not isinstance(ids, list) or not isinstance(sizes, list) or not isinstance(dimensions, dict):
            raise EurostatImportError(f"Eurostat {download.dataset.code} JSON-stat structure changed")
        if "geo" not in ids or "time" not in ids or len(ids) != len(sizes):
            raise EurostatImportError(f"Eurostat {download.dataset.code} lacks geo/time dimensions")
        positions = {dimension: self._positions(dimensions, dimension) for dimension in ids}
        total = math.prod(sizes)
        if isinstance(values, list):
            sparse = {index: value for index, value in enumerate(values) if value is not None}
        elif isinstance(values, dict):
            sparse = {int(index): value for index, value in values.items()}
        else:
            raise EurostatImportError(f"Eurostat {download.dataset.code} has no value array")
        rows: list[tuple[Any, ...]] = []
        for linear_index, raw_value in sparse.items():
            if not 0 <= linear_index < total:
                raise EurostatImportError(f"Eurostat {download.dataset.code} has an invalid value index")
            coordinates: dict[str, str] = {}
            remainder = linear_index
            for dimension, size in reversed(list(zip(ids, sizes))):
                coordinate = remainder % size
                remainder //= size
                coordinates[dimension] = positions[dimension][coordinate]
            country = EUROSTAT_GEO_TO_ATLAS.get(coordinates["geo"])
            year_text = coordinates["time"]
            if country not in ATLAS_COUNTRIES or not year_text.isdigit():
                continue
            year = int(year_text)
            if not start_year <= year <= end_year:
                continue
            try:
                value = float(raw_value) * download.dataset.scale
            except (TypeError, ValueError) as exc:
                raise EurostatImportError(f"Eurostat {download.dataset.code} contains a non-numeric value") from exc
            if not math.isfinite(value):
                raise EurostatImportError(f"Eurostat {download.dataset.code} contains a non-finite value")
            rows.append(
                (
                    country,
                    f"{year:04d}-01-01",
                    f"{year:04d}-12-31",
                    EUROSTAT_SOURCE_NAME,
                    f"eurostat/{download.dataset.code}",
                    "",
                    download.dataset.metric,
                    value,
                    download.dataset.unit,
                    "observed",
                )
            )
        if not rows:
            raise EurostatImportError(f"Eurostat {download.dataset.code} contains no requested Atlas values")
        return rows

    @staticmethod
    def _positions(dimensions: dict[str, Any], dimension: str) -> list[str]:
        try:
            index = dimensions[dimension]["category"]["index"]
        except (KeyError, TypeError) as exc:
            raise EurostatImportError(f"Eurostat dimension {dimension} has no category index") from exc
        if isinstance(index, list):
            return [str(value) for value in index]
        if isinstance(index, dict):
            return [str(key) for key, _ in sorted(index.items(), key=lambda item: item[1])]
        raise EurostatImportError(f"Eurostat dimension {dimension} has an invalid category index")
