from __future__ import annotations

import calendar
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
    EEA_SOURCE_NAME,
    EV_NOMINAL_BATTERY_KWH_PER_BEV,
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

HOUSEHOLD_PRICE_COMPONENT_METRICS = (
    "household_price_energy_eur_mwh",
    "household_price_network_eur_mwh",
    "household_price_taxes_eur_mwh",
)
EUR_PER_MWH_TO_CENTS_PER_KWH = 0.1

EUROSTAT_DIRECT_METRICS = (
    "capacity_total_gw",
    "capacity_wind_gw",
    "capacity_solar_gw",
    "capacity_hydro_gw",
    "capacity_fossil_gw",
    "capacity_nuclear_gw",
    "household_price_energy_eur_mwh",
    "household_price_network_eur_mwh",
    "household_price_taxes_eur_mwh",
    "nonhousehold_price_energy_eur_mwh",
    "nonhousehold_price_network_eur_mwh",
    "nonhousehold_price_taxes_eur_mwh",
    "gross_imports_twh",
    "gross_exports_twh",
    "bev_stock",
    "bev_new_registrations",
)


def _capacity_factor(generation_twh: float | None, capacity_gw: float | None, year: int) -> float | None:
    if generation_twh is None or capacity_gw is None or capacity_gw <= 0:
        return None
    hours = (366 if calendar.isleap(year) else 365) * 24
    return generation_twh * 1000.0 / (capacity_gw * hours) * 100.0


def _yearly_carbon_intensity(connection: sqlite3.Connection, code: str, year: int) -> float | None:
    row = connection.execute(
        """SELECT value FROM period_observation
           WHERE source=? AND country_code=? AND granularity='yearly'
             AND metric='carbon_intensity' AND unit='gCO2/kWh' AND period_start=?
           ORDER BY source_endpoint LIMIT 1""",
        (EMBER_SOURCE_NAME, code, f"{year:04d}-01-01"),
    ).fetchone()
    return float(row["value"]) if row else None


def _sum_present(values: dict[str, float], metrics: Iterable[str]) -> float | None:
    present = [values[metric] for metric in metrics if metric in values]
    return sum(present) if present else None


def _ratio(numerator: float | None, denominator: float | None, scale: float = 1.0) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * scale


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

    negative_residual_metrics = [
        metric
        for metric in ("generation_other_renewables", "generation_other_fossil")
        if values.get(metric) is not None and values[metric] < 0
    ]
    for metric in negative_residual_metrics:
        values.pop(metric)

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
    nuclear_twh = values.get("generation_nuclear")
    if month is not None and generation_twh is not None and nuclear_twh is None:
        # Product decision: absent monthly nuclear series are interpreted as
        # zero for the low-carbon calculation. Other absent technologies stay null.
        nuclear_twh = 0.0
        component_values["generation_nuclear"] = 0.0
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
    if negative_residual_metrics:
        quality_issues.append(
            {
                "issue_type": "negative_source_residual_treated_as_missing",
                "severity": "warning",
                "details": "Negative Ember residual categories are exposed as missing by product decision.",
            }
        )
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
        supplemental = {
            row["metric"]: row["value"]
            for row in connection.execute(
                f"""SELECT metric,value FROM period_observation
                    WHERE source=? AND country_code=? AND granularity='yearly'
                      AND period_start=? AND metric IN ({','.join('?' for _ in EUROSTAT_DIRECT_METRICS)})""",
                (EUROSTAT_SOURCE_NAME, code, f"{year:04d}-01-01", *EUROSTAT_DIRECT_METRICS),
            )
        }
        eea_row = connection.execute(
            """SELECT value FROM period_observation
               WHERE source=? AND country_code=? AND granularity='yearly'
                 AND period_start=? AND metric='eea_public_electricity_heat_emissions_mtco2eq'
               ORDER BY source_endpoint LIMIT 1""",
            (EEA_SOURCE_NAME, code, f"{year:04d}-01-01"),
        ).fetchone()
        eea_emissions = eea_row["value"] if eea_row else None
    else:
        supplemental = {}
        eea_emissions = None
    def per_capita_mwh(value_twh: float | None) -> float | None:
        return (
            value_twh * 1_000_000 / population
            if value_twh is not None and population and population > 0
            else None
        )

    generation_per_capita = per_capita_mwh(generation_twh)
    consumption_per_capita = per_capita_mwh(consumption_twh)
    renewable_per_capita = per_capita_mwh(renewable_twh)
    net_imports_twh = values.get("net_imports")
    net_import_share = (
        net_imports_twh / consumption_twh * 100.0
        if net_imports_twh is not None and consumption_twh not in (None, 0)
        else None
    )
    low_carbon_share = (
        (renewable_twh + nuclear_twh) / generation_twh * 100.0
        if renewable_twh is not None and nuclear_twh is not None and generation_twh not in (None, 0)
        else None
    )
    self_sufficiency = (
        generation_twh / consumption_twh * 100.0
        if generation_twh is not None and consumption_twh not in (None, 0)
        else None
    )
    estimated_emissions = (
        carbon_intensity * generation_twh / 1000.0
        if carbon_intensity is not None and generation_twh is not None
        else None
    )
    previous_carbon = (
        _yearly_carbon_intensity(connection, code, year - 1)
        if month is None and year < date.today().year
        else None
    )
    decarbonization_rate = (
        (previous_carbon - carbon_intensity) / previous_carbon * 100.0
        if carbon_intensity is not None and previous_carbon not in (None, 0)
        else None
    )
    household_components = [supplemental.get(metric) for metric in HOUSEHOLD_PRICE_COMPONENT_METRICS]
    nonhousehold_components = [
        supplemental.get(metric)
        for metric in (
            "nonhousehold_price_energy_eur_mwh",
            "nonhousehold_price_network_eur_mwh",
            "nonhousehold_price_taxes_eur_mwh",
        )
    ]
    household_price = sum(household_components) if all(value is not None for value in household_components) else None
    nonhousehold_price = sum(nonhousehold_components) if all(value is not None for value in nonhousehold_components) else None
    generation_gdp_intensity = _ratio(generation_twh, gdp_current_billion_eur)
    consumption_gdp_intensity = _ratio(consumption_twh, gdp_current_billion_eur)
    electricity_heat_emissions_gdp = _ratio(eea_emissions, gdp_current_billion_eur, 1000.0)
    household_wholesale_price_gap = (
        (household_price - price["price_avg_eur_mwh"]) * EUR_PER_MWH_TO_CENTS_PER_KWH
        if household_price is not None and price["price_avg_eur_mwh"] is not None
        else None
    )
    gross_imports_twh = supplemental.get("gross_imports_twh")
    gross_exports_twh = supplemental.get("gross_exports_twh")
    electricity_trade_throughput = (
        (gross_imports_twh + gross_exports_twh) / consumption_twh * 100.0
        if gross_imports_twh is not None
        and gross_exports_twh is not None
        and consumption_twh not in (None, 0)
        else None
    )
    ev_battery_capacity = (
        supplemental["bev_stock"] * EV_NOMINAL_BATTERY_KWH_PER_BEV / 1_000_000.0
        if supplemental.get("bev_stock") is not None
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

    public_supplemental = dict(supplemental)
    for metric in HOUSEHOLD_PRICE_COMPONENT_METRICS:
        value = public_supplemental.get(metric)
        if value is not None:
            public_supplemental[metric] = value * EUR_PER_MWH_TO_CENTS_PER_KWH

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
        "renewable_per_capita_mwh": renewable_per_capita,
        "low_carbon_share_pct": low_carbon_share,
        "self_sufficiency_pct": self_sufficiency,
        "renewable_twh": renewable_twh,
        "renewable_share_pct": renewable_share(renewable_twh, generation_twh)
        if renewable_twh is not None and generation_twh is not None
        else None,
        "wind_twh": values.get("generation_wind"),
        "wind_share_pct": mix_value("generation_wind", "pct"),
        "wind_per_capita_mwh": per_capita_mwh(values.get("generation_wind")),
        "solar_twh": values.get("generation_solar"),
        "solar_share_pct": mix_value("generation_solar", "pct"),
        "solar_per_capita_mwh": per_capita_mwh(values.get("generation_solar")),
        "hydro_twh": values.get("generation_hydro"),
        "hydro_share_pct": mix_value("generation_hydro", "pct"),
        "hydro_per_capita_mwh": per_capita_mwh(values.get("generation_hydro")),
        "bioenergy_twh": values.get("generation_biomass"),
        "bioenergy_share_pct": mix_value("generation_biomass", "pct"),
        "bioenergy_per_capita_mwh": per_capita_mwh(values.get("generation_biomass")),
        "other_renewables_twh": values.get("generation_other_renewables"),
        "other_renewables_share_pct": mix_value("generation_other_renewables", "pct"),
        "other_renewables_per_capita_mwh": per_capita_mwh(values.get("generation_other_renewables")),
        "nuclear_twh": nuclear_twh,
        "nuclear_share_pct": mix_value("generation_nuclear", "pct"),
        "nuclear_per_capita_mwh": per_capita_mwh(nuclear_twh),
        "fossil_twh": fossil_twh,
        "fossil_share_pct": renewable_share(fossil_twh, generation_twh)
        if fossil_twh is not None and generation_twh is not None
        else None,
        "fossil_per_capita_mwh": per_capita_mwh(fossil_twh),
        "coal_twh": values.get("generation_coal"),
        "coal_share_pct": mix_value("generation_coal", "pct"),
        "coal_per_capita_mwh": per_capita_mwh(values.get("generation_coal")),
        "gas_twh": values.get("generation_gas"),
        "gas_share_pct": mix_value("generation_gas", "pct"),
        "gas_per_capita_mwh": per_capita_mwh(values.get("generation_gas")),
        "other_fossil_twh": values.get("generation_other_fossil"),
        "other_fossil_share_pct": mix_value("generation_other_fossil", "pct"),
        "other_fossil_per_capita_mwh": per_capita_mwh(values.get("generation_other_fossil")),
        "net_imports_twh": net_imports_twh,
        "net_import_share_pct": net_import_share,
        "price_avg_eur_mwh": price["price_avg_eur_mwh"],
        "price_coverage": price["price_coverage"],
        "price_months_available": price["price_months_available"],
        "price_months_complete": price["price_months_complete"],
        "price_source_label": price["price_source_label"],
        "carbon_intensity_gco2eq_kwh": carbon_intensity,
        "estimated_generation_emissions_mtco2eq": estimated_emissions,
        "decarbonization_rate_pct": decarbonization_rate,
        "eea_public_electricity_heat_emissions_mtco2eq": eea_emissions,
        "population": population,
        "gdp_current_billion_eur": gdp_current_billion_eur,
        "gdp_per_capita_pps": gdp_per_capita_pps,
        "generation_gdp_intensity_kwh_eur": generation_gdp_intensity,
        "consumption_gdp_intensity_kwh_eur": consumption_gdp_intensity,
        "electricity_heat_emissions_gdp_t_million_eur": electricity_heat_emissions_gdp,
        "household_wholesale_price_gap_ct_kwh": household_wholesale_price_gap,
        "electricity_trade_throughput_pct": electricity_trade_throughput,
        **public_supplemental,
        "household_electricity_price_eur_mwh": (
            household_price * EUR_PER_MWH_TO_CENTS_PER_KWH
            if household_price is not None
            else None
        ),
        "nonhousehold_electricity_price_eur_mwh": nonhousehold_price,
        "capacity_factor_wind_pct": _capacity_factor(values.get("generation_wind"), supplemental.get("capacity_wind_gw"), year),
        "capacity_factor_solar_pct": _capacity_factor(values.get("generation_solar"), supplemental.get("capacity_solar_gw"), year),
        "capacity_factor_hydro_pct": _capacity_factor(values.get("generation_hydro"), supplemental.get("capacity_hydro_gw"), year),
        "capacity_factor_fossil_pct": _capacity_factor(fossil_twh, supplemental.get("capacity_fossil_gw"), year),
        "capacity_factor_nuclear_pct": _capacity_factor(nuclear_twh, supplemental.get("capacity_nuclear_gw"), year),
        "ev_battery_nominal_capacity_est_gwh": ev_battery_capacity,
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
