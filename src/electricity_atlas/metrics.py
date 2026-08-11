from __future__ import annotations

from typing import Any

from .config import (
    EMBER_PRICE_SOURCE_LABEL,
    EMBER_SOURCE_LABEL,
    EUROSTAT_SOURCE_LABEL,
    JRC_STORAGE_SOURCE_LABEL,
)


def _metric(
    metric_id: str,
    label: str,
    group: str,
    unit: str,
    *,
    monthly: bool,
    yearly: bool,
    snapshot: bool = False,
    table: bool = False,
    map_view: bool = True,
    compare: bool = True,
    source: str = EMBER_SOURCE_LABEL,
    missing: str = "null",
) -> dict[str, Any]:
    views = [view for view, enabled in (("table", table), ("map", map_view), ("compare", compare)) if enabled]
    return {
        "id": metric_id,
        "label_de": label,
        "group": group,
        "unit": unit,
        "views": views,
        "temporal_availability": {"monthly": monthly, "yearly": yearly, "snapshot": snapshot},
        "sortable": True,
        "table": table,
        "map": map_view,
        "compare": compare,
        "source": source,
        "missing_value": missing,
    }


METRICS: tuple[dict[str, Any], ...] = (
    _metric("generation_twh", "Erzeugung", "Stromsystem", "TWh", monthly=True, yearly=True, table=True),
    _metric("consumption_twh", "Verbrauch", "Stromsystem", "TWh", monthly=True, yearly=True, table=True),
    _metric("generation_per_capita_mwh", "Erzeugung pro Kopf", "Stromsystem", "MWh/Einwohner", monthly=False, yearly=True),
    _metric("consumption_per_capita_mwh", "Verbrauch pro Kopf", "Stromsystem", "MWh/Einwohner", monthly=False, yearly=True, table=True, source=f"{EMBER_SOURCE_LABEL}; {EUROSTAT_SOURCE_LABEL}"),
    _metric("renewable_twh", "Erneuerbare gesamt", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("renewable_share_pct", "Erneuerbare", "Erneuerbare", "%", monthly=True, yearly=True, table=True),
    _metric("wind_twh", "Wind", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("wind_share_pct", "Windanteil", "Erneuerbare", "%", monthly=True, yearly=True),
    _metric("solar_twh", "Solar", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("solar_share_pct", "Solaranteil", "Erneuerbare", "%", monthly=True, yearly=True),
    _metric("hydro_twh", "Wasserkraft", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("hydro_share_pct", "Wasserkraftanteil", "Erneuerbare", "%", monthly=True, yearly=True),
    _metric("bioenergy_twh", "Bioenergie", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("bioenergy_share_pct", "Bioenergieanteil", "Erneuerbare", "%", monthly=True, yearly=True),
    _metric("other_renewables_twh", "Sonstige Erneuerbare", "Erneuerbare", "TWh", monthly=True, yearly=True),
    _metric("other_renewables_share_pct", "Anteil sonstige Erneuerbare", "Erneuerbare", "%", monthly=True, yearly=True),
    _metric("fossil_twh", "Fossile gesamt", "Fossile", "TWh", monthly=True, yearly=True),
    _metric("fossil_share_pct", "Fossile", "Fossile", "%", monthly=True, yearly=True, table=True),
    _metric("coal_twh", "Kohle", "Fossile", "TWh", monthly=True, yearly=True),
    _metric("coal_share_pct", "Kohleanteil", "Fossile", "%", monthly=True, yearly=True),
    _metric("gas_twh", "Gas", "Fossile", "TWh", monthly=True, yearly=True),
    _metric("gas_share_pct", "Gasanteil", "Fossile", "%", monthly=True, yearly=True),
    _metric("other_fossil_twh", "Sonstige Fossile", "Fossile", "TWh", monthly=True, yearly=True),
    _metric("other_fossil_share_pct", "Anteil sonstige Fossile", "Fossile", "%", monthly=True, yearly=True),
    _metric("nuclear_twh", "Kernenergie", "Kernenergie", "TWh", monthly=True, yearly=True),
    _metric("nuclear_share_pct", "Kernenergie", "Kernenergie", "%", monthly=True, yearly=True, table=True),
    _metric("net_imports_twh", "Nettoimporte", "Handel", "TWh", monthly=True, yearly=True),
    _metric("net_import_share_pct", "Nettoimportquote", "Handel", "%", monthly=True, yearly=True, table=True),
    _metric("price_avg_eur_mwh", "Großhandelspreis", "Preise", "EUR/MWh", monthly=True, yearly=True, table=True, source=EMBER_PRICE_SOURCE_LABEL),
    _metric("carbon_intensity_gco2eq_kwh", "CO₂-Intensität", "Klima", "gCO₂eq/kWh", monthly=True, yearly=True, table=True),
    _metric("population", "Bevölkerung", "Sozioökonomie", "Einwohner", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL),
    _metric("gdp_current_billion_eur", "BIP", "Sozioökonomie", "Mrd. EUR", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL),
    _metric("gdp_per_capita_pps", "BIP pro Kopf", "Sozioökonomie", "PPS/Einwohner", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL),
    _metric("storage_power_gw", "Speicherleistung", "Kapazitäten und Speicher", "GW", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL),
    _metric("storage_energy_gwh", "Speicherenergie", "Kapazitäten und Speicher", "GWh", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL),
    _metric("storage_duration_hours", "Speicherdauer", "Kapazitäten und Speicher", "h", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL),
)

METRICS_BY_ID = {metric["id"]: metric for metric in METRICS}


def metric_catalog() -> list[dict[str, Any]]:
    return [dict(metric) for metric in METRICS]
