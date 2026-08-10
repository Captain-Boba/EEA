from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Iterable

from .aggregation import period_bounds, renewable_share, reporting_period_status, weighted_mean
from .config import (
    COUNTRIES,
    EMBER_PRICE_ENDPOINT,
    EMBER_PRICE_SOURCE_LABEL,
    EMBER_SOURCE_LABEL,
    EMBER_SOURCE_NAME,
)


EMBER_RENEWABLE_METRICS = (
    "generation_solar",
    "generation_wind",
    "generation_hydro",
    "generation_biomass",
    "generation_other_renewables",
)
EMBER_FOSSIL_METRICS = (
    "generation_coal",
    "generation_gas",
    "generation_other_fossil",
)


def _sum_present(values: dict[str, float], metrics: Iterable[str]) -> float | None:
    present = [values[metric] for metric in metrics if metric in values]
    return sum(present) if present else None


def _price_summary(
    connection: sqlite3.Connection,
    code: str,
    year: int,
    month: int | None,
    today: date | None = None,
) -> dict[str, Any]:
    current = today or date.today()
    start, end = period_bounds(year, month)
    rows = list(
        connection.execute(
            """SELECT period_start,period_end,value,quality_status
               FROM period_observation
               WHERE source=? AND source_endpoint=? AND country_code=?
                 AND granularity='monthly' AND metric='day_ahead_price' AND unit='EUR/MWh'
                 AND period_start>=? AND period_start<?
               ORDER BY period_start""",
            (EMBER_SOURCE_NAME, EMBER_PRICE_ENDPOINT, code, start, end),
        )
    )
    if month is not None:
        row = rows[0] if rows else None
        provisional = bool(row and row["quality_status"] == "provisional_current_month")
        return {
            "price_avg_eur_mwh": row["value"] if row else None,
            "price_coverage": "provisional" if provisional else ("complete" if row else "missing"),
            "price_months_available": 1 if row else 0,
            "price_months_complete": 0 if provisional else (1 if row else 0),
            "price_source_label": EMBER_PRICE_SOURCE_LABEL if row else None,
        }

    complete_rows = [row for row in rows if row["quality_status"] != "provisional_current_month"]
    complete_months = {row["period_start"][:7] for row in complete_rows}
    has_full_year = len(complete_months) == 12
    is_current_year = year == current.year
    if has_full_year or (is_current_year and complete_rows):
        price = weighted_mean(
            (
                row["value"],
                (date.fromisoformat(row["period_end"]) - date.fromisoformat(row["period_start"])).days + 1,
            )
            for row in complete_rows
        )
        coverage = "complete" if has_full_year else "ytd"
    else:
        price = None
        coverage = "incomplete" if rows else "missing"
    return {
        "price_avg_eur_mwh": price,
        "price_coverage": coverage,
        "price_months_available": len({row["period_start"][:7] for row in rows}),
        "price_months_complete": len(complete_months),
        "price_source_label": EMBER_PRICE_SOURCE_LABEL if rows else None,
    }


def aggregate_ember_country(
    connection: sqlite3.Connection, country_code: str, year: int, month: int | None = None
) -> dict[str, Any]:
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError(f"Unsupported pilot country: {country_code}")
    start, end = period_bounds(year, month)
    is_current_ytd = month is None and year == date.today().year
    if is_current_ytd:
        rows = list(
            connection.execute(
                """SELECT period_start,period_end,source_series,metric,value,unit
                   FROM period_observation
                   WHERE source=? AND country_code=? AND granularity='monthly'
                     AND period_start>=? AND period_start<?""",
                (EMBER_SOURCE_NAME, code, start, end),
            )
        )
    else:
        granularity = "monthly" if month is not None else "yearly"
        rows = list(
            connection.execute(
                """SELECT period_start,period_end,source_series,metric,value,unit
                   FROM period_observation
                   WHERE source=? AND country_code=? AND granularity=? AND period_start=?""",
                (EMBER_SOURCE_NAME, code, granularity, start),
            )
        )
    values: dict[str, float] = {}
    monthly_generation: dict[str, float] = {}
    for row in rows:
        if row["unit"] == "TWh" and row["metric"].startswith("generation_"):
            values[row["metric"]] = values.get(row["metric"], 0.0) + row["value"]
            monthly_generation[row["period_start"]] = (
                monthly_generation.get(row["period_start"], 0.0) + row["value"]
            )

    generation_twh = _sum_present(values, values.keys())
    renewable_twh = _sum_present(values, EMBER_RENEWABLE_METRICS)
    fossil_twh = _sum_present(values, EMBER_FOSSIL_METRICS)
    consumption_rows = [
        row for row in rows if row["metric"] == "consumption" and row["unit"] == "TWh"
    ]
    carbon_rows = [
        row
        for row in rows
        if row["metric"] == "carbon_intensity" and row["unit"] == "gCO2/kWh"
    ]
    consumption_twh = (
        sum(row["value"] for row in consumption_rows)
        if is_current_ytd and consumption_rows
        else (consumption_rows[0]["value"] if consumption_rows else None)
    )
    quality_issues: list[dict[str, str]] = []
    if month is None and consumption_twh is None:
        monthly_demand = list(
            connection.execute(
                """SELECT period_start, value FROM period_observation
                   WHERE source=? AND country_code=? AND granularity='monthly'
                     AND metric='consumption' AND unit='TWh'
                     AND period_start>=? AND period_start<?
                   ORDER BY period_start""",
                (EMBER_SOURCE_NAME, code, f"{year:04d}-01-01", f"{year + 1:04d}-01-01"),
            )
        )
        if len({row["period_start"][:7] for row in monthly_demand}) == 12:
            consumption_twh = sum(row["value"] for row in monthly_demand)
            quality_issues.append(
                {
                    "issue_type": "yearly_demand_derived_from_monthly",
                    "severity": "warning",
                    "details": "Ember yearly demand was unavailable; summed from 12 monthly Ember values.",
                }
            )
    if is_current_ytd and carbon_rows:
        carbon_intensity = weighted_mean(
            (
                row["value"],
                monthly_generation.get(
                    row["period_start"],
                    (date.fromisoformat(row["period_end"]) - date.fromisoformat(row["period_start"])).days + 1,
                ),
            )
            for row in carbon_rows
        )
    else:
        carbon_intensity = carbon_rows[0]["value"] if carbon_rows else None
    if is_current_ytd and rows:
        quality_issues.append(
            {
                "issue_type": "current_year_derived_from_monthly",
                "severity": "warning",
                "details": "Current Ember year is aggregated from available monthly values and is YTD.",
            }
        )
    price = _price_summary(connection, code, year, month)
    available_groups = sum(value is not None for value in (generation_twh, consumption_twh, carbon_intensity))
    any_data = available_groups or price["price_months_available"]
    if price["price_coverage"] == "incomplete":
        quality_issues.append(
            {
                "issue_type": "incomplete_wholesale_price_year",
                "severity": "warning",
                "details": "Historical Ember price year has fewer than 12 completed monthly values.",
            }
        )

    mix = {
        metric: {
            "twh": value,
            "pct": value / generation_twh * 100.0 if generation_twh and value is not None else None,
        }
        for metric, value in values.items()
    }
    return {
        "country_code": code,
        "country_name": COUNTRIES[code].name,
        "period": f"{year:04d}-{month:02d}" if month else str(year),
        "period_status": reporting_period_status(year, month),
        "source": EMBER_SOURCE_NAME,
        "source_label": EMBER_SOURCE_LABEL,
        "generation_twh": generation_twh,
        "consumption_twh": consumption_twh,
        "renewable_twh": renewable_twh,
        "renewable_share_pct": renewable_share(renewable_twh, generation_twh)
        if renewable_twh is not None and generation_twh is not None
        else None,
        "wind_twh": values.get("generation_wind"),
        "solar_twh": values.get("generation_solar"),
        "nuclear_twh": values.get("generation_nuclear"),
        "fossil_twh": fossil_twh,
        "price_avg_eur_mwh": price["price_avg_eur_mwh"],
        "price_median_eur_mwh": None,
        "price_min_eur_mwh": None,
        "price_max_eur_mwh": None,
        "negative_price_intervals": None,
        "negative_price_hours": None,
        "price_coverage": price["price_coverage"],
        "price_months_available": price["price_months_available"],
        "price_months_complete": price["price_months_complete"],
        "price_source_label": price["price_source_label"],
        "import_twh": None,
        "export_twh": None,
        "net_import_twh": None,
        "carbon_intensity_gco2eq_kwh": carbon_intensity,
        "installed_capacity_mw": None,
        "installed_capacity_snapshot": None,
        "installed_capacity_snapshot_year": None,
        "installed_capacity_age_years": None,
        "installed_capacity_status": "not_provided",
        "mix": mix,
        "quality_issues": quality_issues,
        "source_unavailable": {
            "gross_import": "von dieser Quelle nicht geliefert",
            "gross_export": "von dieser Quelle nicht geliefert",
            "net_import": "von dieser Quelle nicht geliefert",
            "installed_capacity": "von dieser Quelle nicht geliefert",
        },
        "data_status": (
            "complete"
            if available_groups == 3
            and price["price_coverage"] == "complete"
            and reporting_period_status(year, month) == "closed"
            else ("partial" if any_data else "missing")
        ),
    }
