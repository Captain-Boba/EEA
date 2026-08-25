from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .config import EMBER_COUNTRIES
from .db import database
from .eea_ghg_importer import EeaGhgImporter
from .ember_client import load_ember_api_key
from .ember_importer import EmberImporter
from .eurostat_importer import EurostatImporter
from .eurostat_supplement import EurostatSupplementImporter
from .hydro_importer import JrcHydroImporter
from .price_importer import WholesalePriceImporter
from .refresh_lifecycle import run_refresh_lifecycle
from .storage_online import BatteryChartsImporter, OnlineStorageUpdater


def _compact_result(result: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in (
        "source",
        "endpoint",
        "rows",
        "rows_replaced",
        "countries",
        "metrics",
        "snapshot_date",
        "network_requests",
        "download_requests",
        "release_date",
    ):
        if key in result:
            compact[key] = result[key]
    return compact or result


def run_full_refresh(
    database_path: Path | str,
    *,
    from_year: int = 2015,
    to_year: int | None = None,
    battery_energy_file: Path | str,
    battery_power_file: Path | str,
    eea_file: Path | str | None = None,
    report_path: Path | str | None = None,
) -> dict[str, Any]:
    last_year = to_year or date.today().year
    energy_file = Path(battery_energy_file).resolve()
    power_file = Path(battery_power_file).resolve()
    reviewed_eea_file = Path(eea_file).resolve() if eea_file is not None else None

    def refresh_candidate(candidate: Path) -> dict[str, Any]:
        load_ember_api_key()
        results: dict[str, Any] = {}
        with database(candidate) as connection:
            ember = EmberImporter(connection, refresh=True)
            ember_failures: list[dict[str, Any]] = []
            ember_successes = 0
            for code in EMBER_COUNTRIES:
                country_result = ember.import_range(code, from_year, last_year)
                ember_successes += len(country_result.get("successes", []))
                if country_result.get("errors", 0):
                    ember_failures.append(
                        {
                            "country": code,
                            "failures": country_result.get("failures", []),
                        }
                    )
            if ember_failures:
                failed_countries = ", ".join(
                    item["country"] for item in ember_failures
                )
                raise RuntimeError(
                    f"Ember refresh failed for Atlas countries: {failed_countries}"
                )
            results["ember"] = {
                "countries": len(EMBER_COUNTRIES),
                "successful_units": ember_successes,
                "from_year": from_year,
                "to_year": last_year,
            }
            results["prices"] = _compact_result(
                WholesalePriceImporter(connection).import_prices()
            )
            results["eurostat_core"] = _compact_result(
                EurostatImporter(connection).import_years(from_year, last_year)
            )
            results["eurostat_supplement"] = _compact_result(
                EurostatSupplementImporter(connection).import_years(
                    from_year, last_year
                )
            )
            results["jrc_hydro"] = _compact_result(
                JrcHydroImporter(connection).import_release()
            )
            eea_importer = EeaGhgImporter(connection)
            results["eea_ghg"] = _compact_result(
                eea_importer.import_file(reviewed_eea_file)
                if reviewed_eea_file is not None
                else eea_importer.import_url()
            )
            results["battery_charts"] = _compact_result(
                BatteryChartsImporter(connection).import_files(
                    energy_file,
                    power_file,
                )
            )
            storage_result = OnlineStorageUpdater(
                connection,
                refresh=True,
            ).update()
            results["jrc_storage"] = _compact_result(storage_result["jrc"])
        return results

    return run_refresh_lifecycle(
        database_path,
        refresh_candidate,
        report_path=report_path,
    )
