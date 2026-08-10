from __future__ import annotations

import math
import sqlite3
from datetime import date
from typing import Any, Iterable

from .config import COUNTRIES, EMBER_SOURCE_NAME


def period_bounds(year: int, month: int | None = None) -> tuple[str, str]:
    if month is None:
        return f"{year:04d}-01-01", f"{year + 1:04d}-01-01"
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if month == 12:
        return f"{year:04d}-12-01", f"{year + 1:04d}-01-01"
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month + 1:02d}-01"


def reporting_period_status(year: int, month: int | None = None, today: date | None = None) -> str:
    current = today or date.today()
    if month is not None and (year, month) == (current.year, current.month):
        return "provisional_current_month"
    if month is None and year == current.year:
        return "ytd"
    return "closed"


def renewable_share(renewable_twh: float, generation_twh: float) -> float | None:
    if generation_twh <= 0:
        return None
    return renewable_twh / generation_twh * 100.0


def weighted_mean(values: Iterable[tuple[float, float]]) -> float | None:
    pairs = [
        (float(value), float(weight))
        for value, weight in values
        if weight > 0 and math.isfinite(value)
    ]
    total_weight = sum(weight for _, weight in pairs)
    if not pairs or total_weight == 0:
        return None
    return sum(value * weight for value, weight in pairs) / total_weight


def aggregate_country(
    connection: sqlite3.Connection,
    country_code: str,
    year: int,
    month: int | None = None,
    source: str = EMBER_SOURCE_NAME,
) -> dict[str, Any]:
    if source != EMBER_SOURCE_NAME:
        raise ValueError("source must be 'ember'")
    from .ember_aggregation import aggregate_ember_country

    return aggregate_ember_country(connection, country_code, year, month)


def aggregate_all(
    connection: sqlite3.Connection,
    year: int,
    month: int | None = None,
    source: str = EMBER_SOURCE_NAME,
) -> list[dict[str, Any]]:
    return [aggregate_country(connection, code, year, month, source) for code in COUNTRIES]
