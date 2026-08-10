from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .aggregation import aggregate_all
from .config import DEFAULT_DB, EMBER_COUNTRIES
from .coverage import coverage_markdown
from .db import database, migrate_to_ember_only, read_database, reset
from .ember_client import EmberKeyError, load_ember_api_key
from .ember_importer import EmberImporter
from .price_importer import WholesalePriceImporter
from .server import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eea", description="European Electricity Atlas data core")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Download and normalize Ember electricity data")
    import_parser.add_argument("--source", choices=("ember",), default="ember")
    import_parser.add_argument("--year", type=int, help="Single import year; default 2025")
    import_parser.add_argument("--from-year", type=int, help="Ember history start year")
    import_parser.add_argument("--to-year", type=int, help="Ember history end year; default current year")
    import_parser.add_argument("--months", type=int, nargs="*", help="Optional months (1-12); default full year")
    import_parser.add_argument("--countries", nargs="+", help="Atlas country codes; default all 32 countries")
    import_parser.add_argument("--refresh", action="store_true", help="Re-download and reproducibly replace cached periods")

    subparsers.add_parser("import-prices", help="Download and atomically import Ember monthly wholesale prices")
    subparsers.add_parser(
        "migrate-ember-only",
        help="Remove non-Ember rows, caches and obsolete interval tables",
    )

    serve_parser = subparsers.add_parser("serve", help="Run local debug UI")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    report_parser = subparsers.add_parser("report", help="Generate coverage, summary and validation reports")
    report_parser.add_argument("--year", type=int, default=2025)
    report_parser.add_argument("--output", type=Path, default=Path("data/reports"))

    subparsers.add_parser("reset-db", help="Delete the local SQLite database")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "reset-db":
        print("Database deleted." if reset(args.db) else "Database did not exist.")
        return 0
    if args.command == "serve":
        serve(args.db, args.host, args.port)
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
    if args.command == "migrate-ember-only":
        with database(args.db) as connection:
            result = migrate_to_ember_only(connection)
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
