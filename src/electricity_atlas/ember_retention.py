"""Narrow scheduled-refresh policy for withdrawn monthly generation components.

Keep a whole country/month of the three related Ember datasets, never splice an
old component/share into revised totals. Empty periods, missing aggregates and
losses in demand/carbon/yearly/other sources remain critical errors.
"""
from __future__ import annotations

from collections import defaultdict

from .ember_importer import EMBER_SERIES_TO_METRIC


RETAINED_SOURCE_GAP = "retained_source_gap"
MONTHLY_ENDPOINTS = (
    "electricity-generation/monthly", "electricity-demand/monthly", "carbon-intensity/monthly",
)
COLUMNS = (
    "country_code", "period_start", "period_end", "granularity", "source",
    "source_endpoint", "source_series", "metric", "value", "unit", "quality_status",
)


def _key(row):
    return tuple(row[name] for name in COLUMNS if name not in ("value", "quality_status"))


def monthly_ember_baseline(connection):
    return {
        _key(row): row for row in (
            dict(row) for row in connection.execute(
                f"SELECT {','.join(COLUMNS)} FROM period_observation "
                "WHERE source='ember' AND granularity='monthly' "
                "AND source_endpoint IN (?,?,?)", MONTHLY_ENDPOINTS,
            )
        )
    }


def retain_monthly_source_gaps(connection, before):
    """Called only after all Ember imports succeeded, before the global guard.

No missing key is silently accepted. The baseline is bounded by the existing
database and lives only in memory; restored rows carry a persistent quality
flag. A later complete source response replaces them normally and clears it.
"""
    after = monthly_ember_baseline(connection)
    missing = [row for key, row in before.items() if key not in after]
    affected = defaultdict(list)
    for row in missing:
        component = EMBER_SERIES_TO_METRIC.get(row["source_series"].casefold())
        if (row["source_endpoint"] != MONTHLY_ENDPOINTS[0] or component is None
                or row["metric"] not in (component, "share_of_generation_pct")):
            raise ValueError("Ember lost monthly coverage outside the component-retention policy")
        affected[(row["country_code"], row["period_start"], row["period_end"])].append(row)

    def group(row):
        return row["country_code"], row["period_start"], row["period_end"]

    previous = defaultdict(list)
    fresh = defaultdict(list)
    for row in before.values():
        if group(row) in affected:
            previous[group(row)].append(row)
    for row in after.values():
        if group(row) in affected:
            fresh[group(row)].append(row)
    for period in affected:
        # Reject complete generation/technology outages even when an aggregate
        # happens to survive. The general coverage guard also runs afterwards.
        if not any(row["source_endpoint"] == MONTHLY_ENDPOINTS[0]
                   and row["metric"] in EMBER_SERIES_TO_METRIC.values()
                   for row in fresh[period]):
            raise ValueError("Ember lost all monthly generation components; refusing retention")

    periods = []
    connection.execute("SAVEPOINT ember_source_retention")
    try:
        for period in sorted(affected):
            country, start, end = period
            connection.execute(
                "DELETE FROM period_observation WHERE source='ember' AND granularity='monthly' "
                "AND country_code=? AND period_start=? AND period_end=? "
                "AND source_endpoint IN (?,?,?)", (*period, *MONTHLY_ENDPOINTS),
            )
            connection.executemany(
                f"INSERT INTO period_observation ({','.join(COLUMNS)}) VALUES ({','.join('?' for _ in COLUMNS)})",
                [tuple(RETAINED_SOURCE_GAP if name == "quality_status" else row[name]
                       for name in COLUMNS) for row in previous[period]],
            )
            periods.append({
                "country_code": country, "period_start": start, "period_end": end,
                "missing_observations": len(affected[period]),
                "missing_series": sorted({row["source_series"] for row in affected[period]}),
                "retained_observations": len(previous[period]),
            })
        connection.execute("RELEASE SAVEPOINT ember_source_retention")
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT ember_source_retention")
        connection.execute("RELEASE SAVEPOINT ember_source_retention")
        raise
    return {
        "quality_status": RETAINED_SOURCE_GAP,
        "missing_observations": len(missing),
        "retained_observations": sum(item["retained_observations"] for item in periods),
        "retained_periods": periods,
    }
