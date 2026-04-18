"""Lightweight named scenario overrides (dict → ``dataclasses.replace``)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from airline_rm.types import SimulationConfig

SCENARIO_PRESETS: dict[str, dict[str, Any]] = {
    "high_no_show": {"no_show_mean": 0.18},
    "low_no_show": {"no_show_mean": 0.04},
    "business_heavy": {"early_business_share": 0.28, "late_business_share": 0.72},
    "leisure_heavy": {"early_business_share": 0.08, "late_business_share": 0.42},
    "weak_demand": {"expected_total_demand": 140.0, "demand_multiplier": 0.85},
    "strong_demand": {"expected_total_demand": 260.0, "demand_multiplier": 1.15},
    "no_overbooking": {"overbooking_enabled": False},
}


def list_scenarios() -> tuple[str, ...]:
    return tuple(sorted(SCENARIO_PRESETS.keys()))


def apply_scenario(config: SimulationConfig, scenario_name: str) -> SimulationConfig:
    """Return a new config with fields overridden by a named preset."""

    key = str(scenario_name).strip().lower()
    if key not in SCENARIO_PRESETS:
        raise KeyError(f"Unknown scenario {scenario_name!r}. Available: {', '.join(list_scenarios())}")
    return replace(config, **SCENARIO_PRESETS[key])
