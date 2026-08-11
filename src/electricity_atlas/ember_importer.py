from __future__ import annotations

import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterable

from .config import ATLAS_MIN_YEAR, EMBER_COUNTRIES, EMBER_ISO3, EMBER_SOURCE_NAME
from .ember_client import EmberClient


EMBER_SERIES_TO_METRIC = {
    "bioenergy": "generation_biomass",
    "coal": "generation_coal",
    "gas": "generation_gas",
    "hydro": "generation_hydro",
    "nuclear": "generation_nuclear",
    "other fossil": "generation_other_fossil",
    "other renewables": "generation_other_renewables",
    "solar": "generation_solar",
    "wind": "generation_wind",
}
EMBER_AGGREGATE_SERIES_TO_METRIC = {
    "total generation": "generation_total",
    "demand": "demand_total",
    "renewables": "generation_renewables",
    "fossil": "generation_fossil",
}
EMBER_IGNORED_AGGREGATE_SERIES = frozenset(
    {"clean", "wind and solar", "hydro, bioenergy and other renewables"}
)


@dataclass(frozen=True)
class EmberPeriodRow:
    country_code: str
    period_start: str
    period_end: str
    granularity: str
    source_endpoint: str
    source_series: str
    metric: str
    value: float
    unit: str


def _month_token(year: int, month: int) -> str:
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}")
    return f"{year:04d}-{month:02d}"


def _next_month_token(value: str) -> str:
    year, month = (int(part) for part in value.split("-"))
    return f"{year + 1:04d}-01" if month == 12 else f"{year:04d}-{month + 1:02d}"


def _record_period(value: str, granularity: str) -> tuple[str, str]:
    if granularity == "yearly":
        if len(value) != 4 or not value.isdigit():
            raise ValueError(f"Invalid yearly Ember date: {value}")
        year = int(value)
        return f"{year:04d}-01-01", f"{year:04d}-12-31"
    token = value[:7]
    if len(token) != 7 or token[4] != "-":
        raise ValueError(f"Invalid monthly Ember date: {value}")
    year, month = (int(part) for part in token.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


class EmberImporter:
    def __init__(
        self,
        connection: sqlite3.Connection,
        refresh: bool = False,
        client: EmberClient | None = None,
    ):
        self.connection = connection
        self.refresh = refresh
        self.client = client or EmberClient(connection)

    def import_country(self, country_code: str, year: int, months: Iterable[int] | None = None) -> dict[str, Any]:
        code = country_code.upper()
        self._validate_country(code)
        selected_months = None if months is None else list(months)
        units: list[tuple[str, str, str, str]] = []
        for dataset in ("electricity-generation", "electricity-demand", "carbon-intensity"):
            if selected_months is None:
                units.append((dataset, "monthly", f"{year:04d}-01", f"{year:04d}-12"))
                units.append((dataset, "yearly", str(year), str(year)))
            else:
                for month in selected_months:
                    token = _month_token(year, month)
                    units.append((dataset, "monthly", token, token))

        return self._import_units(code, units)

    def import_range(
        self,
        country_code: str,
        start_year: int,
        end_year: int | None = None,
        today: date | None = None,
    ) -> dict[str, Any]:
        code = country_code.upper()
        self._validate_country(code)
        current = today or date.today()
        last_year = current.year if end_year is None else end_year
        if start_year < ATLAS_MIN_YEAR:
            raise ValueError(f"Ember history starts at the Atlas limit {ATLAS_MIN_YEAR}")
        if last_year < start_year:
            raise ValueError("History end year must not precede the start year")
        if last_year > current.year:
            raise ValueError(f"History end year must not exceed {current.year}")

        completed_year_end = min(last_year, current.year - 1)
        units: list[tuple[str, str, str, str]] = []
        for dataset in ("electricity-generation", "electricity-demand", "carbon-intensity"):
            if completed_year_end >= start_year:
                units.append(
                    (
                        dataset,
                        "monthly",
                        f"{start_year:04d}-01",
                        f"{completed_year_end:04d}-12",
                    )
                )
                if dataset != "electricity-demand":
                    units.append(
                        (dataset, "yearly", str(start_year), str(completed_year_end))
                    )
            if last_year == current.year:
                units.append(
                    (
                        dataset,
                        "monthly",
                        f"{current.year:04d}-01",
                        f"{current.year:04d}-{current.month:02d}",
                    )
                )
        return self._import_units(code, units)

    @staticmethod
    def _validate_country(code: str) -> None:
        if code not in EMBER_COUNTRIES or code not in EMBER_ISO3:
            raise ValueError(f"Unsupported Ember country: {code}")

    def _import_units(
        self, code: str, units: Iterable[tuple[str, str, str, str]]
    ) -> dict[str, Any]:

        summary: dict[str, Any] = {
            "source": EMBER_SOURCE_NAME,
            "rows": 0,
            "errors": 0,
            "successes": [],
            "failures": [],
        }
        for dataset, granularity, start_date, end_date in units:
            endpoint = f"{dataset}/{granularity}"
            preserved = self._existing_count(code, endpoint, granularity, start_date, end_date)
            try:
                count = self._import_endpoint(code, endpoint, granularity, start_date, end_date)
            except Exception as exc:
                summary["errors"] += 1
                summary["failures"].append(
                    {
                        "endpoint": endpoint,
                        "period": f"{start_date}..{end_date}",
                        "error": f"{type(exc).__name__}: {exc}",
                        "preserved_rows": preserved,
                    }
                )
            else:
                summary["rows"] += count
                summary["successes"].append(
                    {
                        "endpoint": endpoint,
                        "period": f"{start_date}..{end_date}",
                        "rows": count,
                        "replaced_rows": preserved,
                    }
                )
        return summary

    def _existing_count(
        self, code: str, endpoint: str, granularity: str, start_date: str, end_date: str
    ) -> int:
        start, _ = _record_period(start_date, granularity)
        end, _ = _record_period(end_date, granularity)
        return self.connection.execute(
            """SELECT COUNT(*) FROM period_observation
               WHERE country_code=? AND source=? AND source_endpoint=? AND granularity=?
                 AND period_start>=? AND period_start<=?""",
            (code, EMBER_SOURCE_NAME, endpoint, granularity, start, end),
        ).fetchone()[0]

    def _atomic_replace(self, operation: Callable[[], int]) -> int:
        self.connection.execute("SAVEPOINT ember_import_unit")
        try:
            count = operation()
            self.connection.execute("RELEASE SAVEPOINT ember_import_unit")
            return count
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT ember_import_unit")
            self.connection.execute("RELEASE SAVEPOINT ember_import_unit")
            raise

    def _import_endpoint(
        self, code: str, endpoint: str, granularity: str, start_date: str, end_date: str
    ) -> int:
        api_end_date = _next_month_token(end_date) if granularity == "monthly" else end_date
        if endpoint.startswith("electricity-generation/"):
            payloads = [
                self.client.get(
                    endpoint,
                    EMBER_ISO3[code],
                    start_date,
                    api_end_date,
                    extra={"is_aggregate_series": aggregate},
                    refresh=self.refresh,
                )
                for aggregate in ("false", "true")
            ]
            payload = {"data": []}
            seen_records: set[tuple[Any, ...]] = set()
            for item in payloads:
                if not isinstance(item, dict) or not isinstance(item.get("data"), list):
                    raise ValueError(f"{endpoint} payload has no data list")
                for record in item["data"]:
                    if not isinstance(record, dict):
                        payload["data"].append(record)
                        continue
                    key = (
                        record.get("entity_code"),
                        record.get("date"),
                        record.get("series"),
                        record.get("is_aggregate_series"),
                    )
                    if key not in seen_records:
                        payload["data"].append(record)
                        seen_records.add(key)
        else:
            payload = self.client.get(
                endpoint,
                EMBER_ISO3[code],
                start_date,
                api_end_date,
                refresh=self.refresh,
            )
        rows = self._normalize_payload(code, endpoint, granularity, start_date, end_date, payload)
        range_start, _ = _record_period(start_date, granularity)
        range_end, _ = _record_period(end_date, granularity)

        def replace() -> int:
            self.connection.execute(
                """DELETE FROM period_observation
                   WHERE country_code=? AND source=? AND source_endpoint=? AND granularity=?
                     AND period_start>=? AND period_start<=?""",
                (code, EMBER_SOURCE_NAME, endpoint, granularity, range_start, range_end),
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        row.country_code,
                        row.period_start,
                        row.period_end,
                        row.granularity,
                        EMBER_SOURCE_NAME,
                        row.source_endpoint,
                        row.source_series,
                        row.metric,
                        row.value,
                        row.unit,
                        "observed",
                    )
                    for row in rows
                ],
            )
            return len(rows)

        return self._atomic_replace(replace)

    def _normalize_payload(
        self,
        code: str,
        endpoint: str,
        granularity: str,
        start_date: str,
        end_date: str,
        payload: dict[str, Any],
    ) -> list[EmberPeriodRow]:
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError(f"{endpoint} payload has no data list")
        expected_iso3 = EMBER_ISO3[code]
        requested_start = _record_period(start_date, granularity)[0]
        requested_end = _record_period(end_date, granularity)[0]
        rows: list[EmberPeriodRow] = []
        for index, record in enumerate(payload["data"]):
            if not isinstance(record, dict):
                raise ValueError(f"{endpoint} record {index} is not an object")
            if record.get("entity_code") != expected_iso3:
                raise ValueError(f"{endpoint} record {index} has an unexpected entity code")
            record_date = str(record.get("date", ""))
            period_start, period_end = _record_period(record_date, granularity)
            if not requested_start <= period_start <= requested_end:
                raise ValueError(f"{endpoint} record {index} is outside the requested period")
            if endpoint.startswith("electricity-generation/"):
                series = str(record.get("series", "")).strip()
                series_key = series.casefold()
                is_aggregate = record.get("is_aggregate_series") is True
                if not series:
                    raise ValueError(f"{endpoint} record {index} has no series")
                if series_key == "net imports":
                    metric = "net_imports"
                elif is_aggregate:
                    if series_key in EMBER_IGNORED_AGGREGATE_SERIES:
                        continue
                    metric = EMBER_AGGREGATE_SERIES_TO_METRIC.get(series_key)
                else:
                    metric = EMBER_SERIES_TO_METRIC.get(series_key)
                if metric is None:
                    raise ValueError(f"{endpoint} record {index} has an unsupported series")
                value = record.get("generation_twh")
                if value is not None:
                    rows.append(EmberPeriodRow(code, period_start, period_end, granularity, endpoint, series, metric, float(value), "TWh"))
                share = record.get("share_of_generation_pct")
                if share is not None and metric not in {"net_imports", "demand_total"}:
                    rows.append(EmberPeriodRow(code, period_start, period_end, granularity, endpoint, series, "share_of_generation_pct", float(share), "%"))
            elif endpoint.startswith("electricity-demand/"):
                value = record.get("demand_twh")
                if value is not None:
                    rows.append(EmberPeriodRow(code, period_start, period_end, granularity, endpoint, "", "consumption", float(value), "TWh"))
            elif endpoint.startswith("carbon-intensity/"):
                value = record.get("emissions_intensity_gco2_per_kwh")
                if value is not None:
                    rows.append(EmberPeriodRow(code, period_start, period_end, granularity, endpoint, "", "carbon_intensity", float(value), "gCO2/kWh"))
            else:
                raise ValueError(f"Unsupported Ember endpoint: {endpoint}")
        return rows
