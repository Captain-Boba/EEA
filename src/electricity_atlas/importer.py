from __future__ import annotations

import calendar
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Iterable

from .client import ApiError, EnergyChartsClient
from .config import COUNTRIES, EXPECTED_PUBLIC_POWER_SERIES, SOURCE_NAME, Country
from .normalization import iso_to_utc, normalize_public_power_record, power_to_mw, split_physical_flows


@dataclass(frozen=True)
class Period:
    start: str
    end: str


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

    def import_country(self, country_code: str, year: int, months: Iterable[int] | None = None) -> dict[str, int]:
        code = country_code.upper()
        if code not in COUNTRIES:
            raise ValueError(f"Unsupported pilot country: {country_code}")
        country = COUNTRIES[code]
        year_start = f"{year:04d}-01-01"
        year_end = f"{year:04d}-12-31T23:59:59"
        self.connection.execute(
            """DELETE FROM quality_issue
               WHERE country_code=? AND period_start<=? AND period_end>=?""",
            (code, year_end, year_start),
        )
        next_year = f"{year + 1:04d}-01-01"
        self.connection.execute(
            "DELETE FROM observation WHERE country_code=? AND timestamp>=? AND timestamp<?",
            (code, year_start, next_year),
        )
        self.connection.execute(
            "DELETE FROM bilateral_flow WHERE country_code=? AND timestamp>=? AND timestamp<?",
            (code, year_start, next_year),
        )
        counts = {"public_power": 0, "cbpf": 0, "price": 0, "installed_power": 0, "errors": 0}
        requested_periods = monthly_periods(year, months) if months is not None else None
        for endpoint in ("public_power", "cbpf"):
            periods = requested_periods or self._smart_periods(endpoint, country.code.lower(), year)
            for period in periods:
                try:
                    counts[endpoint] += self._import_period(endpoint, country, period)
                except ApiError as exc:
                    counts["errors"] += 1
                    self._issue(country.code, endpoint, period, "api_error", "error", str(exc))
        if country.price_strategy == "single_zone":
            price_periods = requested_periods or self._smart_periods("price", country.price_zones[0], year)
            for period in price_periods:
                try:
                    counts["price"] += self._import_price(country, country.price_zones[0], period)
                except ApiError as exc:
                    counts["errors"] += 1
                    self._issue(country.code, "price", period, "api_error", "error", str(exc))
        try:
            counts["installed_power"] = self._import_installed_power(country)
        except ApiError as exc:
            counts["errors"] += 1
            self._issue(country.code, "installed_power", Period(str(year), str(year)), "api_error", "error", str(exc))
        self.connection.commit()
        return counts

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

    def _payload(self, endpoint: str, country: Country, period: Period) -> dict[str, Any]:
        return self.client.get(
            endpoint,
            "country",
            country.code.lower(),
            period.start,
            period.end,
            refresh=self.refresh,
        )

    def _import_period(self, endpoint: str, country: Country, period: Period) -> int:
        payload = self._payload(endpoint, country, period)
        if endpoint == "public_power":
            count = self._store_public_power(country, payload)
        elif endpoint == "cbpf":
            count = self._store_flows(country, payload)
        else:
            raise ValueError(endpoint)
        self._store_period(endpoint, country.code.lower(), period, payload, count)
        self._check_intervals(endpoint, country, period, payload)
        return count

    def _store_public_power(self, country: Country, payload: dict[str, Any]) -> int:
        interval = int(payload["interval_minutes"])
        resolution = str(payload["resolution"])
        unit = str(payload.get("unit", "MW"))
        rows = 0
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
                self._upsert_observation(country, "", timestamp, "public_power", resolution, interval, metric, power_to_mw(value, unit), "MW")
                rows += 1
            reported_share = record["values"].get("renewable_share_of_generation")
            if reported_share is not None:
                self._upsert_observation(
                    country,
                    "",
                    timestamp,
                    "public_power",
                    resolution,
                    interval,
                    "source_renewable_share_generation",
                    float(reported_share),
                    "%",
                )
                rows += 1
        if all_unmapped:
            self._issue(
                country.code,
                "public_power",
                Period(payload.get("available_from", ""), payload.get("available_until", "")),
                "unmapped_generation_categories",
                "warning",
                json.dumps(sorted(all_unmapped)),
            )
        return rows

    def _store_flows(self, country: Country, payload: dict[str, Any]) -> int:
        interval = int(payload["interval_minutes"])
        resolution = str(payload["resolution"])
        unit = str(payload.get("unit", "GW"))
        rows = 0
        for record in payload.get("data", []):
            timestamp = str(record["timestamp"])
            imports, exports, net, bilateral = split_physical_flows(record["values"], unit)
            for metric, value in (("import_total", imports), ("export_total", exports), ("net_import", net)):
                self._upsert_observation(country, "", timestamp, "cbpf", resolution, interval, metric, value, "MW")
                rows += 1
            for counterparty, value in bilateral.items():
                self.connection.execute(
                    """INSERT INTO bilateral_flow
                       (country_code,counterparty,timestamp,timestamp_utc,source,source_resolution,interval_minutes,flow_mw)
                       VALUES (?,?,?,?,?,?,?,?)
                       ON CONFLICT(country_code,counterparty,timestamp_utc,source) DO UPDATE SET flow_mw=excluded.flow_mw""",
                    (country.code, counterparty, timestamp, iso_to_utc(timestamp), SOURCE_NAME, resolution, interval, value),
                )
        return rows

    def _import_price(self, country: Country, zone: str, period: Period) -> int:
        payload = self.client.get("price", "bzn", zone, period.start, period.end, refresh=self.refresh)
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
        resolution = str(payload.get("resolution") or "mixed:" + ",".join(f"PT{x}M" for x in observed_durations))
        unit = str(payload.get("unit", "EUR/MWh"))
        rows = 0
        for record, interval in zip(records, durations):
            value = record["values"].get("day_ahead_price")
            if value is None:
                continue
            self._upsert_observation(country, zone, str(record["timestamp"]), "price", resolution, interval, "day_ahead_price", float(value), unit)
            rows += 1
        self._store_period("price", zone, period, payload, rows)
        return rows

    def _import_installed_power(self, country: Country) -> int:
        payload = self.client.get(
            "installed_power", "country", country.code.lower(), extra={"time_step": "yearly"}, refresh=self.refresh
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

    def _upsert_observation(
        self,
        country: Country,
        zone: str,
        timestamp: str,
        endpoint: str,
        resolution: str,
        interval: int,
        metric: str,
        value: float,
        unit: str,
    ) -> None:
        self.connection.execute(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(country_code,bidding_zone,timestamp_utc,metric,source_endpoint)
               DO UPDATE SET value=excluded.value,unit=excluded.unit,quality_status=excluded.quality_status""",
            (
                country.code,
                country.name,
                zone,
                timestamp,
                iso_to_utc(timestamp),
                SOURCE_NAME,
                endpoint,
                resolution,
                interval,
                metric,
                value,
                unit,
                "observed",
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
