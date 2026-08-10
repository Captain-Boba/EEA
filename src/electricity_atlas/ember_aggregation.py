from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from .aggregation import period_bounds, renewable_share
from .config import COUNTRIES, EMBER_SOURCE_LABEL, EMBER_SOURCE_NAME


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


def aggregate_ember_country(
    connection: sqlite3.Connection, country_code: str, year: int, month: int | None = None
) -> dict[str, Any]:
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError(f"Unsupported pilot country: {country_code}")
    start, _ = period_bounds(year, month)
    granularity = "monthly" if month is not None else "yearly"
    rows = list(
        connection.execute(
            """SELECT source_series, metric, value, unit
               FROM period_observation
               WHERE source=? AND country_code=? AND granularity=? AND period_start=?""",
            (EMBER_SOURCE_NAME, code, granularity, start),
        )
    )
    values: dict[str, float] = {}
    for row in rows:
        if row["unit"] == "TWh" and row["metric"].startswith("generation_"):
            values[row["metric"]] = values.get(row["metric"], 0.0) + row["value"]

    generation_twh = _sum_present(values, values.keys())
    renewable_twh = _sum_present(values, EMBER_RENEWABLE_METRICS)
    fossil_twh = _sum_present(values, EMBER_FOSSIL_METRICS)
    consumption_row = next((row for row in rows if row["metric"] == "consumption" and row["unit"] == "TWh"), None)
    carbon_row = next(
        (row for row in rows if row["metric"] == "carbon_intensity" and row["unit"] == "gCO2/kWh"),
        None,
    )
    consumption_twh = consumption_row["value"] if consumption_row else None
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
    carbon_intensity = carbon_row["value"] if carbon_row else None
    available_groups = sum(value is not None for value in (generation_twh, consumption_twh, carbon_intensity))

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
        "price_avg_eur_mwh": None,
        "price_median_eur_mwh": None,
        "price_min_eur_mwh": None,
        "price_max_eur_mwh": None,
        "negative_price_intervals": None,
        "negative_price_hours": None,
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
            "price": "von dieser Quelle nicht geliefert",
            "gross_import": "von dieser Quelle nicht geliefert",
            "gross_export": "von dieser Quelle nicht geliefert",
            "net_import": "von dieser Quelle nicht geliefert",
            "installed_capacity": "von dieser Quelle nicht geliefert",
        },
        "data_status": "complete" if available_groups == 3 else ("partial" if available_groups else "missing"),
    }
