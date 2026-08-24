from __future__ import annotations

import sqlite3
from collections import OrderedDict
from datetime import date
from typing import Any

from .aggregation import aggregate_country
from .config import ATLAS_MIN_YEAR, COUNTRIES
from .metrics import metric_catalog
from .storage_online import latest_storage


def _validate(country_code: str, year: int, month: int | None) -> str:
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError("country must be a known Atlas country code")
    if not ATLAS_MIN_YEAR <= year <= date.today().year:
        raise ValueError(f"year must be between {ATLAS_MIN_YEAR} and {date.today().year}")
    if month is not None and not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    return code


def _capacity_reporting_row(
    connection: sqlite3.Connection, country_code: str, requested_year: int
) -> tuple[dict[str, Any], int | None]:
    """Return the newest available capacity row at or before the requested year.

    This mirrors the map's availability rule while deliberately keeping the
    reporting year separate from the requested profile period.
    """
    for data_year in range(requested_year, ATLAS_MIN_YEAR - 1, -1):
        row = aggregate_country(connection, country_code, data_year)
        if any(
            value is not None
            for metric_id, value in row.items()
            if metric_id.startswith("capacity_")
        ):
            return row, data_year
    return {}, None


def _source_for(metric: dict[str, Any], row: dict[str, Any]) -> str:
    if metric["id"] == "price_avg_eur_mwh":
        return row.get("price_source_label") or metric["source"]
    return metric["source"]


def _metric_payload(
    metric: dict[str, Any],
    row: dict[str, Any],
    *,
    requested_period: str,
    temporal_basis: str,
    actual_period: str | None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = row.get(metric["id"])
    warnings = [issue["details"] for issue in row.get("quality_issues", []) if issue.get("details")]
    if provenance is not None:
        source = provenance.get("source_label") or metric["source"]
        quality_status = provenance.get("quality_status") or "missing"
        warnings = [provenance["coverage_type"]] if provenance.get("coverage_type") else []
    else:
        source = _source_for(metric, row)
        quality_status = "missing" if value is None else row.get("data_status", "observed")
    return {
        "id": metric["id"],
        "label": metric["label_de"],
        "group": metric["group"],
        "family": metric["family"],
        "representation": metric["representation"],
        "value": value,
        "unit": metric["unit"],
        "requested_period": requested_period,
        "actual_period": actual_period,
        "temporal_basis": temporal_basis,
        "data_status": "missing" if value is None else row.get("data_status", "observed"),
        "quality_status": quality_status,
        "warnings": warnings,
        "source": source,
    }


def build_country_profile(
    connection: sqlite3.Connection,
    country_code: str,
    year: int,
    month: int | None = None,
) -> dict[str, Any]:
    """Build one period-aware, read-only profile from existing aggregation data."""
    code = _validate(country_code, year, month)
    requested_period = f"{year:04d}-{month:02d}" if month is not None else str(year)
    selected_row = aggregate_country(connection, code, year, month)
    annual_row = selected_row if month is None else aggregate_country(connection, code, year)
    capacity_row, capacity_year = _capacity_reporting_row(connection, code, year)
    storage = latest_storage(connection)
    snapshot_row = next(
        (row for row in storage.get("countries", []) if row["country_code"] == code),
        {"country_code": code, "metric_provenance": {}},
    )

    sections: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for metric in metric_catalog():
        availability = metric["temporal_availability"]
        metric_id = metric["id"]
        if availability["snapshot"]:
            provenance = snapshot_row.get("metric_provenance", {}).get(metric_id)
            payload = _metric_payload(
                metric,
                snapshot_row,
                requested_period=requested_period,
                temporal_basis="snapshot",
                actual_period=provenance.get("date") if provenance else None,
                provenance=provenance,
            )
        elif metric["group"] == "Installierte Leistung":
            payload = _metric_payload(
                metric,
                capacity_row,
                requested_period=requested_period,
                temporal_basis="yearly",
                actual_period=str(capacity_year) if capacity_year is not None else None,
            )
        elif month is not None and availability["monthly"]:
            payload = _metric_payload(
                metric,
                selected_row,
                requested_period=requested_period,
                temporal_basis="monthly",
                actual_period=requested_period,
            )
        else:
            payload = _metric_payload(
                metric,
                annual_row,
                requested_period=requested_period,
                temporal_basis="yearly",
                actual_period=str(year),
            )
        sections.setdefault(metric["group"], []).append(payload)

    return {
        "country": {"code": code, "name": COUNTRIES[code].name},
        "requested": {
            "year": year,
            "month": month,
            "period": requested_period,
            "period_status": selected_row["period_status"],
        },
        "coverage": selected_row["data_status"],
        "sections": [
            {"id": group, "label": group, "metrics": metrics}
            for group, metrics in sections.items()
        ],
    }
