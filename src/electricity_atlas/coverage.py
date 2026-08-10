from __future__ import annotations

import sqlite3
import json
from typing import Any

from .aggregation import installed_capacity_summary
from .config import COUNTRIES, SOURCE_NAME


def _has_metric(connection: sqlite3.Connection, code: str, metric: str) -> bool:
    return connection.execute(
        """SELECT 1 FROM period_observation
           WHERE country_code=? AND source=? AND metric=? LIMIT 1""",
        (code, SOURCE_NAME, metric),
    ).fetchone() is not None


def coverage_rows(connection: sqlite3.Connection, year: int = 2025) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code, country in COUNTRIES.items():
        first = connection.execute(
            """SELECT MIN(substr(period_start,1,4)) AS year FROM period_observation
               WHERE country_code=? AND source=?""",
            (code, SOURCE_NAME),
        ).fetchone()["year"]
        resolutions = "monthly" if first else None
        issue_rows = connection.execute(
            """SELECT issue_type, details
               FROM quality_issue WHERE country_code=? ORDER BY issue_type, details""",
            (code,),
        ).fetchall()
        grouped: dict[str, set[str]] = {}
        unmapped: set[str] = set()
        for row in issue_rows:
            if row["issue_type"] == "unmapped_generation_categories":
                try:
                    unmapped.update(json.loads(row["details"]))
                except json.JSONDecodeError:
                    grouped.setdefault(row["issue_type"], set()).add(row["details"])
            else:
                grouped.setdefault(row["issue_type"], set()).add(row["details"])
        if unmapped:
            grouped["unmapped_generation_categories"] = {json.dumps(sorted(unmapped))}
        issues = "; ".join(
            f"{kind}: {', '.join(sorted(details))}" for kind, details in sorted(grouped.items())
        ) or None
        issue_types = set(grouped)
        generation = _has_metric(connection, code, "generation_total")
        source_partial = "missing_expected_series" in issue_types
        load_partial = "missing_metric_values" in issue_types
        status = lambda present, partial=False: "partial" if present and partial else ("full" if present else "missing")
        capacity = installed_capacity_summary(connection, code, f"{year + 1:04d}-01-01", year)
        capacity_status = {"current": "full", "stale": "partial", "missing": "missing"}[capacity["status"]]
        capacity_note = ""
        if capacity["snapshot_timestamp"]:
            capacity_note = (
                f"Kapazitätssnapshot {capacity['snapshot_timestamp']} "
                f"({capacity['status']}, Alter {capacity['age_years']} Kalenderjahre)."
            )
        rows.append(
            {
                "country_code": code,
                "country_name": country.name,
                "generation": status(generation, source_partial),
                "mix": status(generation, source_partial),
                "consumption": status(_has_metric(connection, code, "consumption"), load_partial),
                "price": status(_has_metric(connection, code, "day_ahead_price")),
                "import_export": status(_has_metric(connection, code, "net_import")),
                "carbon": "missing",
                "installed_capacity": capacity_status,
                "installed_capacity_snapshot": capacity["snapshot_timestamp"],
                "installed_capacity_status": capacity["status"],
                "earliest_imported_year": first,
                "resolution": resolutions,
                "gaps": issues,
                "source": SOURCE_NAME,
                "notes": "; ".join(
                    filter(
                        None,
                        (
                            country.notes,
                            capacity_note,
                            "CO2-Intensität nicht über Energy-Charts v2 verfügbar.",
                        ),
                    )
                ),
            }
        )
    return rows


def coverage_markdown(connection: sqlite3.Connection, year: int = 2025) -> str:
    def mark(value: str) -> str:
        return {"full": "✅", "partial": "⚠️", "missing": "—"}[value]

    lines = [
        "# Coverage Report (automatisch erzeugt)",
        "",
        "| Land | Erzeugung | Mix | Verbrauch | Preis | Import/Export | CO₂ | installierte Leistung | Kapazitäts-Snapshot | frühestes importiertes Jahr | Auflösung |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    rows = coverage_rows(connection, year)
    for row in rows:
        lines.append(
            f"| {row['country_code']} | {mark(row['generation'])} | {mark(row['mix'])} | "
            f"{mark(row['consumption'])} | {mark(row['price'])} | {mark(row['import_export'])} | "
            f"{mark(row['carbon'])} | {mark(row['installed_capacity'])} | "
            f"{row['installed_capacity_snapshot'] or '?'} | {row['earliest_imported_year'] or '?'} | "
            f"{row['resolution'] or '?'} |"
        )
    lines.extend(["", "## Hinweise"])
    for row in rows:
        issue = f" Datenqualitätsmeldungen: {row['gaps']}." if row["gaps"] else ""
        lines.append(f"- **{row['country_code']}**: {row['notes']}{issue}")
    lines.extend(
        [
            "",
            "Der Wert ‚frühestes importiertes Jahr‘ beschreibt den lokalen Datenbestand und ist nicht als vollständige historische API-Reichweite zu lesen.",
        ]
    )
    return "\n".join(lines) + "\n"
