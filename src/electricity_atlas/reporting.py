"""Offline, snapshot-consistent reports. No importer or network request is run."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .aggregation import aggregate_all
from .config import ATLAS_MIN_YEAR, COUNTRIES, EMBER_ISO3
from .coverage import coverage_markdown
from .db import read_database
from .ember_client import EmberClient
from .ember_importer import EmberImporter, EMBER_AGGREGATE_SERIES_TO_METRIC
from .ember_retention import RETAINED_SOURCE_GAP

SAMPLE_COUNTRIES = ("DE", "FR", "UK", "ES", "NO")
REPORT_FILES = ("COVERAGE.generated.md", "SUMMARY.generated.json",
                "VALIDATION.generated.md", "VALIDATION.generated.json")
MANIFEST_NAME = "REPORT_MANIFEST.generated.json"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot_digest(connection: sqlite3.Connection) -> str:
    """Logical content, including committed WAL rows; NOT a main-file SHA-256."""
    digest = hashlib.sha256()
    for table, columns in (("period_observation", 11), ("api_cache", 10), ("source_cache", 10)):
        digest.update(table.encode("ascii"))
        order = ",".join(str(index) for index in range(1, columns + 1))
        for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}"):
            digest.update(_json(list(row)).encode("utf-8"))
    return digest.hexdigest()


def _row_key(row: Any) -> tuple:
    return tuple(row[key] for key in ("period_start", "period_end", "granularity",
                                     "source_endpoint", "source_series", "metric", "unit"))


def _cache_checks(connection: sqlite3.Connection, code: str, year: int) -> dict[str, Any]:
    """Replay normalization only; this is NOT independent validation of Ember."""
    actual = list(connection.execute(
        "SELECT * FROM period_observation WHERE source='ember' AND country_code=? "
        "AND substr(period_start,1,4)=? AND source_endpoint IN "
        "('electricity-generation/monthly','electricity-generation/yearly',"
        "'electricity-demand/monthly','electricity-demand/yearly',"
        "'carbon-intensity/monthly','carbon-intensity/yearly') ORDER BY period_start,source_endpoint,metric,source_series",
        (code, str(year)),
    ))
    caches = list(connection.execute(
        "SELECT * FROM api_cache WHERE (target=? OR target LIKE ?) "
        "AND endpoint LIKE 'ember/%' AND status_code=200 ORDER BY fetched_at DESC,id DESC",
        (EMBER_ISO3[code], EMBER_ISO3[code] + "|%"),
    ))
    # A sentinel client prevents constructing the authenticated/network client.
    normalizer = EmberImporter(connection, client=object())
    parsed: dict[int, tuple[dict, dict[tuple, float]] | None] = {}
    counts: Counter = Counter()
    issues: list[dict[str, Any]] = []
    used_cache: dict[int, dict] = {}

    def parse(cache):
        if cache["id"] not in parsed:
            try:
                if _digest(cache["response_json"]) != cache["sha256"].lower():
                    raise ValueError("cache checksum mismatch")
                payload = json.loads(cache["response_json"])
                if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                    raise ValueError("cache data is not a list")
                if any(not isinstance(row, dict) for row in payload["data"]):
                    raise ValueError("cache record is not an object")
                records = [row for row in payload["data"] if str(row.get("date", ""))[:4] == str(year)]
                endpoint = cache["endpoint"].removeprefix("ember/")
                granularity = endpoint.rsplit("/", 1)[-1]
                start, end = ((f"{year}-01", f"{year}-12") if granularity == "monthly" else (str(year), str(year)))
                normalized = normalizer._normalize_payload(code, endpoint, granularity, start, end, {"data": records})
                values = {}
                for row in normalized:
                    if not math.isfinite(row.value):
                        raise ValueError("nonfinite cache value")
                    key = _row_key(vars(row))
                    if key in values and values[key] != row.value:
                        raise ValueError("conflicting cache records")
                    values[key] = row.value
                parsed[cache["id"]] = (payload, values)
            except (ValueError, TypeError, KeyError, OverflowError):
                parsed[cache["id"]] = None
        return parsed[cache["id"]]

    for row in actual:
        endpoint = row["source_endpoint"]
        token = row["period_start"][:7 if row["granularity"] == "monthly" else 4]
        aggregate = row["source_series"].casefold() in EMBER_AGGREGATE_SERIES_TO_METRIC
        target = EMBER_ISO3[code]
        if endpoint.startswith("electricity-generation/"):
            target += "|is_aggregate_series=" + ("true" if aggregate else "false")
        selected = None
        for cache in caches:
            if cache["endpoint"] != "ember/" + endpoint:
                continue
            # Monthly API upper bounds are exclusive; yearly bounds are inclusive.
            covered = (cache["start_date"] <= token < cache["end_date"] if row["granularity"] == "monthly"
                       else cache["start_date"] <= token <= cache["end_date"])
            if not covered:
                continue
            if cache["target"] != target:
                if aggregate or not endpoint.startswith("electricity-generation/") or cache["target"] != EMBER_ISO3[code]:
                    continue
                content = parse(cache)
                if content is not None and not EmberClient._is_non_aggregate_generation(content[0]):
                    continue
            selected = cache
            break  # Never mask an absent/revised record with an older response.
        if row["quality_status"] == RETAINED_SOURCE_GAP:
            status = "retained_source_gap"
        elif selected is None:
            status = "unverifiable_no_cache"
        else:
            content = parse(selected)
            used_cache[selected["id"]] = {
                "endpoint": endpoint, "target": selected["target"],
                "fetched_at": selected["fetched_at"], "sha256": selected["sha256"],
            }
            if content is None:
                status = "invalid_cache"
            elif _row_key(row) not in content[1]:
                status = "missing_in_latest_cache"
            elif math.isclose(row["value"], content[1][_row_key(row)], rel_tol=1e-9, abs_tol=1e-9):
                status = "matched"
            else:
                status = "value_mismatch"
        counts[status] += 1
        if status != "matched":
            issues.append({"status": status, "period_start": row["period_start"],
                           "endpoint": endpoint, "metric": row["metric"], "series": row["source_series"]})
    errors = sum(counts[key] for key in ("invalid_cache", "missing_in_latest_cache", "value_mismatch"))
    return {"country": code, "observations": len(actual), "counts": dict(sorted(counts.items())),
            "errors": errors, "issues": issues, "cache_evidence": list(used_cache.values())}


def build_reports(connection: sqlite3.Connection, year: int, *, as_of: date) -> dict[str, str]:
    if not ATLAS_MIN_YEAR <= year <= as_of.year:
        raise ValueError(f"Report year must be between {ATLAS_MIN_YEAR} and the as-of year")
    integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if integrity != ["ok"]:
        raise ValueError("Atlas integrity check failed; no reports written")
    snapshot = _snapshot_digest(connection)
    summary = aggregate_all(connection, year, today=as_of)
    checks = [_cache_checks(connection, code, year) for code in SAMPLE_COUNTRIES]
    countries = {row[0] for row in connection.execute("SELECT DISTINCT country_code FROM period_observation")}
    inventory = [dict(row) for row in connection.execute(
        "SELECT source,quality_status,COUNT(*) AS observations,MIN(period_start) AS first_period,"
        "MAX(period_end) AS last_period FROM period_observation GROUP BY source,quality_status ORDER BY source,quality_status")]
    errors = sum(check["errors"] for check in checks) + len(countries - set(COUNTRIES))
    warnings = sum(check["counts"].get("unverifiable_no_cache", 0) + check["counts"].get("retained_source_gap", 0)
                   + (1 if not check["observations"] else 0) for check in checks)
    missing = [row["country_code"] for row in summary if any(row.get(metric) is None for metric in (
        "generation_twh", "consumption_twh", "renewable_share_pct", "carbon_intensity_gco2eq_kwh"))]
    warnings += len(missing) + len(set(COUNTRIES) - countries)
    validation = {
        "schema_version": 1, "year": year, "as_of": as_of.isoformat(), "snapshot_sha256": snapshot,
        "fingerprint_kind": "logical_sqlite_content_v1",
        "status": "failed" if errors else "warnings" if warnings else "passed",
        "errors": errors, "warnings": warnings, "integrity": "ok",
        "scope": "Offline stored Ember observation/cache consistency for DE, FR, UK, ES, NO; shared importer normalization. Not an independent source audit or live freshness check. Cache-only records not imported are not audited.",
        "missing_core_summary_countries": missing,
        "missing_catalog_countries": sorted(set(COUNTRIES) - countries),
        "unexpected_catalog_countries": sorted(countries - set(COUNTRIES)),
        "summary_status_counts": dict(sorted(Counter(row["data_status"] for row in summary).items())),
        "summary_period_status_counts": dict(sorted(Counter(row["period_status"] for row in summary).items())),
        "summary_quality_issue_counts": dict(sorted(Counter(
            issue["issue_type"] for row in summary for issue in row["quality_issues"]
        ).items())),
        "source_inventory": inventory, "ember_cache_checks": checks,
    }
    lines = [f"# Atlas validation {year}", "", f"Status: **{validation['status']}**; errors: {errors}; warnings: {warnings}.",
             f"As-of date: {as_of.isoformat()} (aggregation calendar, not a historical database reconstruction).", "",
             f"Logical snapshot SHA-256: `{snapshot}`", "", validation["scope"], "",
             "Missing values remain null. Retained source-gap values are NOT freshly verified.",
             "Period end dates in the inventory are reporting periods, NOT fetch/freshness timestamps.", "",
             "| Country | Stored observations | Matched | Retained | No cache | Errors |",
             "|---|---:|---:|---:|---:|---:|"]
    for check in checks:
        count = check["counts"]
        lines.append(f"| {check['country']} | {check['observations']} | {count.get('matched', 0)} | "
                     f"{count.get('retained_source_gap', 0)} | {count.get('unverifiable_no_cache', 0)} | {check['errors']} |")
    lines += ["", "Countries missing one or more core summary values: " + (", ".join(missing) or "none") + ".",
              "", "See VALIDATION.generated.json for per-observation issues, cache evidence and source inventory.",
              "REPORT_MANIFEST.generated.json identifies the complete report set and each file's checksum."]
    coverage = coverage_markdown(connection, year, today=as_of)
    coverage += f"\nAs-of: {as_of.isoformat()}; logical snapshot SHA-256: `{snapshot}`.\n"
    return dict(zip(REPORT_FILES, (coverage, _json(summary), "\n".join(lines) + "\n", _json(validation))))


def write_reports(database_path: Path, output: Path, year: int, *, as_of: date | None = None) -> dict[str, Any]:
    """Prepare everything first; replace files atomically and write the receipt last."""
    database_path, output = Path(database_path).resolve(), Path(output).resolve()
    for name in (*REPORT_FILES, MANIFEST_NAME):
        target = output / name
        if target.is_symlink() or target.resolve() == database_path or (
            target.exists() and database_path.exists() and target.samefile(database_path)
        ):
            raise ValueError("Report output collides with a database or symbolic link")
    with read_database(database_path) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")  # One SQLite snapshot for every report, including WAL content.
        reports = build_reports(connection, year, as_of=as_of or date.today())
    validation = json.loads(reports["VALIDATION.generated.json"])
    manifest = {key: validation[key] for key in ("schema_version", "year", "as_of", "snapshot_sha256", "fingerprint_kind", "status")}
    manifest["files"] = {name: _digest(content) for name, content in reports.items()}
    reports[MANIFEST_NAME] = _json(manifest)
    output.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for name, content in reports.items():
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=output,
                                             prefix=".atlas-report-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                staged.append((temporary, output / name))
                handle.write(content)
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return validation
