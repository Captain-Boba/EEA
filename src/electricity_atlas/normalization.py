from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Iterable

SERIES_TO_METRIC: dict[str, str] = {
    "solar": "generation_solar",
    "wind_onshore": "generation_wind_onshore",
    "wind_offshore": "generation_wind_offshore",
    "hydro_run_of_river": "generation_hydro",
    "hydro_water_reservoir": "generation_hydro",
    "hydro_pumped_storage": "generation_hydro",
    "hydro": "generation_hydro",
    "biomass": "generation_biomass",
    "nuclear": "generation_nuclear",
    "fossil_gas": "generation_gas",
    "fossil_coal_derived_gas": "generation_gas",
    "fossil_hard_coal": "generation_coal",
    "fossil_brown_coal_lignite": "generation_lignite",
    "fossil_oil": "generation_oil",
}

NON_GENERATION_SERIES = frozenset(
    {
        "hydro_pumped_storage_consumption",
        "battery_consumption",
        "cross_border_electricity_trading",
        "load",
        "residual_load",
        "renewable_share_of_load",
        "renewable_share_of_generation",
    }
)


def iso_to_utc(timestamp: str) -> str:
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp has no timezone offset: {timestamp}")
    return parsed.astimezone(UTC).isoformat()


def power_to_mw(value: float, unit: str) -> float:
    normalized = unit.strip().lower()
    factors = {"w": 1e-6, "kw": 1e-3, "mw": 1.0, "gw": 1e3}
    if normalized not in factors:
        raise ValueError(f"Unsupported power unit: {unit}")
    return float(value) * factors[normalized]


def energy_to_mwh(value: float, unit: str) -> float:
    normalized = unit.strip().lower()
    factors = {"wh": 1e-6, "kwh": 1e-3, "mwh": 1.0, "gwh": 1e3, "twh": 1e6}
    if normalized not in factors:
        raise ValueError(f"Unsupported energy unit: {unit}")
    return float(value) * factors[normalized]


def mw_interval_to_mwh(value_mw: float, interval_minutes: int) -> float:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    return float(value_mw) * interval_minutes / 60.0


def mwh_to_twh(value_mwh: float) -> float:
    return float(value_mwh) / 1_000_000.0


def _series_ids(series: list[dict[str, Any]] | dict[str, Any]) -> Iterable[str]:
    if isinstance(series, dict):
        yield str(series["id"])
        return
    for item in series:
        yield str(item["id"])


def normalize_public_power_record(
    values: dict[str, float | None], series: list[dict[str, Any]] | dict[str, Any]
) -> tuple[dict[str, float], list[str]]:
    metrics: dict[str, float] = defaultdict(float)
    unmapped: list[str] = []
    generation_total = 0.0
    has_generation = False
    available_ids = set(_series_ids(series))

    for series_id in available_ids:
        value = values.get(series_id)
        if value is None:
            continue
        numeric = float(value)
        if series_id == "load":
            metrics["consumption"] = numeric
            continue
        if series_id in NON_GENERATION_SERIES:
            continue
        metric = SERIES_TO_METRIC.get(series_id)
        if metric is None:
            # Unknown production types remain visible as other and are reported.
            metric = "generation_other"
            unmapped.append(series_id)
        metrics[metric] += numeric
        generation_total += numeric
        has_generation = True

    if has_generation:
        metrics["generation_total"] = generation_total
    return dict(metrics), sorted(set(unmapped))


def split_physical_flows(values: dict[str, float | None], unit: str) -> tuple[float, float, float, dict[str, float]]:
    bilateral: dict[str, float] = {}
    for counterparty, value in values.items():
        if counterparty == "sum" or value is None:
            continue
        bilateral[counterparty] = power_to_mw(float(value), unit)
    imports = sum(value for value in bilateral.values() if value > 0)
    exports = sum(-value for value in bilateral.values() if value < 0)
    net = imports - exports
    return imports, exports, net, bilateral
