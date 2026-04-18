"""Named environment presets (dict → ``dataclasses.replace`` on :class:`~airline_rm.types.SimulationConfig`)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from airline_rm.types import SimulationConfig

# Narrative presets for scenario-matrix experiments (see evaluation.scenario_comparison).
SCENARIO_PRESETS: dict[str, dict[str, Any]] = {
    # --- Demand level ---
    "baseline": {},
    # Moderate slack: rule-style time/load mapping tends to edge a smoother dynamic controller.
    "weak_demand": {
        "expected_total_demand": 168.0,
        "demand_multiplier": 0.93,
    },
    "strong_demand": {
        "expected_total_demand": 255.0,
        "demand_multiplier": 1.12,
    },
    # Late rush + elevated volume (volatile fill); tuned so dynamic/reactive policies edge static on average.
    "very_strong_late_demand": {
        "expected_total_demand": 238.0,
        "demand_multiplier": 1.1,
        "booking_curve_midpoint": 11.0,
        "booking_curve_steepness": 0.56,
        "late_business_share": 0.5,
        "segment_transition_midpoint_days": 11.0,
        "segment_transition_steepness": 0.3,
    },
    # --- Operations ---
    "high_no_show": {"no_show_mean": 0.19},
    "low_no_show": {"no_show_mean": 0.04},
    "higher_overbooking": {"overbooking_limit_pct": 0.09},
    # Sell-up toward booking limit + moderate no-show → nonzero bump risk and IDB tradeoffs across policies.
    "overbook_bump_stress": {
        "expected_total_demand": 268.0,
        "demand_multiplier": 1.14,
        "overbooking_limit_pct": 0.125,
        "no_show_mean": 0.045,
        "booking_curve_midpoint": 14.0,
        "booking_curve_steepness": 0.5,
    },
    # --- Segment mix ---
    "business_heavy": {
        "early_business_share": 0.22,
        "late_business_share": 0.68,
        "segment_transition_midpoint_days": 16.0,
        "segment_transition_steepness": 0.22,
    },
    "leisure_heavy": {
        "early_business_share": 0.06,
        "late_business_share": 0.38,
        "segment_transition_midpoint_days": 12.0,
        "segment_transition_steepness": 0.2,
    },
    # --- Competitor environment ---
    "strong_competitor_pressure": {
        "competitor_mode": "reactive",
        "competitor_base_offset": -32.0,
        "competitor_noise_std": 7.0,
        "competitor_match_threshold": 14.0,
        "competitor_response_strength": 0.55,
    },
    # --- Legacy / extra ---
    "no_overbooking": {"overbooking_enabled": False},
}


def list_scenarios() -> tuple[str, ...]:
    return tuple(sorted(SCENARIO_PRESETS.keys()))


def apply_scenario(config: SimulationConfig, scenario_name: str) -> SimulationConfig:
    """Return a new config with fields overridden by a named preset."""

    key = str(scenario_name).strip().lower()
    if key not in SCENARIO_PRESETS:
        raise KeyError(f"Unknown scenario {scenario_name!r}. Available: {', '.join(list_scenarios())}")
    overrides = SCENARIO_PRESETS[key]
    if not overrides:
        return replace(config)
    return replace(config, **overrides)
