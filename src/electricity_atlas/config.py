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


ATLAS_COUNTRIES: dict[str, Country] = {
    "AL": Country("AL", "Albanien", "Europe/Tirane", (), "ember_only"),
    "AT": Country("AT", "Österreich", "Europe/Vienna", (), "ember_only"),
    "BE": Country("BE", "Belgien", "Europe/Brussels", (), "ember_only"),
    "BG": Country("BG", "Bulgarien", "Europe/Sofia", (), "ember_only"),
    "CH": Country("CH", "Schweiz", "Europe/Zurich", (), "ember_only"),
    "CZ": Country("CZ", "Tschechien", "Europe/Prague", (), "ember_only"),
    "DE": Country("DE", "Deutschland", "Europe/Berlin", ("DE-LU",), "single_zone", "DE-LU umfasst auch Luxemburg."),
    "DK": Country("DK", "Dänemark", "Europe/Copenhagen", ("DK1", "DK2"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "ES": Country("ES", "Spanien", "Europe/Madrid", ("ES",), "single_zone"),
    "EE": Country("EE", "Estland", "Europe/Tallinn", (), "ember_only"),
    "FI": Country("FI", "Finnland", "Europe/Helsinki", (), "ember_only"),
    "FR": Country("FR", "Frankreich", "Europe/Paris", ("FR",), "single_zone"),
    "UK": Country("UK", "Vereinigtes Königreich", "Europe/London", (), "unavailable", "Keine UK-Gebotszone im Energy-Charts-v2-Preisendpoint."),
    "GR": Country("GR", "Griechenland", "Europe/Athens", (), "ember_only"),
    "HR": Country("HR", "Kroatien", "Europe/Zagreb", (), "ember_only"),
    "HU": Country("HU", "Ungarn", "Europe/Budapest", (), "ember_only"),
    "IE": Country("IE", "Irland", "Europe/Dublin", (), "ember_only"),
    "IT": Country("IT", "Italien", "Europe/Rome", ("IT-North", "IT-Centre-North", "IT-Centre-South", "IT-South", "IT-Calabria", "IT-Sicily", "IT-Sardinia"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "LT": Country("LT", "Litauen", "Europe/Vilnius", (), "ember_only"),
    "LU": Country("LU", "Luxemburg", "Europe/Luxembourg", (), "ember_only"),
    "LV": Country("LV", "Lettland", "Europe/Riga", (), "ember_only"),
    "ME": Country("ME", "Montenegro", "Europe/Podgorica", (), "ember_only"),
    "MK": Country("MK", "Nordmazedonien", "Europe/Skopje", (), "ember_only"),
    "NL": Country("NL", "Niederlande", "Europe/Amsterdam", ("NL",), "single_zone"),
    "NO": Country("NO", "Norwegen", "Europe/Oslo", ("NO1", "NO2", "NO3", "NO4", "NO5"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
    "PL": Country("PL", "Polen", "Europe/Warsaw", ("PL",), "single_zone"),
    "PT": Country("PT", "Portugal", "Europe/Lisbon", (), "ember_only"),
    "RO": Country("RO", "Rumänien", "Europe/Bucharest", (), "ember_only"),
    "RS": Country("RS", "Serbien", "Europe/Belgrade", (), "ember_only"),
    "SK": Country("SK", "Slowakei", "Europe/Bratislava", (), "ember_only"),
    "SI": Country("SI", "Slowenien", "Europe/Ljubljana", (), "ember_only"),
    "SE": Country("SE", "Schweden", "Europe/Stockholm", ("SE1", "SE2", "SE3", "SE4"), "unavailable_multi_zone", "Kein belastbarer nationaler Preis ohne Zonen-/Lastgewichte."),
}

# Capability catalogs are deliberately separate: adding Atlas countries must
# never expand the Energy-Charts import target list implicitly.
EMBER_COUNTRIES = tuple(ATLAS_COUNTRIES)
ENERGY_CHARTS_COUNTRIES = ("DE", "FR", "ES", "IT", "PL", "UK", "NO", "SE", "DK", "NL")
COUNTRIES = ATLAS_COUNTRIES
ATLAS_MIN_YEAR = 2015

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

EMBER_API_BASE_URL = "https://api.ember-energy.org/v1"
EMBER_SOURCE_NAME = "ember"
EMBER_SOURCE_LABEL = "Ember, CC BY 4.0"
EMBER_PRICE_SOURCE_LABEL = "Ember Wholesale Electricity Price Data, CC BY 4.0"
EMBER_PRICE_ENDPOINT = "wholesale-electricity-price/monthly-csv"
EMBER_PRICE_CSV_URL = (
    "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/price/outputs/"
    "european_wholesale_electricity_price_data_monthly.csv"
)
EMBER_ISO3: dict[str, str] = {
    "AL": "ALB",
    "AT": "AUT",
    "BE": "BEL",
    "BG": "BGR",
    "CH": "CHE",
    "CZ": "CZE",
    "DE": "DEU",
    "DK": "DNK",
    "ES": "ESP",
    "EE": "EST",
    "FI": "FIN",
    "FR": "FRA",
    "UK": "GBR",
    "GR": "GRC",
    "HR": "HRV",
    "HU": "HUN",
    "IE": "IRL",
    "IT": "ITA",
    "LT": "LTU",
    "LU": "LUX",
    "LV": "LVA",
    "ME": "MNE",
    "MK": "MKD",
    "NL": "NLD",
    "NO": "NOR",
    "PL": "POL",
    "PT": "PRT",
    "RO": "ROU",
    "RS": "SRB",
    "SK": "SVK",
    "SI": "SVN",
    "SE": "SWE",
}
EMBER_ISO3_TO_ATLAS = {iso3: code for code, iso3 in EMBER_ISO3.items()}
