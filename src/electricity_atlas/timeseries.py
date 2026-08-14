from __future__ import annotations

import math
import re
import sqlite3
from datetime import date
from typing import Any, Iterable

from .aggregation import aggregate_country
from .config import ATLAS_MIN_YEAR, COUNTRIES
from .metrics import METRICS_BY_ID


MONTH_TOKEN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
YEAR_TOKEN = re.compile(r"^\d{4}$")
MAX_COUNTRIES = 10


def build_timeseries(
    connection: sqlite3.Connection,
    metric_id: str,
    country_codes: Iterable[str],
    start: str,
    end: str,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    current = today or date.today()
    metric = METRICS_BY_ID.get(metric_id)
    if metric is None:
        raise ValueError("metric must be a known Atlas metric")
    availability = metric["temporal_availability"]
    if availability["monthly"]:
        granularity = "monthly"
    elif availability["yearly"]:
        granularity = "yearly"
    else:
        raise ValueError("metric is snapshot-only and has no time series")

    codes = [code.strip().upper() for code in country_codes if code.strip()]
    if not 1 <= len(codes) <= MAX_COUNTRIES:
        raise ValueError("countries must contain 1 to 10 Atlas country codes")
    if len(set(codes)) != len(codes):
        raise ValueError("countries must not contain duplicate country codes")
    invalid = [code for code in codes if code not in COUNTRIES]
    if invalid:
        raise ValueError(f"unknown Atlas country code: {invalid[0]}")

    periods = _periods(start, end, granularity, current)
    country_points: dict[str, list[dict[str, Any]]] = {code: [] for code in codes}
    average_points: list[dict[str, Any]] = []

    for period in periods:
        year = int(period[:4])
        month = int(period[5:7]) if granularity == "monthly" else None
        rows = {
            code: aggregate_country(connection, code, year, month)
            for code in COUNTRIES
        }
        for code in codes:
            country_points[code].append(_point(period, rows[code], metric_id))
        values = [
            float(row[metric_id])
            for row in rows.values()
            if row.get(metric_id) is not None and math.isfinite(float(row[metric_id]))
        ]
        period_status = next(iter(rows.values()))["period_status"]
        average_points.append(
            {
                "period": period,
                "value": sum(values) / len(values) if values else None,
                "data_status": "available" if values else "missing",
                "period_status": period_status,
            }
        )

    baseline_year = int(periods[0][:4])
    baseline_periods = _baseline_periods(periods, granularity, baseline_year)
    country_baselines = {
        code: [
            _point(
                baseline_period,
                aggregate_country(
                    connection,
                    code,
                    int(baseline_period[:4]),
                    int(baseline_period[5:7]) if granularity == "monthly" else None,
                ),
                metric_id,
            )
            for baseline_period in baseline_periods
        ]
        for code in codes
    }

    return {
        "metric": dict(metric),
        "granularity": granularity,
        "start": periods[0],
        "end": periods[-1],
        "comparison_baseline": {
            "year": baseline_year,
            "method": "same_calendar_month" if granularity == "monthly" else "annual",
        },
        "countries": [
            {
                "country_code": code,
                "country_name": COUNTRIES[code].name,
                "values": country_points[code],
                "baseline_values": country_baselines[code],
            }
            for code in codes
        ],
        "atlas_average": {
            "label": "Atlas-Durchschnitt",
            "values": average_points,
        },
    }


def _baseline_periods(
    periods: list[str], granularity: str, baseline_year: int
) -> list[str]:
    if granularity == "yearly":
        return [str(baseline_year)]
    months = sorted({period[5:7] for period in periods})
    return [f"{baseline_year:04d}-{month}" for month in months]


def _point(period: str, row: dict[str, Any], metric_id: str) -> dict[str, Any]:
    value = row.get(metric_id)
    if value is not None:
        value = float(value)
        if not math.isfinite(value):
            value = None
    return {
        "period": period,
        "value": value,
        "data_status": "available" if value is not None else "missing",
        "period_status": row["period_status"],
    }


def _periods(start: str, end: str, granularity: str, current: date) -> list[str]:
    if granularity == "monthly":
        start_pair = _month(start, "start")
        end_pair = _month(end, "end")
        current_pair = (current.year, current.month)
        if start_pair < (ATLAS_MIN_YEAR, 1) or end_pair > current_pair:
            raise ValueError(
                f"monthly range must be between {ATLAS_MIN_YEAR:04d}-01 and "
                f"{current.year:04d}-{current.month:02d}"
            )
        if start_pair > end_pair:
            raise ValueError("start must not be after end")
        year, month = start_pair
        periods: list[str] = []
        while (year, month) <= end_pair:
            periods.append(f"{year:04d}-{month:02d}")
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
        return periods

    start_year = _year(start, "start")
    end_year = _year(end, "end")
    if start_year < ATLAS_MIN_YEAR or end_year > current.year:
        raise ValueError(
            f"yearly range must be between {ATLAS_MIN_YEAR:04d} and {current.year:04d}"
        )
    if start_year > end_year:
        raise ValueError("start must not be after end")
    return [str(year) for year in range(start_year, end_year + 1)]


def _month(value: str, label: str) -> tuple[int, int]:
    match = MONTH_TOKEN.fullmatch(value)
    if not match:
        raise ValueError(f"{label} must use YYYY-MM for a monthly metric")
    return int(match.group(1)), int(match.group(2))


def _year(value: str, label: str) -> int:
    if not YEAR_TOKEN.fullmatch(value):
        raise ValueError(f"{label} must use YYYY for a yearly metric")
    return int(value)
