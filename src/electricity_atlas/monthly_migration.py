from __future__ import annotations

import calendar
import sqlite3
from datetime import date
from typing import Any

from .config import SOURCE_NAME


def _bounds(token: str) -> tuple[str, str]:
    year, month = (int(part) for part in token.split("-"))
    return f"{token}-01", f"{token}-{calendar.monthrange(year, month)[1]:02d}"


def _quality(token: str) -> str:
    return "provisional_current_month" if token == date.today().strftime("%Y-%m") else "observed"


def _upsert(
    connection: sqlite3.Connection,
    code: str,
    token: str,
    endpoint: str,
    series: str,
    metric: str,
    value: float,
    unit: str,
) -> None:
    start, end = _bounds(token)
    connection.execute(
        """INSERT INTO period_observation
           (country_code,period_start,period_end,granularity,source,source_endpoint,
            source_series,metric,value,unit,quality_status)
           VALUES (?,?,?,'monthly',?,?,?,?,?,?,?)
           ON CONFLICT(country_code,period_start,period_end,granularity,source,source_endpoint,source_series,metric)
           DO UPDATE SET value=excluded.value,unit=excluded.unit,quality_status=excluded.quality_status""",
        (code, start, end, SOURCE_NAME, endpoint, series, metric, value, unit, _quality(token)),
    )


def migrate_legacy_intervals(connection: sqlite3.Connection) -> dict[str, Any]:
    legacy_observations = connection.execute(
        "SELECT COUNT(*) FROM observation WHERE source=?", (SOURCE_NAME,)
    ).fetchone()[0]
    legacy_flows = connection.execute(
        "SELECT COUNT(*) FROM bilateral_flow WHERE source=?", (SOURCE_NAME,)
    ).fetchone()[0]
    if not legacy_observations and not legacy_flows:
        return {"legacy_observations_removed": 0, "legacy_flows_removed": 0, "period_rows_written": 0}

    connection.execute("SAVEPOINT monthly_migration")
    written = 0
    try:
        energy_rows = connection.execute(
            """SELECT country_code,source_endpoint,substr(timestamp,1,7) AS month,metric,
                      SUM(value * interval_minutes / 60.0) / 1000000.0 AS value_twh
               FROM observation
               WHERE source=? AND unit='MW' AND source_endpoint IN ('public_power','cbpf')
                 AND interval_minutes IS NOT NULL
               GROUP BY country_code,source_endpoint,month,metric""",
            (SOURCE_NAME,),
        ).fetchall()
        for row in energy_rows:
            _upsert(
                connection,
                row["country_code"],
                row["month"],
                row["source_endpoint"],
                "",
                row["metric"],
                row["value_twh"],
                "TWh",
            )
            written += 1

        price_rows = connection.execute(
            """SELECT country_code,bidding_zone,substr(timestamp,1,7) AS month,
                      SUM(value * interval_minutes) / SUM(interval_minutes) AS average_value,
                      MIN(value) AS minimum_value,MAX(value) AS maximum_value,
                      SUM(CASE WHEN value < 0 THEN 1 ELSE 0 END) AS negative_intervals,
                      SUM(CASE WHEN value < 0 THEN interval_minutes ELSE 0 END) / 60.0 AS negative_hours,
                      SUM(interval_minutes) / 60.0 AS weight_hours
               FROM observation
               WHERE source=? AND source_endpoint='price' AND metric='day_ahead_price'
                 AND interval_minutes IS NOT NULL
               GROUP BY country_code,bidding_zone,month""",
            (SOURCE_NAME,),
        ).fetchall()
        for row in price_rows:
            metrics = (
                ("day_ahead_price", row["average_value"], "EUR/MWh"),
                ("day_ahead_price_min", row["minimum_value"], "EUR/MWh"),
                ("day_ahead_price_max", row["maximum_value"], "EUR/MWh"),
                ("negative_price_intervals", row["negative_intervals"], "count"),
                ("negative_price_hours", row["negative_hours"], "hours"),
                ("price_weight_hours", row["weight_hours"], "hours"),
            )
            for metric, value, unit in metrics:
                _upsert(
                    connection,
                    row["country_code"],
                    row["month"],
                    "price",
                    row["bidding_zone"],
                    metric,
                    float(value),
                    unit,
                )
                written += 1

        connection.execute("DELETE FROM observation WHERE source=?", (SOURCE_NAME,))
        connection.execute("DELETE FROM bilateral_flow WHERE source=?", (SOURCE_NAME,))
        connection.execute("RELEASE SAVEPOINT monthly_migration")
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT monthly_migration")
        connection.execute("RELEASE SAVEPOINT monthly_migration")
        raise

    return {
        "legacy_observations_removed": legacy_observations,
        "legacy_flows_removed": legacy_flows,
        "period_rows_written": written,
    }
