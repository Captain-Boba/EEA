from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    timezone: str
    price_zones: tuple[str, ...]
    price_strategy: str
    notes: str = ""


COUNTRIES: dict[str, Country] = {
    "DE": Country("DE", "Deutschland", "Europe/Berlin", ("DE-LU",), "single_zone", "DE-LU umfasst auch Luxemburg."),
    "FR": Country("FR", "Frankreich", "Europe/Paris", ("FR",), "single_zone"),
    "ES": Country("ES", "Spanien", "Europe/Madrid", ("ES",), "single_zone"),
    "IT": Country("IT", "Italien", "Europe/Rome", ("IT-North", "IT-Centre-North", "IT-Centre-South", "IT-South", "IT-Calabria", "IT-Sicily", "IT-Sardinia"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "PL": Country("PL", "Polen", "Europe/Warsaw", ("PL",), "single_zone"),
    "UK": Country("UK", "Vereinigtes Königreich", "Europe/London", (), "unavailable", "Keine UK-Gebotszone im Energy-Charts-v2-Preisendpoint."),
    "NO": Country("NO", "Norwegen", "Europe/Oslo", ("NO1", "NO2", "NO3", "NO4", "NO5"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "SE": Country("SE", "Schweden", "Europe/Stockholm", ("SE1", "SE2", "SE3", "SE4"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "DK": Country("DK", "Dänemark", "Europe/Copenhagen", ("DK1", "DK2"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "NL": Country("NL", "Niederlande", "Europe/Amsterdam", ("NL",), "single_zone"),
}

RENEWABLE_METRICS = frozenset(
    {
        "generation_solar",
        "generation_wind_onshore",
        "generation_wind_offshore",
        "generation_hydro",
        "generation_biomass",
    }
)

GENERATION_METRICS = (
    "generation_solar",
    "generation_wind_onshore",
    "generation_wind_offshore",
    "generation_hydro",
    "generation_biomass",
    "generation_nuclear",
    "generation_gas",
    "generation_coal",
    "generation_lignite",
    "generation_oil",
    "generation_other",
)

# Minimum series that must be present for a country to be called comparable.
# Absence of a technology is only suspicious where that technology is known to
# be material for the national system; zero-capacity technologies are omitted.
EXPECTED_PUBLIC_POWER_SERIES: dict[str, frozenset[str]] = {
    "DE": frozenset({"solar", "wind_onshore", "wind_offshore", "hydro_run_of_river", "biomass", "fossil_gas", "fossil_hard_coal", "fossil_brown_coal_lignite", "load"}),
    "FR": frozenset({"nuclear", "solar", "wind_onshore", "wind_offshore", "hydro_run_of_river", "fossil_gas", "load"}),
    "ES": frozenset({"nuclear", "solar", "wind_onshore", "hydro_run_of_river", "fossil_gas", "load"}),
    "IT": frozenset({"solar", "wind_onshore", "hydro_run_of_river", "fossil_gas", "load"}),
    "PL": frozenset({"solar", "wind_onshore", "biomass", "fossil_gas", "fossil_hard_coal", "fossil_brown_coal_lignite", "load"}),
    "UK": frozenset({"nuclear", "solar", "wind_onshore", "wind_offshore", "fossil_gas", "load"}),
    "NO": frozenset({"hydro_run_of_river", "hydro_water_reservoir", "wind_onshore", "load"}),
    "SE": frozenset({"nuclear", "hydro_water_reservoir", "wind_onshore", "load"}),
    "DK": frozenset({"solar", "wind_onshore", "wind_offshore", "biomass", "fossil_gas", "load"}),
    "NL": frozenset({"nuclear", "solar", "wind_onshore", "wind_offshore", "fossil_gas", "load"}),
}

DEFAULT_DB = Path("data/atlas.sqlite3")
API_BASE_URL = "https://api.energy-charts.info/v2"
SOURCE_NAME = "energy-charts.info"
INSTALLED_CAPACITY_MAX_AGE_YEARS = 2
