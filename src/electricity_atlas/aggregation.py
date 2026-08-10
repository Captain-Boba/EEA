from __future__ import annotations

import calendar
import math
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from .config import COUNTRIES, GENERATION_METRICS, RENEWABLE_METRICS
from .normalization import mwh_to_twh, mw_interval_to_mwh


def period_bounds(year: int, month: int | None = None) -> tuple[str, str]:
    if month is None:
        return f"{year:04d}-01-01", f"{year + 1:04d}-01-01"
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if month == 12:
        return f"{year:04d}-12-01", f"{year + 1:04d}-01-01"
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month + 1:02d}-01"


def renewable_share(renewable_mwh: float, generation_mwh: float) -> float | None:
    if generation_mwh <= 0:
        return None
    return renewable_mwh / generation_mwh * 100.0


def net_import_balance(import_mwh: float, export_mwh: float) -> float:
    return import_mwh - export_mwh


def weighted_mean(values: Iterable[tuple[float, float]]) -> float | None:
    pairs = [(float(value), float(weight)) for value, weight in values if weight > 0 and math.isfinite(value)]
    total_weight = sum(weight for _, weight in pairs)
    if not pairs or total_weight == 0:
        return None
    return sum(value * weight for value, weight in pairs) / total_weight


def weighted_median(values: Iterable[tuple[float, float]]) -> float | None:
    pairs = sorted((float(value), float(weight)) for value, weight in values if weight > 0 and math.isfinite(value))
    if not pairs:
        return None
    midpoint = sum(weight for _, weight in pairs) / 2.0
    cumulative = 0.0
    for index, (value, weight) in enumerate(pairs):
        cumulative += weight
        if cumulative == midpoint and index + 1 < len(pairs):
            return (value + pairs[index + 1][0]) / 2.0
        if cumulative > midpoint:
            return value
    return pairs[-1][0]


def _energy_by_metric(connection: sqlite3.Connection, code: str, start: str, end: str) -> dict[str, float]:
    rows = connection.execute(
        """SELECT metric, value, interval_minutes
           FROM observation
           WHERE country_code=? AND bidding_zone='' AND timestamp>=? AND timestamp<?
             AND unit='MW' AND interval_minutes IS NOT NULL""",
        (code, start, end),
    )
    totals: dict[str, float] = {}
    for row in rows:
        totals[row["metric"]] = totals.get(row["metric"], 0.0) + mw_interval_to_mwh(
            row["value"], row["interval_minutes"]
        )
    return totals


def _price_stats(connection: sqlite3.Connection, code: str, start: str, end: str) -> dict[str, Any]:
    rows = list(
        connection.execute(
            """SELECT value, interval_minutes
               FROM observation
               WHERE country_code=? AND metric='day_ahead_price' AND timestamp>=? AND timestamp<?
               ORDER BY timestamp_utc""",
            (code, start, end),
        )
    )
    if not rows:
        return {
            "price_avg_eur_mwh": None,
            "price_median_eur_mwh": None,
            "price_min_eur_mwh": None,
            "price_max_eur_mwh": None,
            "negative_price_intervals": None,
            "negative_price_hours": None,
        }
    pairs = [(row["value"], row["interval_minutes"] or 0) for row in rows]
    negative = [row for row in rows if row["value"] < 0]
    return {
        "price_avg_eur_mwh": weighted_mean(pairs),
        "price_median_eur_mwh": weighted_median(pairs),
        "price_min_eur_mwh": min(row["value"] for row in rows),
        "price_max_eur_mwh": max(row["value"] for row in rows),
        "negative_price_intervals": len(negative),
        "negative_price_hours": sum((row["interval_minutes"] or 0) / 60 for row in negative),
    }


def _installed_capacity(connection: sqlite3.Connection, code: str, end: str) -> float | None:
    timestamp_row = connection.execute(
        """SELECT MAX(timestamp) AS timestamp FROM installed_capacity
           WHERE country_code=? AND timestamp<?""",
        (code, end),
    ).fetchone()
    if not timestamp_row or not timestamp_row["timestamp"]:
        return None
    rows = connection.execute(
        """SELECT category, value_mw FROM installed_capacity
           WHERE country_code=? AND timestamp=?""",
        (code, timestamp_row["timestamp"]),
    )
    total = 0.0
    found = False
    for row in rows:
        category = row["category"]
        # Planned assets, energy capacity and solar AC are not added to the
        # operational generation nameplate total. solar_dc is preferred.
        if "planned" in category or category == "battery_storage_capacity" or category == "solar_ac":
            continue
        total += row["value_mw"]
        found = True
    return total if found else None


def aggregate_country(
    connection: sqlite3.Connection, country_code: str, year: int, month: int | None = None
) -> dict[str, Any]:
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError(f"Unsupported pilot country: {country_code}")
    start, end = period_bounds(year, month)
    energy = _energy_by_metric(connection, code, start, end)
    generation_mwh = energy.get("generation_total", 0.0)
    renewable_mwh = sum(energy.get(metric, 0.0) for metric in RENEWABLE_METRICS)
    wind_mwh = energy.get("generation_wind_onshore", 0.0) + energy.get("generation_wind_offshore", 0.0)
    fossil_mwh = sum(
        energy.get(metric, 0.0)
        for metric in ("generation_gas", "generation_coal", "generation_lignite", "generation_oil")
    )
    import_mwh = energy.get("import_total", 0.0)
    export_mwh = energy.get("export_total", 0.0)
    issues = connection.execute(
        """SELECT issue_type, severity, details FROM quality_issue
           WHERE country_code=? AND period_start<? AND period_end>=?
           ORDER BY severity, issue_type""",
        (code, end, start),
    ).fetchall()
    issue_types = {row["issue_type"] for row in issues}
    has_generation = "generation_total" in energy and "missing_expected_series" not in issue_types
    has_consumption = "consumption" in energy and "missing_metric_values" not in issue_types
    has_trade = "import_total" in energy or "export_total" in energy

    result: dict[str, Any] = {
        "country_code": code,
        "country_name": COUNTRIES[code].name,
        "period": f"{year:04d}-{month:02d}" if month else str(year),
        "generation_twh": mwh_to_twh(generation_mwh) if has_generation else None,
        "consumption_twh": mwh_to_twh(energy.get("consumption", 0.0)) if has_consumption else None,
        "renewable_twh": mwh_to_twh(renewable_mwh) if has_generation else None,
        "renewable_share_pct": renewable_share(renewable_mwh, generation_mwh) if has_generation else None,
        "wind_twh": mwh_to_twh(wind_mwh) if has_generation else None,
        "solar_twh": mwh_to_twh(energy.get("generation_solar", 0.0)) if has_generation else None,
        "nuclear_twh": mwh_to_twh(energy.get("generation_nuclear", 0.0)) if has_generation else None,
        "fossil_twh": mwh_to_twh(fossil_mwh) if has_generation else None,
        "import_twh": mwh_to_twh(import_mwh) if has_trade else None,
        "export_twh": mwh_to_twh(export_mwh) if has_trade else None,
        "net_import_twh": mwh_to_twh(net_import_balance(import_mwh, export_mwh)) if has_trade else None,
        "carbon_intensity_gco2eq_kwh": None,
        "installed_capacity_mw": _installed_capacity(connection, code, end),
        "mix": {},
    }
    for metric in GENERATION_METRICS:
        value = energy.get(metric, 0.0)
        result["mix"][metric] = {
            "twh": mwh_to_twh(value) if has_generation else None,
            "pct": (value / generation_mwh * 100.0) if generation_mwh > 0 else None,
        }
    result.update(_price_stats(connection, code, start, end))
    result["quality_issues"] = [dict(row) for row in issues]
    result["data_status"] = "partial" if any(
        row["issue_type"] in {"missing_expected_series", "missing_metric_values", "missing_intervals"}
        for row in issues
    ) else ("complete" if has_generation else "missing")
    return result


def aggregate_all(connection: sqlite3.Connection, year: int, month: int | None = None) -> list[dict[str, Any]]:
    return [aggregate_country(connection, code, year, month) for code in COUNTRIES]
