from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Country:
    code: str
    name: str


ATLAS_COUNTRIES: dict[str, Country] = {
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

EUROSTAT_SOURCE_NAME = "eurostat"
EUROSTAT_API_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
EUROSTAT_SOURCE_LABEL = "Eurostat"
# Eurostat uses the statistical code EL for Greece, while the Atlas keeps GR.
EUROSTAT_GEO = {code: ("EL" if code == "GR" else code) for code in ATLAS_COUNTRIES}
EUROSTAT_GEO_TO_ATLAS = {geo: code for code, geo in EUROSTAT_GEO.items()}

EUROSTAT_CAPACITY_SOURCE_LABEL = "Eurostat – installierte Nettoleistung"
EUROSTAT_RETAIL_PRICE_SOURCE_LABEL = "Eurostat – Strompreise und Preisbestandteile"
EUROSTAT_BALANCE_SOURCE_LABEL = "Eurostat – Strombilanz"
EUROSTAT_ROAD_SOURCE_LABEL = "Eurostat – Straßenverkehrsbestand und Neuzulassungen"

JRC_SOURCE_NAME = "jrc"
# Historical identifiers retained only for reading/recovery of prior local
# snapshots.  `update-storage` no longer requests this retired projects API.
JRC_STORAGE_ENDPOINT = "european-energy-storage-inventory/manual-export"
JRC_STORAGE_API_ENDPOINT = "european-energy-storage-inventory/api/projects"
JRC_STORAGE_API_URL = "https://ses.jrc.ec.europa.eu/storage-inventory-tool/api/projects"
# Current controlled source: the public dashboard's visible, filtered XLSX
# exports.  No Qlik session URL is persisted.
JRC_STORAGE_DASHBOARD_URL = "https://ses.jrc.ec.europa.eu/storage-inventory"
JRC_STORAGE_DASHBOARD_ENDPOINT = "european-energy-storage-inventory/dashboard-export"
JRC_STORAGE_SOURCE_LABEL = "European Commission JRC – European Energy Storage Inventory"

JRC_HYDRO_ENDPOINT = "jrc-hydro-power-database/release-01"
JRC_HYDRO_URL = (
    "https://raw.githubusercontent.com/energy-modelling-toolkit/"
    "hydro-power-database/master/data/jrc-hydro-power-plant-database.csv"
)
JRC_HYDRO_RELEASE_DATE = "2023-10-25"
JRC_HYDRO_SOURCE_LABEL = "European Commission JRC – Hydro-power database, CC BY 4.0"

EEA_SOURCE_NAME = "eea"
EEA_GHG_ENDPOINT = "national-emissions-reported/2026-v1"
EEA_GHG_URL = "https://sdi.eea.europa.eu/data/83ee8f8c-1422-4e3f-af63-ba88146811e5"
EEA_GHG_SOURCE_LABEL = "European Environment Agency – GHG inventory, CC BY 4.0"

# This is deliberately a transparent, flat fleet assumption rather than an asserted fleet fact.
# It estimates nominal traction-battery energy and must never be described as
# grid-available or bidirectionally accessible V2G storage.
EV_NOMINAL_BATTERY_KWH_PER_BEV = 60.0

BATTERY_CHARTS_SOURCE_NAME = "battery_charts"
BATTERY_CHARTS_API_URL = "https://battery-charts.de/wp-json/isea/v1/data"
BATTERY_CHARTS_ENERGY_ENDPOINT = "bess_monthly_energy"
BATTERY_CHARTS_POWER_ENDPOINT = "bess_monthly_power"
BATTERY_CHARTS_COMBINED_ENDPOINT = "bess_monthly_energy+bess_monthly_power"
BATTERY_CHARTS_SOURCE_LABEL = "Battery-Charts – bereinigter MaStR-Gesamtbestand, CC BY 4.0"

# Albania remains present in Ember's vendor CSV but is intentionally outside
# the Atlas catalog. It is ignored while every other unknown ISO3 code remains
# a hard validation error.
EXCLUDED_VENDOR_ISO3 = frozenset({"ALB"})
