from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .aggregation import aggregate_all
from .community_backup import backup_community_database
from .config import DEFAULT_DB, EMBER_COUNTRIES
from .coverage import coverage_markdown
from .db import database, migrate_atlas_catalog, read_database, reset
from .ember_client import EmberKeyError, load_ember_api_key
from .ember_importer import EmberImporter
from .eurostat_importer import EurostatImporter
from .eurostat_supplement import EurostatSupplementImporter
from .eea_ghg_importer import EeaGhgImporter
from .full_refresh import run_full_refresh
from .hydro_importer import JrcHydroImporter
from .price_importer import WholesalePriceImporter
from .server import serve
from .runtime import resolve_community_db, resolve_server_config
from .storage_importer import JrcStorageImporter
from .storage_online import BatteryChartsImporter, OnlineStorageUpdater


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eea", description="European Electricity Atlas data core")
    parser.add_argument("--db", type=Path, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Download and normalize Ember electricity data")
    import_parser.add_argument("--source", choices=("ember",), default="ember")
    import_parser.add_argument("--year", type=int, help="Single import year; default 2025")
    import_parser.add_argument("--from-year", type=int, help="Ember history start year")
    import_parser.add_argument("--to-year", type=int, help="Ember history end year; default current year")
    import_parser.add_argument("--months", type=int, nargs="*", help="Optional months (1-12); default full year")
    import_parser.add_argument("--countries", nargs="+", help="Atlas country codes; default all 31 countries")
    import_parser.add_argument("--refresh", action="store_true", help="Re-download and reproducibly replace cached periods")

    subparsers.add_parser("import-prices", help="Download and atomically import Ember monthly wholesale prices")
    eurostat_parser = subparsers.add_parser(
        "import-eurostat",
        help="Sequentially import annual Eurostat population and GDP data",
    )
    eurostat_parser.add_argument("--from-year", type=int, default=2015)
    eurostat_parser.add_argument("--to-year", type=int)
    supplement_parser = subparsers.add_parser(
        "import-eurostat-supplement",
        help="Import selected capacity, retail-price, trade and battery-electric car data",
    )
    supplement_parser.add_argument("--from-year", type=int, default=2015)
    supplement_parser.add_argument("--to-year", type=int)
    subparsers.add_parser(
        "import-hydro-inventory",
        help="Import the CC BY 4.0 JRC hydro-power plant inventory",
    )
    eea_parser = subparsers.add_parser(
        "import-eea-ghg",
        help="Import EEA CRT 1.A.1.a public electricity and heat GHG emissions",
    )
    eea_parser.add_argument("--file", type=Path, help="Optional reviewed EEA CSV or ZIP; default official URL")
    storage_parser = subparsers.add_parser(
        "import-storage",
        help="Deprecated offline fallback: import reviewed JRC CSV or paired XLSX exports",
    )
    storage_parser.add_argument("--file", type=Path, help="Reviewed canonical CSV")
    storage_parser.add_argument("--power-file", type=Path, help="JRC Power (GW) XLSX export")
    storage_parser.add_argument("--capacity-file", type=Path, help="JRC Capacity (GWh) XLSX export")
    storage_parser.add_argument("--snapshot-date", help="Dashboard update date in YYYY-MM-DD")
    online_storage_parser = subparsers.add_parser(
        "update-storage",
        help="Conservatively update JRC storage data; Battery-Charts network access is disabled",
    )
    online_storage_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Bypass the monthly cache while retaining request and retry limits",
    )
    battery_storage_parser = subparsers.add_parser(
        "import-battery-storage",
        help="Import manually exported Battery-Charts energy and power JSON files",
    )
    battery_storage_parser.add_argument("--energy-file", type=Path, required=True)
    battery_storage_parser.add_argument("--power-file", type=Path, required=True)
    subparsers.add_parser(
        "migrate-atlas",
        help="Remove Albania, unsupported sources and obsolete interval tables",
    )
    subparsers.add_parser(
        "migrate-ember-only",
        help=argparse.SUPPRESS,
    )

    serve_parser = subparsers.add_parser("serve", help="Run local debug UI")
    serve_parser.add_argument("--host", help="Bind host; overrides EEA_HOST")
    serve_parser.add_argument("--port", help="Bind port; overrides EEA_PORT")
    serve_parser.add_argument("--community-db", type=Path, help="Community SQLite path; overrides EEA_COMMUNITY_DB")
    serve_parser.add_argument("--public-origin", help="Public http(s) origin; overrides EEA_PUBLIC_ORIGIN")
    serve_parser.add_argument("--require-existing-db", action="store_true", help="Refuse to initialize a missing Atlas database")

    backup_parser = subparsers.add_parser("backup-community", help="Atomically back up the community vote database")
    backup_parser.add_argument("--output", type=Path, required=True, help="New SQLite backup file")
    backup_parser.add_argument("--community-db", type=Path, help="Community SQLite source; overrides EEA_COMMUNITY_DB")
    backup_parser.add_argument("--force", action="store_true", help="Replace an existing backup file")

    report_parser = subparsers.add_parser("report", help="Generate coverage, summary and validation reports")
    report_parser.add_argument("--year", type=int, default=2025)
    report_parser.add_argument("--output", type=Path, default=Path("data/reports"))

    refresh_parser = subparsers.add_parser(
        "refresh-all",
        help="Refresh every Atlas source through an isolated, rollback-safe lifecycle",
    )
    refresh_parser.add_argument("--from-year", type=int, default=2015)
    refresh_parser.add_argument("--to-year", type=int)
    refresh_parser.add_argument("--battery-energy-file", type=Path, required=True)
    refresh_parser.add_argument("--battery-power-file", type=Path, required=True)
    refresh_parser.add_argument("--eea-file", type=Path)
    refresh_parser.add_argument(
        "--refresh-report",
        type=Path,
        help="Compact lifecycle report; default data/reports/REFRESH.generated.json",
    )

    subparsers.add_parser("reset-db", help="Delete the local SQLite database")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "serve":
        try:
            runtime = resolve_server_config(
                atlas_db=args.db,
                community_db=args.community_db,
                host=args.host,
                port=args.port,
                public_origin=args.public_origin,
                require_existing_db=args.require_existing_db,
            )
        except ValueError as exc:
            parser.error(str(exc))
        try:
            serve(
                runtime.atlas_db,
                runtime.host,
                runtime.port,
                community_path=runtime.community_db,
                public_origin=runtime.public_origin,
                require_existing_db=runtime.require_existing_db,
            )
        except (OSError, ValueError) as exc:
            print(f"Server start aborted: {exc}", file=sys.stderr)
            return 1
        return 0
    if args.command == "backup-community":
        try:
            backup = backup_community_database(resolve_community_db(args.community_db), args.output, force=args.force)
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(f"Community backup aborted: {exc}", file=sys.stderr)
            return 1
        print(f"Community backup created: {backup}")
        return 0
    args.db = args.db or DEFAULT_DB
    if args.command == "reset-db":
        print("Database deleted." if reset(args.db) else "Database did not exist.")
        return 0
    if args.command == "refresh-all":
        try:
            result = run_full_refresh(
                args.db,
                from_year=args.from_year,
                to_year=args.to_year,
                battery_energy_file=args.battery_energy_file,
                battery_power_file=args.battery_power_file,
                eea_file=args.eea_file,
                report_path=args.refresh_report,
            )
        except Exception as exc:
            print(f"Full refresh aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-prices":
        try:
            with database(args.db) as connection:
                result = WholesalePriceImporter(connection).import_prices()
        except Exception as exc:
            print(f"Price import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-eurostat":
        try:
            with database(args.db) as connection:
                result = EurostatImporter(connection).import_years(args.from_year, args.to_year)
        except Exception as exc:
            print(f"Eurostat import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-eurostat-supplement":
        try:
            with database(args.db) as connection:
                result = EurostatSupplementImporter(connection).import_years(args.from_year, args.to_year)
        except Exception as exc:
            print(f"Eurostat supplement import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-hydro-inventory":
        try:
            with database(args.db) as connection:
                result = JrcHydroImporter(connection).import_release()
        except Exception as exc:
            print(f"JRC hydro import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-eea-ghg":
        try:
            with database(args.db) as connection:
                importer = EeaGhgImporter(connection)
                result = importer.import_file(args.file) if args.file else importer.import_url()
        except Exception as exc:
            print(f"EEA GHG import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "update-storage":
        try:
            with database(args.db) as connection:
                result = OnlineStorageUpdater(connection, refresh=args.refresh).update()
        except Exception as exc:
            print(f"Storage update aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-battery-storage":
        try:
            with database(args.db) as connection:
                result = BatteryChartsImporter(connection).import_files(
                    args.energy_file,
                    args.power_file,
                )
        except Exception as exc:
            print(f"Battery storage import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import-storage":
        try:
            with database(args.db) as connection:
                importer = JrcStorageImporter(connection)
                if args.file and not any((args.power_file, args.capacity_file, args.snapshot_date)):
                    result = importer.import_file(args.file)
                elif (
                    not args.file
                    and args.power_file
                    and args.capacity_file
                    and args.snapshot_date
                ):
                    result = importer.import_exports(
                        args.power_file,
                        args.capacity_file,
                        args.snapshot_date,
                    )
                else:
                    raise ValueError(
                        "Use either --file or all of --power-file, --capacity-file and --snapshot-date"
                    )
        except Exception as exc:
            print(f"JRC storage import aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command in {"migrate-atlas", "migrate-ember-only"}:
        with database(args.db) as connection:
            result = migrate_atlas_catalog(connection)
            connection.execute("VACUUM")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "import":
        if args.from_year is not None:
            if args.year is not None or args.months is not None:
                print("--from-year cannot be combined with --year or --months.", file=sys.stderr)
                return 2
        elif args.to_year is not None:
            print("--to-year requires --from-year.", file=sys.stderr)
            return 2
        try:
            load_ember_api_key()
        except EmberKeyError as exc:
            print(f"Ember import aborted: {exc}", file=sys.stderr)
            return 1
        exit_code = 0
        countries = args.countries or list(EMBER_COUNTRIES)
        with database(args.db) as connection:
            importer = EmberImporter(connection, refresh=args.refresh)
            for code in countries:
                try:
                    if args.from_year is not None:
                        result = importer.import_range(code, args.from_year, args.to_year)
                    else:
                        result = importer.import_country(code, args.year or 2025, args.months)
                except Exception as exc:
                    result = {
                        "errors": 1,
                        "successes": [],
                        "failures": [{"endpoint": "country", "error": str(exc), "preserved_rows": None}],
                    }
                print(f"{code.upper()}: {json.dumps(result, ensure_ascii=False)}")
                if result.get("errors", 0):
                    exit_code = 1
        return exit_code
    if args.command == "report":
        args.output.mkdir(parents=True, exist_ok=True)
        with read_database(args.db) as connection:
            (args.output / "COVERAGE.generated.md").write_text(coverage_markdown(connection, args.year), encoding="utf-8")
            (args.output / "SUMMARY.generated.json").write_text(
                json.dumps(aggregate_all(connection, args.year), ensure_ascii=False, indent=2, allow_nan=False),
                encoding="utf-8",
            )
        print(f"Reports written to {args.output}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
