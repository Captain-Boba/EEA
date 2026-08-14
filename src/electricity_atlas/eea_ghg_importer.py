from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import math
import re
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import (
    ATLAS_COUNTRIES,
    ATLAS_MIN_YEAR,
    EEA_GHG_ENDPOINT,
    EEA_GHG_URL,
    EEA_SOURCE_NAME,
)


class EeaGhgImportError(RuntimeError):
    pass


class EeaGhgImporter:
    """Import aggregate GHG emissions for CRT 1.A.1.a from an EEA CSV bundle."""

    def __init__(self, connection: sqlite3.Connection, timeout: int = 180):
        self.connection = connection
        self.timeout = timeout

    def import_url(self, url: str = EEA_GHG_URL) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": "European-Electricity-Atlas/0.1 (annual open-data importer)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                metadata = {
                    "request_url": response.geturl(),
                    "status_code": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
        except (HTTPError, URLError) as exc:
            raise EeaGhgImportError(f"EEA GHG download failed: {exc}") from exc
        if "text/html" in (metadata["content_type"] or "").lower():
            page = payload.decode("utf-8", "replace")
            match = re.search(r'name="downloadURL"\s+value="([^"]+)"', page)
            if not match:
                raise EeaGhgImportError("EEA GHG download page contains no direct download URL")
            download_url = match.group(1).replace("&amp;", "&")
            try:
                with urlopen(
                    Request(download_url, headers={"User-Agent": "European-Electricity-Atlas/0.1"}),
                    timeout=self.timeout,
                ) as response:
                    payload = response.read()
                    metadata.update(
                        request_url=download_url,
                        status_code=response.status,
                        content_type=response.headers.get("Content-Type"),
                        etag=response.headers.get("ETag"),
                        last_modified=response.headers.get("Last-Modified"),
                    )
            except (HTTPError, URLError) as exc:
                raise EeaGhgImportError(f"EEA GHG direct download failed: {exc}") from exc
        return self._import_payload(payload, metadata)

    def import_file(self, path: Path) -> dict[str, Any]:
        payload = Path(path).read_bytes()
        return self._import_payload(
            payload,
            {
                "request_url": Path(path).resolve().as_uri(),
                "status_code": 200,
                "content_type": "application/zip" if zipfile.is_zipfile(io.BytesIO(payload)) else "text/csv",
                "etag": None,
                "last_modified": datetime.fromtimestamp(Path(path).stat().st_mtime, UTC).isoformat(),
            },
        )

    def _import_payload(self, payload: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
        csv_payload, member = self._csv_payload(payload)
        rows = self._normalize(csv_payload)
        if not rows:
            raise EeaGhgImportError("EEA GHG data contained no Atlas values for CRT 1.A.1.a")
        archive_sha256 = hashlib.sha256(payload).hexdigest()
        sha256 = hashlib.sha256(csv_payload).hexdigest()
        self.connection.execute("SAVEPOINT eea_ghg_import")
        try:
            replaced = self.connection.execute(
                "SELECT COUNT(*) FROM period_observation WHERE source=? AND source_endpoint=?",
                (EEA_SOURCE_NAME, EEA_GHG_ENDPOINT),
            ).fetchone()[0]
            self.connection.execute(
                "DELETE FROM period_observation WHERE source=? AND source_endpoint=?",
                (EEA_SOURCE_NAME, EEA_GHG_ENDPOINT),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,'yearly',?,?,?,?,?,?,?)""",
                rows,
            )
            # Cache only the selected CSV, not a potentially very large folder
            # archive containing duplicate Access/SQLite/Excel distributions.
            cache_text = "gzip+base64:" + base64.b64encode(gzip.compress(csv_payload)).decode("ascii")
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
                    EEA_SOURCE_NAME,
                    EEA_GHG_ENDPOINT,
                    metadata["request_url"],
                    datetime.now(UTC).isoformat(),
                    metadata["status_code"],
                    "text/csv" if member else metadata["content_type"],
                    metadata["etag"],
                    metadata["last_modified"],
                    sha256,
                    cache_text,
                ),
            )
            self.connection.execute("RELEASE SAVEPOINT eea_ghg_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT eea_ghg_import")
            self.connection.execute("RELEASE SAVEPOINT eea_ghg_import")
            raise
        return {
            "source": EEA_SOURCE_NAME,
            "rows": len(rows),
            "countries_with_values": len({row[0] for row in rows}),
            "countries_missing": sorted(set(ATLAS_COUNTRIES) - {row[0] for row in rows}),
            "period": f"{min(int(row[1][:4]) for row in rows)}..{max(int(row[1][:4]) for row in rows)}",
            "archive_member": member,
            "sha256": sha256,
            "archive_sha256": archive_sha256 if member else None,
            "replaced_rows": replaced,
        }

    @staticmethod
    def _csv_payload(payload: bytes) -> tuple[bytes, str | None]:
        if not zipfile.is_zipfile(io.BytesIO(payload)):
            return payload, None
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            candidates = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            preferred = [name for name in candidates if "unfccc" in name.lower() or "data_viewer" in name.lower()]
            names = preferred or candidates
            if not names:
                raise EeaGhgImportError("EEA GHG archive contains no CSV file")
            if len(names) > 1:
                names.sort(key=lambda name: ("user" not in name.lower(), len(name)))
            name = names[0]
            return archive.read(name), name

    @staticmethod
    def _normalize_header(value: str) -> str:
        return "".join(character for character in value.lower() if character.isalnum())

    def _normalize(self, payload: bytes) -> list[tuple[Any, ...]]:
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = payload.decode("latin-1")
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        if not reader.fieldnames:
            raise EeaGhgImportError("EEA GHG CSV has no header")
        headers = {self._normalize_header(name): name for name in reader.fieldnames}

        def header(*aliases: str) -> str:
            for alias in aliases:
                if self._normalize_header(alias) in headers:
                    return headers[self._normalize_header(alias)]
            raise EeaGhgImportError(f"EEA GHG CSV lacks required column: {aliases[0]}")

        country_col = header("country_code", "countrycode")
        year_col = header("year", "inventory_year")
        sector_col = header("sector_code", "sectorcode", "sector")
        gas_col = header("pollutant_name", "gas", "pollutant")
        unit_col = header("unit")
        value_col = header("emissions", "value")
        normalized: dict[tuple[str, int], float] = {}
        for row in reader:
            code = (row.get(country_col) or "").strip().upper()
            code = {"GB": "UK", "EL": "GR"}.get(code, code)
            if code not in ATLAS_COUNTRIES:
                continue
            sector = self._normalize_header(row.get(sector_col) or "")
            if sector != "1a1a":
                continue
            gas = self._normalize_header(row.get(gas_col) or "")
            if not ("aggregate" in gas or "greenhouse" in gas or gas in {"ghg", "allghgs"}):
                continue
            unit = self._normalize_header(row.get(unit_col) or "")
            if "co2" not in unit or not ("equiv" in unit or "eq" in unit):
                continue
            try:
                year = int((row.get(year_col) or "").strip())
                value_mt = float((row.get(value_col) or "").strip()) * 0.001
            except ValueError:
                continue
            if year < ATLAS_MIN_YEAR or not math.isfinite(value_mt):
                continue
            key = (code, year)
            if key in normalized and not math.isclose(normalized[key], value_mt, rel_tol=1e-12, abs_tol=1e-12):
                raise EeaGhgImportError(f"EEA GHG CSV contains conflicting duplicate values for {code} {year}")
            normalized[key] = value_mt
        return [
            (
                code,
                f"{year:04d}-01-01",
                f"{year:04d}-12-31",
                EEA_SOURCE_NAME,
                EEA_GHG_ENDPOINT,
                "CRT 1.A.1.a:aggregate GHGs; public electricity and heat",
                "eea_public_electricity_heat_emissions_mtco2eq",
                value,
                "Mt CO2eq",
                "observed_including_public_heat",
            )
            for (code, year), value in sorted(normalized.items())
        ]
