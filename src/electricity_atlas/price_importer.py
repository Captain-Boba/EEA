from __future__ import annotations

import calendar
import csv
import hashlib
import io
import math
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import (
    EMBER_COUNTRIES,
    EMBER_ISO3_TO_ATLAS,
    EMBER_PRICE_CSV_URL,
    EMBER_PRICE_ENDPOINT,
    EMBER_SOURCE_NAME,
    EXCLUDED_VENDOR_ISO3,
)


EXPECTED_COLUMNS = ("Country", "ISO3 Code", "Date", "Price (EUR/MWhe)")


class PriceImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class PriceDownload:
    request_url: str
    fetched_at: str
    status_code: int
    content_type: str | None
    etag: str | None
    last_modified: str | None
    sha256: str
    payload_text: str


@dataclass(frozen=True)
class PriceRow:
    country_code: str
    period_start: str
    period_end: str
    value: float
    quality_status: str


class WholesalePriceClient:
    def __init__(self, url: str = EMBER_PRICE_CSV_URL, timeout: int = 90):
        self.url = url
        self.timeout = timeout

    def fetch(self) -> PriceDownload:
        request = Request(self.url, headers={"User-Agent": "European-Electricity-Atlas/0.1"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload_bytes = response.read()
                status = response.status
                content_type = response.headers.get("Content-Type")
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
        except HTTPError as exc:
            raise PriceImportError(f"Ember price CSV returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise PriceImportError(f"Ember price CSV could not be reached: {exc.reason}") from exc
        try:
            payload_text = payload_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PriceImportError("Ember price CSV is not valid UTF-8") from exc
        return PriceDownload(
            request_url=self.url,
            fetched_at=datetime.now(UTC).isoformat(),
            status_code=status,
            content_type=content_type,
            etag=etag,
            last_modified=last_modified,
            sha256=hashlib.sha256(payload_bytes).hexdigest(),
            payload_text=payload_text,
        )


class WholesalePriceImporter:
    def __init__(
        self,
        connection: sqlite3.Connection,
        client: WholesalePriceClient | None = None,
        today: date | None = None,
    ):
        self.connection = connection
        self.client = client or WholesalePriceClient()
        self.today = today or date.today()

    def import_prices(self) -> dict[str, Any]:
        download = self.client.fetch()
        if download.status_code != 200:
            raise PriceImportError(f"Ember price CSV returned HTTP {download.status_code}")
        if not download.content_type or "text/csv" not in download.content_type.lower():
            raise PriceImportError("Ember price CSV returned an unexpected content type")
        rows = self._validate(download.payload_text)

        self.connection.execute("SAVEPOINT ember_price_import")
        try:
            replaced_rows = self.connection.execute(
                """SELECT COUNT(*) FROM period_observation
                   WHERE source=? AND source_endpoint=? AND metric='day_ahead_price'""",
                (EMBER_SOURCE_NAME, EMBER_PRICE_ENDPOINT),
            ).fetchone()[0]
            self.connection.execute(
                """DELETE FROM period_observation
                   WHERE source=? AND source_endpoint=? AND metric='day_ahead_price'""",
                (EMBER_SOURCE_NAME, EMBER_PRICE_ENDPOINT),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,'monthly',?,?,?,'day_ahead_price',?,'EUR/MWh',?)""",
                [
                    (
                        row.country_code,
                        row.period_start,
                        row.period_end,
                        EMBER_SOURCE_NAME,
                        EMBER_PRICE_ENDPOINT,
                        "national_wholesale_price",
                        row.value,
                        row.quality_status,
                    )
                    for row in rows
                ],
            )
            self.connection.execute(
                """INSERT INTO source_cache
                   (source,endpoint,request_url,fetched_at,status_code,content_type,etag,
                    last_modified,sha256,payload_text)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(source,endpoint) DO UPDATE SET
                     request_url=excluded.request_url,
                     fetched_at=excluded.fetched_at,
                     status_code=excluded.status_code,
                     content_type=excluded.content_type,
                     etag=excluded.etag,
                     last_modified=excluded.last_modified,
                     sha256=excluded.sha256,
                     payload_text=excluded.payload_text""",
                (
                    EMBER_SOURCE_NAME,
                    EMBER_PRICE_ENDPOINT,
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
            self.connection.execute("RELEASE SAVEPOINT ember_price_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT ember_price_import")
            self.connection.execute("RELEASE SAVEPOINT ember_price_import")
            raise

        return {
            "source": EMBER_SOURCE_NAME,
            "endpoint": EMBER_PRICE_ENDPOINT,
            "rows": len(rows),
            "countries": len(EMBER_COUNTRIES),
            "countries_with_values": len({row.country_code for row in rows}),
            "replaced_rows": replaced_rows,
            "sha256": download.sha256,
            "fetched_at": download.fetched_at,
        }

    def _validate(self, payload_text: str) -> list[PriceRow]:
        if not payload_text.strip():
            raise PriceImportError("Ember price CSV is empty")
        reader = csv.DictReader(io.StringIO(payload_text, newline=""))
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise PriceImportError(
                f"Ember price CSV header changed; expected {', '.join(EXPECTED_COLUMNS)}"
            )

        rows: list[PriceRow] = []
        seen: set[tuple[str, str]] = set()
        seen_iso3: set[str] = set()
        country_names: dict[str, str] = {}
        current_month = self.today.replace(day=1)
        for line_number, record in enumerate(reader, start=2):
            if None in record or any(record[column] is None for column in EXPECTED_COLUMNS):
                raise PriceImportError(f"Ember price CSV row {line_number} has the wrong field count")
            country_name = record["Country"].strip()
            iso3 = record["ISO3 Code"].strip()
            if not country_name:
                raise PriceImportError(f"Ember price CSV row {line_number} has no country name")
            if iso3 in EXCLUDED_VENDOR_ISO3:
                continue
            if iso3 not in EMBER_ISO3_TO_ATLAS:
                raise PriceImportError(f"Ember price CSV row {line_number} has unknown ISO3 code {iso3!r}")
            if iso3 in country_names and country_names[iso3] != country_name:
                raise PriceImportError(f"Ember price CSV uses inconsistent names for {iso3}")
            country_names[iso3] = country_name
            try:
                period_start = date.fromisoformat(record["Date"].strip())
            except ValueError as exc:
                raise PriceImportError(f"Ember price CSV row {line_number} has an invalid date") from exc
            if period_start.day != 1:
                raise PriceImportError(f"Ember price CSV row {line_number} is not a month start")
            code = EMBER_ISO3_TO_ATLAS[iso3]
            key = (code, period_start.isoformat())
            if key in seen:
                raise PriceImportError(f"Ember price CSV contains duplicate month {key[1]} for {code}")
            seen.add(key)
            seen_iso3.add(iso3)
            price_text = record["Price (EUR/MWhe)"].strip()
            if not price_text:
                # Ember uses an empty price cell for a known country-month with
                # no published value. It is coverage, not a numeric zero.
                continue
            try:
                value = float(price_text)
            except ValueError as exc:
                raise PriceImportError(f"Ember price CSV row {line_number} has a non-numeric price") from exc
            if not math.isfinite(value):
                raise PriceImportError(f"Ember price CSV row {line_number} has a non-finite price")

            period_end = period_start.replace(day=calendar.monthrange(period_start.year, period_start.month)[1])
            rows.append(
                PriceRow(
                    country_code=code,
                    period_start=period_start.isoformat(),
                    period_end=period_end.isoformat(),
                    value=value,
                    quality_status=(
                        "provisional_current_month" if period_start == current_month else "observed"
                    ),
                )
            )

        if not rows:
            raise PriceImportError("Ember price CSV contains no data rows")
        expected_iso3 = set(EMBER_ISO3_TO_ATLAS)
        if seen_iso3 != expected_iso3:
            missing = ", ".join(sorted(expected_iso3 - seen_iso3)) or "none"
            raise PriceImportError(
                f"Ember price CSV does not contain the full {len(expected_iso3)}-country catalog; missing: {missing}"
            )
        return rows
