from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Country:
    code: str
    name: str


ATLAS_COUNTRIES: dict[str, Country] = {
    "AL": Country("AL", "Albanien"),
    "AT": Country("AT", "Österreich"),
    "BE": Country("BE", "Belgien"),
    "BG": Country("BG", "Bulgarien"),
    "CH": Country("CH", "Schweiz"),
    "CZ": Country("CZ", "Tschechien"),
    "DE": Country("DE", "Deutschland"),
    "DK": Country("DK", "Dänemark"),
    "ES": Country("ES", "Spanien"),
    "EE": Country("EE", "Estland"),
    "FI": Country("FI", "Finnland"),
    "FR": Country("FR", "Frankreich"),
    "UK": Country("UK", "Vereinigtes Königreich"),
    "GR": Country("GR", "Griechenland"),
    "HR": Country("HR", "Kroatien"),
    "HU": Country("HU", "Ungarn"),
    "IE": Country("IE", "Irland"),
    "IT": Country("IT", "Italien"),
    "LT": Country("LT", "Litauen"),
    "LU": Country("LU", "Luxemburg"),
    "LV": Country("LV", "Lettland"),
    "ME": Country("ME", "Montenegro"),
    "MK": Country("MK", "Nordmazedonien"),
    "NL": Country("NL", "Niederlande"),
    "NO": Country("NO", "Norwegen"),
    "PL": Country("PL", "Polen"),
    "PT": Country("PT", "Portugal"),
    "RO": Country("RO", "Rumänien"),
    "RS": Country("RS", "Serbien"),
    "SK": Country("SK", "Slowakei"),
    "SI": Country("SI", "Slowenien"),
    "SE": Country("SE", "Schweden"),
}

EMBER_COUNTRIES = tuple(ATLAS_COUNTRIES)
COUNTRIES = ATLAS_COUNTRIES
ATLAS_MIN_YEAR = 2015

DEFAULT_DB = Path("data/atlas.sqlite3")

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
