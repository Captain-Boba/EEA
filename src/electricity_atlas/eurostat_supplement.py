from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from .config import ATLAS_MIN_YEAR, EUROSTAT_SOURCE_NAME
from .eurostat_importer import EurostatClient, EurostatDataset, EurostatImportError, EurostatImporter


def _capacity(metric: str, siec: str) -> EurostatDataset:
    return EurostatDataset(
        "nrg_inf_epc",
        metric,
        "GW",
        {
            "freq": "A",
            "siec": siec,
            "plant_tec": "CAP_NET_ELC",
            "operator": "TOTAL",
            "unit": "MW",
        },
        0.001,
    )


def _price(dataset: str, metric: str, band: str, component: str) -> EurostatDataset:
    return EurostatDataset(
        dataset,
        metric,
        "EUR/MWh",
        {
            "freq": "A",
            "nrg_cons": band,
            "nrg_prc": component,
            "currency": "EUR",
        },
        1000.0,
    )


SUPPLEMENT_DATASETS = (
    _capacity("capacity_total_gw", "TOTAL"),
    _capacity("capacity_wind_gw", "RA300"),
    _capacity("capacity_solar_gw", "RA420"),
    _capacity("capacity_hydro_gw", "RA100"),
    _capacity("capacity_fossil_gw", "CF"),
    _capacity("capacity_nuclear_gw", "N9000"),
    _price("nrg_pc_204_c", "household_price_energy_eur_mwh", "KWH2500-4999", "NRG_SUP"),
    _price("nrg_pc_204_c", "household_price_network_eur_mwh", "KWH2500-4999", "NETC"),
    _price("nrg_pc_204_c", "household_price_taxes_eur_mwh", "KWH2500-4999", "TAX_FEE_LEV_CHRG"),
    _price("nrg_pc_205_c", "nonhousehold_price_energy_eur_mwh", "MWH500-1999", "NRG_SUP"),
    _price("nrg_pc_205_c", "nonhousehold_price_network_eur_mwh", "MWH500-1999", "NETC"),
    _price("nrg_pc_205_c", "nonhousehold_price_taxes_eur_mwh", "MWH500-1999", "TAX_FEE_LEV_CHRG"),
    EurostatDataset("nrg_cb_e", "gross_imports_twh", "TWh", {"freq": "A", "nrg_bal": "IMP", "siec": "E7000", "unit": "GWH"}, 0.001),
    EurostatDataset("nrg_cb_e", "gross_exports_twh", "TWh", {"freq": "A", "nrg_bal": "EXP", "siec": "E7000", "unit": "GWH"}, 0.001),
    EurostatDataset("road_eqs_carpda", "bev_stock", "vehicles", {"freq": "A", "unit": "NR", "mot_nrg": "ELC", "leg_form": "TOTAL"}),
    EurostatDataset("road_eqr_carpda", "bev_new_registrations", "vehicles", {"freq": "A", "unit": "NR", "mot_nrg": "ELC"}),
)

SUPPLEMENT_METRICS = tuple(dataset.metric for dataset in SUPPLEMENT_DATASETS)


class EurostatSupplementImporter:
    """Atomically import the selected capacity, price, trade and BEV series."""

    def __init__(self, connection: sqlite3.Connection, client: EurostatClient | None = None):
        self.connection = connection
        self.client = client or EurostatClient()

    def import_years(self, start_year: int = ATLAS_MIN_YEAR, end_year: int | None = None) -> dict[str, Any]:
        current_year = datetime.now().year
        last_year = current_year if end_year is None else end_year
        if start_year < ATLAS_MIN_YEAR or last_year < start_year or last_year > current_year:
            raise ValueError(f"Eurostat years must be between {ATLAS_MIN_YEAR} and {current_year}")

        downloads = [self.client.fetch(dataset, start_year, last_year) for dataset in SUPPLEMENT_DATASETS]
        normalizer = EurostatImporter(self.connection, self.client)
        normalized: list[tuple[Any, ...]] = []
        for download in downloads:
            rows = normalizer._normalize(download, start_year, last_year)
            filters = ";".join(f"{key}={value}" for key, value in sorted(download.dataset.filters.items()))
            for row in rows:
                values = list(row)
                values[4] = f"eurostat/{download.dataset.code}/{download.dataset.metric}"
                values[5] = filters
                normalized.append(tuple(values))
        if not normalized:
            raise EurostatImportError("Eurostat supplement responses contained no Atlas data")

        placeholders = ",".join("?" for _ in SUPPLEMENT_METRICS)
        parameters = (
            EUROSTAT_SOURCE_NAME,
            f"{start_year:04d}-01-01",
            f"{last_year:04d}-01-01",
            *SUPPLEMENT_METRICS,
        )
        self.connection.execute("SAVEPOINT eurostat_supplement_import")
        try:
            replaced = self.connection.execute(
                f"""SELECT COUNT(*) FROM period_observation
                    WHERE source=? AND granularity='yearly'
                      AND period_start>=? AND period_start<=?
                      AND metric IN ({placeholders})""",
                parameters,
            ).fetchone()[0]
            self.connection.execute(
                f"""DELETE FROM period_observation
                    WHERE source=? AND granularity='yearly'
                      AND period_start>=? AND period_start<=?
                      AND metric IN ({placeholders})""",
                parameters,
            )
            self.connection.executemany(
                """INSERT INTO period_observation
                   (country_code,period_start,period_end,granularity,source,source_endpoint,
                    source_series,metric,value,unit,quality_status)
                   VALUES (?,?,?,'yearly',?,?,?,?,?,?,?)""",
                normalized,
            )
            for download in downloads:
                endpoint = f"{download.dataset.code}:{download.dataset.metric}"
                self.connection.execute(
                    """INSERT INTO source_cache
                       (source,endpoint,request_url,fetched_at,status_code,content_type,etag,last_modified,sha256,payload_text)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(source,endpoint) DO UPDATE SET
                         request_url=excluded.request_url,fetched_at=excluded.fetched_at,
                         status_code=excluded.status_code,content_type=excluded.content_type,
                         etag=excluded.etag,last_modified=excluded.last_modified,
                         sha256=excluded.sha256,payload_text=excluded.payload_text""",
                    (
                        EUROSTAT_SOURCE_NAME,
                        endpoint,
                        download.request_url,
                        download.fetched_at,
                        download.status_code,
                        download.content_type,
                        download.etag,
                        download.last_modified,
                        download.sha256,
                        download.payload_text,
                    ),
                )
            self.connection.execute("RELEASE SAVEPOINT eurostat_supplement_import")
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT eurostat_supplement_import")
            self.connection.execute("RELEASE SAVEPOINT eurostat_supplement_import")
            raise

        return {
            "source": EUROSTAT_SOURCE_NAME,
            "rows": len(normalized),
            "countries_with_values": len({row[0] for row in normalized}),
            "metrics": list(SUPPLEMENT_METRICS),
            "replaced_rows": replaced,
            "period": f"{start_year}..{last_year}",
        }
