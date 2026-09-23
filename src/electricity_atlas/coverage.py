from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

from .aggregation import aggregate_country
from .config import COUNTRIES, EMBER_SOURCE_NAME


def coverage_rows(connection: sqlite3.Connection, year: int, *, today: date | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code, country in COUNTRIES.items():
        summary = aggregate_country(connection, code, year, today=today)
        earliest = connection.execute(
            """SELECT MIN(substr(period_start,1,4))
               FROM period_observation WHERE source=? AND country_code=?""",
            (EMBER_SOURCE_NAME, code),
        ).fetchone()[0]
        rows.append(
            {
                "country_code": code,
                "country_name": country.name,
                "source": EMBER_SOURCE_NAME,
                "generation": "available" if summary["generation_twh"] is not None else "missing",
                "demand": "available" if summary["consumption_twh"] is not None else "missing",
                "carbon_intensity": (
                    "available" if summary["carbon_intensity_gco2eq_kwh"] is not None else "missing"
                ),
                "wholesale_price": summary["price_coverage"],
                "data_status": summary["data_status"],
                "earliest_imported_year": int(earliest) if earliest else None,
            }
        )
    return rows


def coverage_markdown(connection: sqlite3.Connection, year: int, *, today: date | None = None) -> str:
    lines = [
        f"# Ember coverage {year}",
        "",
        "| Country | Generation | Demand | CO2 intensity | Wholesale price | Status | Earliest year |",
        "|---|---|---|---|---|---|---:|",
    ]
    for row in coverage_rows(connection, year, today=today):
        lines.append(
            f"| {row['country_code']} | {row['generation']} | {row['demand']} | "
            f"{row['carbon_intensity']} | {row['wholesale_price']} | {row['data_status']} | "
            f"{row['earliest_imported_year'] or '—'} |"
        )
    return "\n".join(lines) + "\n"
