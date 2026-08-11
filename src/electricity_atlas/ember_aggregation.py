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
    EUROSTAT_SOURCE_NAME,
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
    monthly_component_generation: dict[str, float] = {}
    for row in rows:
        if row["unit"] == "TWh" and (
            row["metric"].startswith("generation_")
            or row["metric"] in {"demand_total", "net_imports"}
        ):
            values[row["metric"]] = values.get(row["metric"], 0.0) + row["value"]
            if row["metric"] == "generation_total":
                monthly_generation[row["period_start"]] = row["value"]
            elif (
                row["metric"] in EMBER_RENEWABLE_METRICS
                or row["metric"] in EMBER_FOSSIL_METRICS
                or row["metric"] == "generation_nuclear"
            ):
                monthly_component_generation[row["period_start"]] = (
                    monthly_component_generation.get(row["period_start"], 0.0) + row["value"]
                )

    for period_start, value in monthly_component_generation.items():
        monthly_generation.setdefault(period_start, value)

    component_values = {
        metric: value
        for metric, value in values.items()
        if metric in EMBER_RENEWABLE_METRICS or metric in EMBER_FOSSIL_METRICS or metric == "generation_nuclear"
    }
    generation_twh = values.get("generation_total")
    if generation_twh is None:
        generation_twh = _sum_present(component_values, component_values.keys())
    renewable_twh = values.get("generation_renewables")
    if renewable_twh is None:
        renewable_twh = _sum_present(component_values, EMBER_RENEWABLE_METRICS)
    fossil_twh = values.get("generation_fossil")
    if fossil_twh is None:
        fossil_twh = _sum_present(component_values, EMBER_FOSSIL_METRICS)
    consumption_rows = [
        row for row in rows if row["metric"] == "consumption" and row["unit"] == "TWh"
    ]
    carbon_rows = [
        row
        for row in rows
        if row["metric"] == "carbon_intensity" and row["unit"] == "gCO2/kWh"
    ]
    consumption_twh = values.get("demand_total")
    fallback_consumption = (
        sum(row["value"] for row in consumption_rows)
        if is_current_ytd and consumption_rows
        else (consumption_rows[0]["value"] if consumption_rows else None)
    )
    if consumption_twh is None:
        consumption_twh = fallback_consumption
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
    population = None
    gdp_current_billion_eur = None
    gdp_per_capita_pps = None
    if month is None:
        socioeconomic = {
            row["metric"]: row["value"]
            for row in connection.execute(
                """SELECT metric,value FROM period_observation
                   WHERE source=? AND country_code=? AND granularity='yearly'
                     AND period_start=? AND metric IN ('population','gdp_current_billion_eur','gdp_per_capita_pps')""",
                (EUROSTAT_SOURCE_NAME, code, f"{year:04d}-01-01"),
            )
        }
        population = socioeconomic.get("population")
        gdp_current_billion_eur = socioeconomic.get("gdp_current_billion_eur")
        gdp_per_capita_pps = socioeconomic.get("gdp_per_capita_pps")
    generation_per_capita = (
        generation_twh * 1_000_000 / population
        if generation_twh is not None and population and population > 0
        else None
    )
    consumption_per_capita = (
        consumption_twh * 1_000_000 / population
        if consumption_twh is not None and population and population > 0
        else None
    )
    net_imports_twh = values.get("net_imports")
    net_import_share = (
        net_imports_twh / consumption_twh * 100.0
        if net_imports_twh is not None and consumption_twh not in (None, 0)
        else None
    )
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
        for metric, value in component_values.items()
    }
    def mix_value(metric: str, part: str) -> float | None:
        return mix.get(metric, {}).get(part)

    return {
        "country_code": code,
        "country_name": COUNTRIES[code].name,
        "period": f"{year:04d}-{month:02d}" if month else str(year),
        "period_status": reporting_period_status(year, month),
        "source": EMBER_SOURCE_NAME,
        "source_label": EMBER_SOURCE_LABEL,
        "generation_twh": generation_twh,
        "consumption_twh": consumption_twh,
        "generation_per_capita_mwh": generation_per_capita,
        "consumption_per_capita_mwh": consumption_per_capita,
        "renewable_twh": renewable_twh,
        "renewable_share_pct": renewable_share(renewable_twh, generation_twh)
        if renewable_twh is not None and generation_twh is not None
        else None,
        "wind_twh": values.get("generation_wind"),
        "wind_share_pct": mix_value("generation_wind", "pct"),
        "solar_twh": values.get("generation_solar"),
        "solar_share_pct": mix_value("generation_solar", "pct"),
        "hydro_twh": values.get("generation_hydro"),
        "hydro_share_pct": mix_value("generation_hydro", "pct"),
        "bioenergy_twh": values.get("generation_biomass"),
        "bioenergy_share_pct": mix_value("generation_biomass", "pct"),
        "other_renewables_twh": values.get("generation_other_renewables"),
        "other_renewables_share_pct": mix_value("generation_other_renewables", "pct"),
        "nuclear_twh": values.get("generation_nuclear"),
        "nuclear_share_pct": mix_value("generation_nuclear", "pct"),
        "fossil_twh": fossil_twh,
        "fossil_share_pct": renewable_share(fossil_twh, generation_twh)
        if fossil_twh is not None and generation_twh is not None
        else None,
        "coal_twh": values.get("generation_coal"),
        "coal_share_pct": mix_value("generation_coal", "pct"),
        "gas_twh": values.get("generation_gas"),
        "gas_share_pct": mix_value("generation_gas", "pct"),
        "other_fossil_twh": values.get("generation_other_fossil"),
        "other_fossil_share_pct": mix_value("generation_other_fossil", "pct"),
        "net_imports_twh": net_imports_twh,
        "net_import_share_pct": net_import_share,
        "price_avg_eur_mwh": price["price_avg_eur_mwh"],
        "price_coverage": price["price_coverage"],
        "price_months_available": price["price_months_available"],
        "price_months_complete": price["price_months_complete"],
        "price_source_label": price["price_source_label"],
        "carbon_intensity_gco2eq_kwh": carbon_intensity,
        "population": population,
        "gdp_current_billion_eur": gdp_current_billion_eur,
        "gdp_per_capita_pps": gdp_per_capita_pps,
        "mix": mix,
        "quality_issues": quality_issues,
        "data_status": (
            "complete"
            if available_groups == 3
            and price["price_coverage"] == "complete"
            and reporting_period_status(year, month) == "closed"
            else ("partial" if any_data else "missing")
        ),
    }
