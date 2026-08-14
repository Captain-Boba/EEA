from __future__ import annotations

from typing import Any

from .config import (
    BATTERY_CHARTS_SOURCE_LABEL,
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
    family: str | None = None,
    representation: str | None = None,
    map_scale: str = "sequential",
    map_palette: str = "generation",
    map_domain: tuple[float, float] | None = None,
    map_midpoint: float | None = None,
    map_decimals: int = 2,
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
        "family": family or label,
        "representation": representation or label,
        "map_config": {
            "scale": map_scale,
            "palette": map_palette,
            "domain": list(map_domain) if map_domain else None,
            "midpoint": map_midpoint,
            "decimals": map_decimals,
        },
    }


METRICS: tuple[dict[str, Any], ...] = (
    _metric("generation_twh", "Erzeugung", "Stromsystem", "TWh", monthly=True, yearly=True, table=True, family="Erzeugung", representation="Erzeugung in TWh"),
    _metric("consumption_twh", "Verbrauch", "Stromsystem", "TWh", monthly=True, yearly=True, table=True, family="Verbrauch", representation="Verbrauch in TWh", map_palette="consumption"),
    _metric("generation_per_capita_mwh", "Erzeugung pro Kopf", "Stromsystem", "MWh/Einwohner", monthly=False, yearly=True, family="Erzeugung", representation="Erzeugung in MWh je Einwohner"),
    _metric("consumption_per_capita_mwh", "Verbrauch pro Kopf", "Stromsystem", "MWh/Einwohner", monthly=False, yearly=True, table=True, source=f"{EMBER_SOURCE_LABEL}; {EUROSTAT_SOURCE_LABEL}", family="Verbrauch", representation="Verbrauch in MWh je Einwohner", map_palette="consumption"),
    _metric("renewable_twh", "Erneuerbare gesamt", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Erneuerbare gesamt", representation="Erzeugung in TWh", map_palette="renewables"),
    _metric("renewable_share_pct", "Erneuerbare", "Erneuerbare", "%", monthly=True, yearly=True, table=True, family="Erneuerbare gesamt", representation="Anteil an der Gesamterzeugung", map_palette="renewables", map_decimals=1),
    _metric("wind_twh", "Wind", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Wind", representation="Erzeugung in TWh", map_palette="wind"),
    _metric("wind_share_pct", "Windanteil", "Erneuerbare", "%", monthly=True, yearly=True, family="Wind", representation="Anteil an der Gesamterzeugung", map_palette="wind", map_decimals=1),
    _metric("solar_twh", "Solar", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Solar", representation="Erzeugung in TWh", map_palette="solar"),
    _metric("solar_share_pct", "Solaranteil", "Erneuerbare", "%", monthly=True, yearly=True, family="Solar", representation="Anteil an der Gesamterzeugung", map_palette="solar", map_decimals=1),
    _metric("hydro_twh", "Wasserkraft", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Wasserkraft", representation="Erzeugung in TWh", map_palette="hydro"),
    _metric("hydro_share_pct", "Wasserkraftanteil", "Erneuerbare", "%", monthly=True, yearly=True, family="Wasserkraft", representation="Anteil an der Gesamterzeugung", map_palette="hydro", map_decimals=1),
    _metric("bioenergy_twh", "Bioenergie", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Bioenergie", representation="Erzeugung in TWh", map_palette="bioenergy"),
    _metric("bioenergy_share_pct", "Bioenergieanteil", "Erneuerbare", "%", monthly=True, yearly=True, family="Bioenergie", representation="Anteil an der Gesamterzeugung", map_palette="bioenergy", map_decimals=1),
    _metric("other_renewables_twh", "Sonstige Erneuerbare", "Erneuerbare", "TWh", monthly=True, yearly=True, family="Sonstige Erneuerbare", representation="Erzeugung in TWh", map_palette="other-renewables"),
    _metric("other_renewables_share_pct", "Anteil sonstige Erneuerbare", "Erneuerbare", "%", monthly=True, yearly=True, family="Sonstige Erneuerbare", representation="Anteil an der Gesamterzeugung", map_palette="other-renewables", map_decimals=1),
    _metric("fossil_twh", "Fossile gesamt", "Fossile", "TWh", monthly=True, yearly=True, family="Fossile gesamt", representation="Erzeugung in TWh", map_palette="fossil"),
    _metric("fossil_share_pct", "Fossile", "Fossile", "%", monthly=True, yearly=True, table=True, family="Fossile gesamt", representation="Anteil an der Gesamterzeugung", map_palette="fossil", map_decimals=1),
    _metric("coal_twh", "Kohle", "Fossile", "TWh", monthly=True, yearly=True, family="Kohle", representation="Erzeugung in TWh", map_palette="coal"),
    _metric("coal_share_pct", "Kohleanteil", "Fossile", "%", monthly=True, yearly=True, family="Kohle", representation="Anteil an der Gesamterzeugung", map_palette="coal", map_decimals=1),
    _metric("gas_twh", "Gas", "Fossile", "TWh", monthly=True, yearly=True, family="Gas", representation="Erzeugung in TWh", map_palette="gas"),
    _metric("gas_share_pct", "Gasanteil", "Fossile", "%", monthly=True, yearly=True, family="Gas", representation="Anteil an der Gesamterzeugung", map_palette="gas", map_decimals=1),
    _metric("other_fossil_twh", "Sonstige Fossile", "Fossile", "TWh", monthly=True, yearly=True, family="Sonstige Fossile", representation="Erzeugung in TWh", map_palette="other-fossil"),
    _metric("other_fossil_share_pct", "Anteil sonstige Fossile", "Fossile", "%", monthly=True, yearly=True, family="Sonstige Fossile", representation="Anteil an der Gesamterzeugung", map_palette="other-fossil", map_decimals=1),
    _metric("nuclear_twh", "Kernenergie", "Kernenergie", "TWh", monthly=True, yearly=True, family="Kernenergie", representation="Erzeugung in TWh", map_palette="nuclear"),
    _metric("nuclear_share_pct", "Kernenergie", "Kernenergie", "%", monthly=True, yearly=True, table=True, family="Kernenergie", representation="Anteil an der Gesamterzeugung", map_palette="nuclear", map_decimals=1),
    _metric("net_imports_twh", "Nettoimporte", "Handel", "TWh", monthly=True, yearly=True, family="Nettoimporte", representation="Nettoimporte in TWh", map_scale="diverging", map_palette="trade", map_midpoint=0),
    _metric("net_import_share_pct", "Nettoimportquote", "Handel", "%", monthly=True, yearly=True, table=True, family="Nettoimporte", representation="Anteil am Verbrauch", map_scale="diverging", map_palette="trade", map_midpoint=0, map_decimals=1),
    _metric("price_avg_eur_mwh", "Großhandelspreis", "Preise", "EUR/MWh", monthly=True, yearly=True, table=True, source=EMBER_PRICE_SOURCE_LABEL, family="Großhandelspreis", representation="Durchschnittspreis", map_palette="price"),
    _metric("carbon_intensity_gco2eq_kwh", "CO₂-Intensität", "Klima", "gCO₂eq/kWh", monthly=True, yearly=True, table=True, family="CO₂-Intensität", representation="CO₂-Intensität", map_palette="carbon", map_decimals=0),
    _metric("population", "Bevölkerung", "Sozioökonomie", "Einwohner", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL, family="Bevölkerung", representation="Einwohner", map_palette="population", map_decimals=0),
    _metric("gdp_current_billion_eur", "BIP", "Sozioökonomie", "Mrd. EUR", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL, family="BIP", representation="BIP zu laufenden Preisen", map_palette="gdp"),
    _metric("gdp_per_capita_pps", "BIP pro Kopf", "Sozioökonomie", "PPS/Einwohner", monthly=False, yearly=True, source=EUROSTAT_SOURCE_LABEL, family="BIP pro Kopf", representation="Kaufkraftstandard je Einwohner", map_palette="gdp-per-capita", map_decimals=0),
    _metric("battery_power_gw", "Batterie-Entladeleistung", "Kapazitäten und Speicher", "GW", monthly=False, yearly=False, snapshot=True, source=f"{BATTERY_CHARTS_SOURCE_LABEL}; {JRC_STORAGE_SOURCE_LABEL}", family="Batteriespeicher", representation="Entladeleistung in GW", map_palette="battery"),
    _metric("battery_energy_gwh", "Batterie-Speicherenergie", "Kapazitäten und Speicher", "GWh", monthly=False, yearly=False, snapshot=True, source=f"{BATTERY_CHARTS_SOURCE_LABEL}; {JRC_STORAGE_SOURCE_LABEL}", family="Batteriespeicher", representation="Speicherenergie in GWh", map_palette="battery"),
    _metric("battery_duration_hours", "Batterie-Entladedauer", "Kapazitäten und Speicher", "h", monthly=False, yearly=False, snapshot=True, source=f"{BATTERY_CHARTS_SOURCE_LABEL}; {JRC_STORAGE_SOURCE_LABEL}", family="Batteriespeicher", representation="Äquivalente Entladedauer in Stunden", map_palette="battery"),
    _metric("pumped_storage_power_gw", "Pumpspeicher-Entladeleistung", "Kapazitäten und Speicher", "GW", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL, family="Pumpspeicher", representation="Entladeleistung in GW", map_palette="pumped-storage"),
    _metric("pumped_storage_energy_gwh", "Pumpspeicher-Speicherenergie", "Kapazitäten und Speicher", "GWh", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL, family="Pumpspeicher", representation="Speicherenergie in GWh", map_palette="pumped-storage"),
    _metric("pumped_storage_duration_hours", "Pumpspeicher-Entladedauer", "Kapazitäten und Speicher", "h", monthly=False, yearly=False, snapshot=True, source=JRC_STORAGE_SOURCE_LABEL, family="Pumpspeicher", representation="Äquivalente Entladedauer in Stunden", map_palette="pumped-storage"),
)

METRICS_BY_ID = {metric["id"]: metric for metric in METRICS}


def metric_catalog() -> list[dict[str, Any]]:
    return [dict(metric) for metric in METRICS]
