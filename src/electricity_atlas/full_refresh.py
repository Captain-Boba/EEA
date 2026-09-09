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


class ScheduledRefreshCriticalError(RuntimeError):
    """A required scheduled source failed with source-status context."""

    def __init__(self, source_results: dict[str, Any], cause: Exception):
        super().__init__(str(cause))
        self.source_results = source_results


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


def _optional_candidate_source(
    connection: Any,
    source_name: str,
    action: Any,
) -> dict[str, Any]:
    """Run an optional importer without allowing it to degrade a candidate.

    Each scheduled optional source gets a savepoint of its own.  The candidate
    begins as a copy of the published snapshot, so rolling back the savepoint
    deliberately retains its previously published rows.
    """

    savepoint = f"scheduled_{source_name}"
    connection.execute(f"SAVEPOINT {savepoint}")
    try:
        result = action()
        connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        return {"status": "refreshed", "result": _compact_result(result)}
    except Exception as exc:
        connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        return {
            "status": "failed_optional",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def run_scheduled_refresh(
    database_path: Path | str,
    *,
    from_year: int = 2015,
    to_year: int | None = None,
    battery_energy_file: Path | str | None = None,
    battery_power_file: Path | str | None = None,
    report_path: Path | str | None = None,
    community_path: Path | str | None = None,
) -> dict[str, Any]:
    """Refresh the production snapshot under the monthly source policy.

    This deliberately differs from :func:`run_full_refresh`: the latter is the
    strict manual command and remains strict for every source.  The scheduled
    production mode requires the four machine-readable core sources, retains
    controlled Battery-Charts values when local exports are absent, and never
    invokes the browser-bound JRC storage updater.
    """

    last_year = to_year or date.today().year
    energy_file = Path(battery_energy_file).resolve() if battery_energy_file else None
    power_file = Path(battery_power_file).resolve() if battery_power_file else None

    source_results: dict[str, Any] = {
        "ember": {"status": "preserved", "reason": "not attempted after an earlier critical failure"},
        "wholesale_prices": {"status": "preserved", "reason": "not attempted after an earlier critical failure"},
        "eurostat_core": {"status": "preserved", "reason": "not attempted after an earlier critical failure"},
        "eurostat_supplement": {"status": "preserved", "reason": "not attempted after an earlier critical failure"},
        "battery_charts": {"status": "preserved_controlled_input", "reason": "not reached"},
        "jrc_storage": {"status": "preserved", "reason": "not reached"},
        "jrc_hydro": {"status": "preserved", "reason": "not reached"},
        "eea_ghg": {"status": "preserved", "reason": "not reached"},
    }

    def critical(source_name: str, action: Any) -> Any:
        try:
            result = action()
        except Exception as exc:
            source_results[source_name] = {
                "status": "failed_critical",
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            }
            raise ScheduledRefreshCriticalError(source_results, exc) from exc
        source_results[source_name] = {
            "status": "refreshed",
            "result": _compact_result(result) if isinstance(result, dict) else {},
        }
        return result

    def refresh_candidate(candidate: Path) -> dict[str, Any]:
        critical("ember", load_ember_api_key)
        with database(candidate) as connection:
            ember = EmberImporter(connection, refresh=True)
            ember_failures: list[dict[str, Any]] = []
            ember_successes = 0
            for code in EMBER_COUNTRIES:
                country_result = ember.import_range(code, from_year, last_year)
                ember_successes += len(country_result.get("successes", []))
                if country_result.get("errors", 0):
                    ember_failures.append({
                        "country": code,
                        "failures": country_result.get("failures", []),
                    })
            if ember_failures:
                failed_countries = ", ".join(item["country"] for item in ember_failures)
                source_results["ember"] = {
                    "status": "failed_critical",
                    "countries": len(EMBER_COUNTRIES),
                    "error": f"Ember refresh failed for Atlas countries: {failed_countries}",
                }
                raise ScheduledRefreshCriticalError(source_results, RuntimeError(source_results["ember"]["error"]))
            source_results["ember"] = {
                "status": "refreshed",
                "countries": len(EMBER_COUNTRIES),
                "successful_units": ember_successes,
                "from_year": from_year,
                "to_year": last_year,
            }
            critical("wholesale_prices", lambda: WholesalePriceImporter(connection).import_prices())
            critical("eurostat_core", lambda: EurostatImporter(connection).import_years(from_year, last_year))
            critical(
                "eurostat_supplement",
                lambda: EurostatSupplementImporter(connection).import_years(from_year, last_year),
            )

            if energy_file is not None and power_file is not None and energy_file.is_file() and power_file.is_file():
                source_results["battery_charts"] = _optional_candidate_source(
                    connection,
                    "battery_charts",
                    lambda: BatteryChartsImporter(connection).import_files(energy_file, power_file),
                )
            else:
                configured = [str(path) for path in (energy_file, power_file) if path is not None]
                source_results["battery_charts"] = {
                    "status": "preserved_controlled_input",
                    "reason": "Both approved local Battery-Charts JSON files are required",
                    "configured_files": [Path(path).name for path in configured],
                }

            source_results["jrc_storage"] = {
                "status": "preserved",
                "reason": "The scheduled refresh does not run the browser-bound JRC dashboard importer",
            }
            source_results["jrc_hydro"] = _optional_candidate_source(
                connection,
                "jrc_hydro",
                lambda: JrcHydroImporter(connection).import_release(),
            )
            source_results["eea_ghg"] = _optional_candidate_source(
                connection,
                "eea_ghg",
                lambda: EeaGhgImporter(connection).import_url(),
            )
        return source_results

    try:
        return run_refresh_lifecycle(
            database_path,
            refresh_candidate,
            report_path=report_path,
            community_path=community_path,
        )
    except Exception as exc:
        if isinstance(exc, ScheduledRefreshCriticalError):
            raise
        raise ScheduledRefreshCriticalError(source_results, exc) from exc
