from __future__ import annotations

import argparse
import json
from pathlib import Path

from .aggregation import aggregate_all
from .config import COUNTRIES, DEFAULT_DB
from .coverage import coverage_markdown
from .db import database, reset
from .importer import Importer
from .server import serve
from .validation import validation_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eea", description="European Electricity Atlas data core")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Download and normalize Energy-Charts data")
    import_parser.add_argument("--year", type=int, default=2025)
    import_parser.add_argument("--months", type=int, nargs="*", help="Optional months (1-12); default full year")
    import_parser.add_argument("--countries", nargs="+", default=list(COUNTRIES), help="Pilot country codes")
    import_parser.add_argument("--refresh", action="store_true", help="Re-download and reproducibly replace cached periods")

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
    if args.command == "import":
        with database(args.db) as connection:
            importer = Importer(connection, refresh=args.refresh)
            for code in args.countries:
                result = importer.import_country(code, args.year, args.months)
                print(f"{code.upper()}: {json.dumps(result, ensure_ascii=False)}")
        return 0
    if args.command == "report":
        args.output.mkdir(parents=True, exist_ok=True)
        with database(args.db) as connection:
            (args.output / "COVERAGE.generated.md").write_text(coverage_markdown(connection), encoding="utf-8")
            (args.output / "VALIDATION.generated.md").write_text(validation_markdown(connection, args.year), encoding="utf-8")
            (args.output / "SUMMARY.generated.json").write_text(
                json.dumps(aggregate_all(connection, args.year), ensure_ascii=False, indent=2, allow_nan=False),
                encoding="utf-8",
            )
        print(f"Reports written to {args.output}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

