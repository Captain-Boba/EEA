from __future__ import annotations

import calendar
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Callable, Iterable

from .client import EnergyChartsClient
from .config import ATLAS_MIN_YEAR, COUNTRIES, ENERGY_CHARTS_COUNTRIES, EXPECTED_PUBLIC_POWER_SERIES, SOURCE_NAME, Country
from .normalization import iso_to_utc, normalize_public_power_record, power_to_mw, split_physical_flows


@dataclass(frozen=True)
class Period:
    start: str
    end: str


def _month_bounds(token: str) -> tuple[str, str]:
    year, month = (int(part) for part in token.split("-"))
    return f"{token}-01", f"{token}-{calendar.monthrange(year, month)[1]:02d}"


def _period_quality(token: str) -> str:
    return "provisional_current_month" if token == date.today().strftime("%Y-%m") else "observed"


def _weighted_median(pairs: list[tuple[float, int]]) -> float | None:
    usable = sorted((float(value), int(weight)) for value, weight in pairs if weight > 0)
    if not usable:
        return None
    midpoint = sum(weight for _, weight in usable) / 2
    cumulative = 0
    for index, (value, weight) in enumerate(usable):
        cumulative += weight
        if cumulative == midpoint and index + 1 < len(usable):
            return (value + usable[index + 1][0]) / 2
        if cumulative > midpoint:
            return value
    return usable[-1][0]


def monthly_periods(year: int, months: Iterable[int] | None = None) -> list[Period]:
    selected = list(months) if months is not None else list(range(1, 13))
    periods: list[Period] = []
    for month in selected:
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid month: {month}")
        last_day = calendar.monthrange(year, month)[1]
        periods.append(Period(f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"))
    return periods


class Importer:
    def __init__(self, connection: sqlite3.Connection, refresh: bool = False):
        self.connection = connection
        self.client = EnergyChartsClient(connection)
        self.refresh = refresh

    def import_country(self, country_code: str, year: int, months: Iterable[int] | None = None) -> dict[str, Any]:
        code = country_code.upper()
        if code not in ENERGY_CHARTS_COUNTRIES:
            raise ValueError(f"Energy-Charts does not support Atlas country: {country_code}")
        country = COUNTRIES[code]
        summary: dict[str, Any] = {
            "public_power": 0,
            "cbpf": 0,
            "price": 0,
            "installed_power": 0,
            "errors": 0,
            "successes": [],
            "failures": [],
            "skipped": [],
        }
        requested_periods = monthly_periods(year, months) if months is not None else None
        for endpoint in ("public_power", "cbpf"):
            try:
                periods = requested_periods or self._smart_periods(endpoint, country.code.lower(), year)
            except Exception as exc:
                self._record_failure(
                    summary,
                    endpoint,
                    Period(f"{year:04d}-01-01", f"{year:04d}-12-31"),
                    exc,
                    self._existing_count(endpoint, country, Period(f"{year:04d}-01-01", f"{year:04d}-12-31")),
                )
                continue
            for period in periods:
                preserved = self._existing_count(endpoint, country, period)
                try:
                    count = self._import_period(endpoint, country, period)
                except Exception as exc:
                    self._record_failure(summary, endpoint, period, exc, preserved)
                else:
                    summary[endpoint] += count
                    self._record_success(summary, endpoint, period, count, preserved)
        if country.price_strategy == "single_zone":
            zone = country.price_zones[0]
            try:
                price_periods = requested_periods or self._smart_periods("price", zone, year)
            except Exception as exc:
                period = Period(f"{year:04d}-01-01", f"{year:04d}-12-31")
                self._record_failure(summary, "price", period, exc, self._existing_count("price", country, period, zone))
                price_periods = []
            for period in price_periods:
                preserved = self._existing_count("price", country, period, zone)
                try:
                    count = self._import_price(country, zone, period)
                except Exception as exc:
                    self._record_failure(summary, "price", period, exc, preserved)
                else:
                    summary["price"] += count
                    self._record_success(summary, "price", period, count, preserved)
        if months is None:
            period = Period(str(year), str(year))
            preserved = self._existing_count("installed_power", country, period)
            try:
                count = self._import_installed_power(country)
            except Exception as exc:
                self._record_failure(summary, "installed_power", period, exc, preserved)
            else:
                summary["installed_power"] = count
                self._record_success(summary, "installed_power", period, count, preserved)
        else:
            summary["skipped"].append(
                {"endpoint": "installed_power", "reason": "partial_month_import_does_not_replace_snapshots"}
            )
        return summary

    def import_range(
        self,
        country_code: str,
        start_year: int,
        end_year: int | None = None,
        today: date | None = None,
    ) -> dict[str, Any]:
        current = today or date.today()
        last_year = current.year if end_year is None else end_year
        if start_year < ATLAS_MIN_YEAR:
            raise ValueError(f"Energy-Charts history starts at the Atlas limit {ATLAS_MIN_YEAR}")
        if last_year < start_year:
            raise ValueError("History end year must not precede the start year")
        if last_year > current.year:
            raise ValueError(f"History end year must not exceed {current.year}")

        summary: dict[str, Any] = {
            "source": SOURCE_NAME,
            "years": [],
            "errors": 0,
            "successes": [],
            "failures": [],
            "skipped": [],
        }
        code = country_code.upper()
        if code not in ENERGY_CHARTS_COUNTRIES:
            raise ValueError(f"Energy-Charts does not support Atlas country: {country_code}")
        country = COUNTRIES[code]
        for year in range(start_year, last_year + 1):
            if year < current.year and not self.refresh and self._year_is_complete(country, year):
                summary["skipped"].append({"year": year, "reason": "monthly_periods_already_complete"})
                continue
            months = range(1, current.month + 1) if year == current.year else None
            result = self.import_country(country_code, year, months)
            summary["years"].append(year)
            summary["errors"] += result["errors"]
            summary["successes"].extend(
                {**item, "year": year} for item in result["successes"]
            )
            summary["failures"].extend(
                {**item, "year": year} for item in result["failures"]
            )
        return summary

    def _year_is_complete(self, country: Country, year: int) -> bool:
        required = [("public_power", country.code.lower()), ("cbpf", country.code.lower())]
        if country.price_strategy == "single_zone":
            required.append(("price", country.price_zones[0]))
        start = f"{year:04d}-01-01"
        end = f"{year:04d}-12-31"
        for endpoint, target in required:
            imported = self.connection.execute(
                """SELECT 1 FROM import_period
                   WHERE endpoint=? AND target=? AND start_date=? AND end_date=?""",
                (endpoint, target, start, end),
            ).fetchone()
            unavailable = self.connection.execute(
                """SELECT 1 FROM api_cache
                   WHERE endpoint=? AND target=? AND start_date=? AND end_date=? AND status_code=404""",
                (endpoint, target, start, end),
            ).fetchone()
            if not imported and not unavailable:
                return False
        return True

    def _record_success(
        self,
        summary: dict[str, Any],
        endpoint: str,
        period: Period,
        rows: int,
        replaced_rows: int,
    ) -> None:
        summary["successes"].append(
            {
                "endpoint": endpoint,
                "period": f"{period.start}..{period.end}",
                "rows": rows,
                "replaced_rows": replaced_rows,
            }
        )

    def _record_failure(
        self,
        summary: dict[str, Any],
        endpoint: str,
        period: Period,
        exc: Exception,
        preserved_rows: int,
    ) -> None:
        summary["errors"] += 1
        summary["failures"].append(
            {
                "endpoint": endpoint,
                "period": f"{period.start}..{period.end}",
                "error": f"{type(exc).__name__}: {exc}",
                "preserved_rows": preserved_rows,
            }
        )

    def _smart_periods(self, endpoint: str, target: str, year: int) -> list[Period]:
        year_start = f"{year:04d}-01-01"
        year_end = f"{year:04d}-12-31"
        overlap = self.connection.execute(
            """SELECT 1 FROM api_cache
               WHERE endpoint=? AND target=? AND start_date<>'' AND end_date<>''
                 AND end_date>=? AND start_date<=?
               LIMIT 1""",
            (endpoint, target, year_start, year_end),
        ).fetchone()
        # First import is one rate-limit-friendly annual request. If partial
        # cache data exists, month chunks identify and download only gaps.
        return monthly_periods(year) if overlap else [Period(year_start, year_end)]

    def _existing_count(
        self, endpoint: str, country: Country, period: Period, zone: str = ""
    ) -> int:
        if endpoint == "installed_power":
            return self.connection.execute(
                "SELECT COUNT(*) FROM installed_capacity WHERE country_code=?",
                (country.code,),
            ).fetchone()[0]
        params: list[Any] = [country.code, SOURCE_NAME, endpoint, period.start, period.end]
        zone_clause = ""
        if endpoint == "price":
            zone_clause = " AND source_series=?"
            params.append(zone)
        return self.connection.execute(
            f"""SELECT COUNT(*) FROM period_observation
                WHERE country_code=? AND source=? AND source_endpoint=?
                  AND granularity='monthly' AND period_start>=? AND period_start<=?{zone_clause}""",
            params,
        ).fetchone()[0]

    def _atomic_replace(self, operation: Callable[[], int]) -> int:
        self.connection.execute("SAVEPOINT import_unit")
        try:
            count = operation()
            self.connection.execute("RELEASE SAVEPOINT import_unit")
            return count
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT import_unit")
            self.connection.execute("RELEASE SAVEPOINT import_unit")
            raise

    def _clear_period_scope(self, endpoint: str, country: Country, period: Period, zone: str = "") -> None:
        params: list[Any] = [country.code, SOURCE_NAME, endpoint, period.start, period.end]
        zone_clause = ""
        if endpoint == "price":
            zone_clause = " AND source_series=?"
            params.append(zone)
        self.connection.execute(
            f"""DELETE FROM period_observation
                WHERE country_code=? AND source=? AND source_endpoint=?
                  AND granularity='monthly' AND period_start>=? AND period_start<=?{zone_clause}""",
            params,
        )
        self._replace_quality_issue_scope(country.code, endpoint, period)

    def _replace_quality_issue_scope(self, code: str, endpoint: str, period: Period) -> None:
        target_start = date.fromisoformat(period.start)
        target_end = date.fromisoformat(period.end)
        rows = self.connection.execute(
            """SELECT * FROM quality_issue
               WHERE country_code=? AND endpoint=?""",
            (code, endpoint),
        ).fetchall()
        for row in rows:
            try:
                issue_start = date.fromisoformat(str(row["period_start"])[:10])
                issue_end = date.fromisoformat(str(row["period_end"])[:10])
            except ValueError:
                continue
            if issue_end < target_start or issue_start > target_end:
                continue
            self.connection.execute("DELETE FROM quality_issue WHERE id=?", (row["id"],))
            if issue_start < target_start:
                self._issue(
                    code,
                    endpoint,
                    Period(str(issue_start), str(target_start - timedelta(days=1))),
                    row["issue_type"],
                    row["severity"],
                    row["details"],
                )
            if issue_end > target_end:
                self._issue(
                    code,
                    endpoint,
                    Period(str(target_end + timedelta(days=1)), str(issue_end)),
                    row["issue_type"],
                    row["severity"],
                    row["details"],
                )

    def _payload(self, endpoint: str, country: Country, period: Period) -> dict[str, Any]:
        return self.client.get(
            endpoint,
            "country",
            country.code.lower(),
            period.start,
            period.end,
            refresh=self.refresh,
        )

    def _validate_payload(self, endpoint: str, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ValueError(f"{endpoint} payload must be an object")
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            raise ValueError(f"{endpoint} payload contains no data records")
        if endpoint in {"public_power", "cbpf"}:
            if not payload.get("resolution") or not payload.get("interval_minutes"):
                raise ValueError(f"{endpoint} payload has no usable resolution")
            if "series" not in payload:
                raise ValueError(f"{endpoint} payload has no series catalog")
        for index, record in enumerate(data):
            if not isinstance(record, dict) or "timestamp" not in record or not isinstance(record.get("values"), dict):
                raise ValueError(f"{endpoint} record {index} is structurally invalid")

    def _validate_payload_period(self, endpoint: str, payload: dict[str, Any], period: Period) -> None:
        requested_start = date.fromisoformat(period.start)
        requested_end = date.fromisoformat(period.end)
        for index, record in enumerate(payload["data"]):
            timestamp = str(record["timestamp"])
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"{endpoint} record {index} has an invalid timestamp: {timestamp}") from exc
            if parsed.tzinfo is None:
                raise ValueError(f"{endpoint} record {index} timestamp has no timezone offset: {timestamp}")
            if not requested_start <= parsed.date() <= requested_end:
                raise ValueError(
                    f"{endpoint} record {index} timestamp {timestamp} is outside requested period "
                    f"{period.start}..{period.end}"
                )

    def _import_period(self, endpoint: str, country: Country, period: Period) -> int:
        payload = self._payload(endpoint, country, period)
        if payload.get("coverage_status") == "not_available":
            def clear_unavailable() -> int:
                self._clear_period_scope(endpoint, country, period)
                self._store_period(endpoint, country.code.lower(), period, payload, 0)
                return 0

            return self._atomic_replace(clear_unavailable)
        self._validate_payload(endpoint, payload)
        self._validate_payload_period(endpoint, payload, period)

        def replace() -> int:
            self._clear_period_scope(endpoint, country, period)
            if endpoint == "public_power":
                count = self._store_public_power(country, payload)
            elif endpoint == "cbpf":
                count = self._store_flows(country, payload)
            else:
                raise ValueError(endpoint)
            self._check_intervals(endpoint, country, period, payload)
            self._store_period(endpoint, country.code.lower(), period, payload, count)
            return count

        return self._atomic_replace(replace)

    def _store_public_power(self, country: Country, payload: dict[str, Any]) -> int:
        interval = int(payload["interval_minutes"])
        unit = str(payload.get("unit", "MW"))
        totals: dict[tuple[str, str], float] = defaultdict(float)
        all_unmapped: set[str] = set()
        series_items = payload["series"] if isinstance(payload["series"], list) else [payload["series"]]
        series_ids = {str(item["id"]) for item in series_items}
        missing_expected = sorted(EXPECTED_PUBLIC_POWER_SERIES[country.code] - series_ids)
        if missing_expected:
            self._issue(
                country.code,
                "public_power",
                Period(payload.get("available_from", ""), payload.get("available_until", "")),
                "missing_expected_series",
                "error",
                json.dumps(missing_expected),
            )
        load_missing = sum(1 for record in payload.get("data", []) if record["values"].get("load") is None)
        if load_missing:
            self._issue(
                country.code,
                "public_power",
                Period(payload.get("available_from", ""), payload.get("available_until", "")),
                "missing_metric_values",
                "warning",
                f"load: {load_missing}/{len(payload.get('data', []))}",
            )
        for record in payload.get("data", []):
            timestamp = str(record["timestamp"])
            metrics, unmapped = normalize_public_power_record(record["values"], payload["series"])
            all_unmapped.update(unmapped)
            for metric, value in metrics.items():
                totals[(timestamp[:7], metric)] += (
                    power_to_mw(value, unit) * interval / 60 / 1_000_000
                )
        if all_unmapped:
            self._issue(
                country.code,
                "public_power",
                Period(payload.get("available_from", ""), payload.get("available_until", "")),
                "unmapped_generation_categories",
                "warning",
                json.dumps(sorted(all_unmapped)),
            )
        for (token, metric), value in sorted(totals.items()):
            self._insert_period_value(country.code, token, "public_power", "", metric, value, "TWh")
        return len(totals)

    def _store_flows(self, country: Country, payload: dict[str, Any]) -> int:
        interval = int(payload["interval_minutes"])
        unit = str(payload.get("unit", "GW"))
        totals: dict[tuple[str, str], float] = defaultdict(float)
        for record in payload.get("data", []):
            timestamp = str(record["timestamp"])
            imports, exports, net, _ = split_physical_flows(record["values"], unit)
            for metric, value in (("import_total", imports), ("export_total", exports), ("net_import", net)):
                totals[(timestamp[:7], metric)] += value * interval / 60 / 1_000_000
        for (token, metric), value in sorted(totals.items()):
            self._insert_period_value(country.code, token, "cbpf", "", metric, value, "TWh")
        return len(totals)

    def _import_price(self, country: Country, zone: str, period: Period) -> int:
        payload = self.client.get("price", "bzn", zone, period.start, period.end, refresh=self.refresh)
        if payload.get("coverage_status") == "not_available":
            def clear_unavailable() -> int:
                self._clear_period_scope("price", country, period, zone)
                self._store_period("price", zone, period, payload, 0)
                return 0

            return self._atomic_replace(clear_unavailable)
        self._validate_payload("price", payload)
        self._validate_payload_period("price", payload, period)

        def replace() -> int:
            self._clear_period_scope("price", country, period, zone)
            records = list(payload.get("data", []))
            utc_times = [datetime.fromisoformat(iso_to_utc(str(record["timestamp"]))) for record in records]
            durations: list[int] = []
            for current, following in zip(utc_times, utc_times[1:]):
                durations.append(int((following - current).total_seconds() / 60))
            durations.append(durations[-1] if durations else int(payload.get("interval_minutes") or 60))
            observed_durations = sorted(set(durations))
            unusual = [value for value in observed_durations if value not in {15, 30, 60}]
            if unusual:
                self._issue(
                    country.code,
                    "price",
                    period,
                    "unexpected_price_interval",
                    "warning",
                    json.dumps(unusual),
                )
            unit = str(payload.get("unit", "EUR/MWh"))
            month_pairs: dict[str, list[tuple[float, int]]] = defaultdict(list)
            for record, interval in zip(records, durations):
                value = record["values"].get("day_ahead_price")
                if value is None:
                    continue
                month_pairs[str(record["timestamp"])[:7]].append((float(value), interval))
            rows = 0
            for token, pairs in sorted(month_pairs.items()):
                total_minutes = sum(weight for _, weight in pairs)
                average = sum(value * weight for value, weight in pairs) / total_minutes
                negative = [(value, weight) for value, weight in pairs if value < 0]
                metrics = (
                    ("day_ahead_price", average, unit),
                    ("day_ahead_price_median", _weighted_median(pairs), unit),
                    ("day_ahead_price_min", min(value for value, _ in pairs), unit),
                    ("day_ahead_price_max", max(value for value, _ in pairs), unit),
                    ("negative_price_intervals", float(len(negative)), "count"),
                    ("negative_price_hours", sum(weight for _, weight in negative) / 60, "hours"),
                    ("price_weight_hours", total_minutes / 60, "hours"),
                )
                for metric, value, metric_unit in metrics:
                    if value is not None:
                        self._insert_period_value(
                            country.code, token, "price", zone, metric, value, metric_unit
                        )
                        rows += 1
            self._store_period("price", zone, period, payload, rows)
            return rows

        return self._atomic_replace(replace)

    def _import_installed_power(self, country: Country) -> int:
        payload = self.client.get(
            "installed_power", "country", country.code.lower(), extra={"time_step": "yearly"}, refresh=self.refresh
        )
        self._validate_payload("installed_power", payload)
        if "series" not in payload or not payload.get("resolution"):
            raise ValueError("installed_power payload has no series catalog or resolution")

        def replace() -> int:
            self.connection.execute("DELETE FROM installed_capacity WHERE country_code=?", (country.code,))
            self.connection.execute(
                "DELETE FROM quality_issue WHERE country_code=? AND endpoint='installed_power'",
                (country.code,),
            )
            series = payload["series"] if isinstance(payload["series"], list) else [payload["series"]]
            units = {str(item["id"]): str(item.get("unit", payload.get("unit", "GW"))) for item in series}
            rows = 0
            for record in payload.get("data", []):
                for category, value in record["values"].items():
                    if value is None or units.get(category, "").lower() not in {"mw", "gw"}:
                        continue
                    self.connection.execute(
                        """INSERT INTO installed_capacity
                           (country_code,country_name,timestamp,source,source_resolution,category,value_mw,quality_status)
                           VALUES (?,?,?,?,?,?,?,?)
                           ON CONFLICT(country_code,timestamp,category,source) DO UPDATE SET value_mw=excluded.value_mw""",
                        (
                            country.code,
                            country.name,
                            record["timestamp"],
                            SOURCE_NAME,
                            payload["resolution"],
                            category,
                            power_to_mw(value, units[category]),
                            "observed_end_of_period",
                        ),
                    )
                    rows += 1
            self._store_period("installed_power", country.code.lower(), Period("", ""), payload, rows)
            return rows

        return self._atomic_replace(replace)

    def _insert_period_value(
        self, code: str, token: str, endpoint: str, series: str, metric: str, value: float, unit: str
    ) -> None:
        period_start, period_end = _month_bounds(token)
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,'monthly',?,?,?,?,?,?,?)""",
            (
                code,
                period_start,
                period_end,
                SOURCE_NAME,
                endpoint,
                series,
                metric,
                value,
                unit,
                _period_quality(token),
            ),
        )

    def _store_period(self, endpoint: str, target: str, period: Period, payload: dict[str, Any], count: int) -> None:
        self.connection.execute(
            """INSERT INTO import_period
               (endpoint,target,start_date,end_date,imported_at,record_count,available_from,available_until,
                resolution,interval_minutes,unit,license)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(endpoint,target,start_date,end_date) DO UPDATE SET
                 imported_at=excluded.imported_at,record_count=excluded.record_count,
                 available_from=excluded.available_from,available_until=excluded.available_until,
                 resolution=excluded.resolution,interval_minutes=excluded.interval_minutes,
                 unit=excluded.unit,license=excluded.license""",
            (
                endpoint,
                target,
                period.start,
                period.end,
                datetime.now(UTC).isoformat(),
                count,
                payload.get("available_from"),
                payload.get("available_until"),
                payload.get("resolution"),
                payload.get("interval_minutes"),
                payload.get("unit"),
                payload.get("license"),
            ),
        )

    def _check_intervals(self, endpoint: str, country: Country, period: Period, payload: dict[str, Any]) -> None:
        interval = payload.get("interval_minutes")
        data = payload.get("data", [])
        if not interval or not data:
            return
        timestamps = [iso_to_utc(str(row["timestamp"])) for row in data]
        duplicates = len(timestamps) - len(set(timestamps))
        if duplicates:
            self._issue(country.code, endpoint, period, "duplicate_intervals", "error", str(duplicates))
        parsed = sorted(datetime.fromisoformat(value) for value in set(timestamps))
        gaps = 0
        for previous, current in zip(parsed, parsed[1:]):
            missing = int((current - previous).total_seconds() // (int(interval) * 60)) - 1
            gaps += max(0, missing)
        if gaps:
            self._issue(country.code, endpoint, period, "missing_intervals", "warning", str(gaps))

    def _issue(self, code: str, endpoint: str, period: Period, kind: str, severity: str, details: str) -> None:
        self.connection.execute(
            """INSERT OR IGNORE INTO quality_issue
               (country_code,endpoint,period_start,period_end,issue_type,severity,details)
               VALUES (?,?,?,?,?,?,?)""",
            (code, endpoint, period.start, period.end, kind, severity, details[:4000]),
        )
