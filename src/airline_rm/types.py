"""Core configuration types and shared domain type aliases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

DayIndex: TypeAlias = int
SeatCount: TypeAlias = int
USD: TypeAlias = float
Miles: TypeAlias = float

CompetitorMode: TypeAlias = Literal["none", "static", "reactive"]
BookingCurveTypeName: TypeAlias = Literal["logistic"]
PricingPolicyName: TypeAlias = Literal["static", "rule_based", "dynamic"]


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Immutable simulation parameters loaded from YAML."""

    booking_horizon_days: int
    route_distance_miles: float
    capacity: int
    base_fare: float
    fare_buckets: tuple[float, ...]
    business_share_late: float
    leisure_elasticity: float
    business_elasticity: float
    no_show_mean: float
    overbooking_limit_pct: float
    ancillary_mean: float
    casm_ex: float
    fixed_flight_cost: float
    competitor_mode: str
    rng_seed: int
    expected_total_demand: float
    demand_multiplier: float
    booking_curve_type: BookingCurveTypeName
    booking_curve_steepness: float
    booking_curve_midpoint: float
    early_business_share: float
    late_business_share: float
    segment_transition_midpoint_days: float
    segment_transition_steepness: float
    leisure_wtp_mean: float
    leisure_wtp_sigma: float
    business_wtp_mean: float
    business_wtp_sigma: float
    route_origin: str = "UNK"
    route_destination: str = "UNK"
    demand_stochastic: bool = True
    pricing_policy: str = "static"
    early_window_days: int = 45
    late_window_days: int = 14
    low_load_factor_threshold: float = 0.35
    high_load_factor_threshold: float = 0.85
    pace_gap_raise_threshold: float = 6.0
    pace_gap_lower_threshold: float = -6.0
    competitor_base_offset: float = -12.0
    competitor_noise_std: float = 4.0
    competitor_match_threshold: float = 12.0
    competitor_response_strength: float = 0.3
    # --- Dynamic policy: stateful score-based controller (ignored by static/rule_based) ---
    dynamic_initial_bucket_index: int | None = None
    dynamic_weight_pace: float = 0.88
    dynamic_weight_scarcity: float = 1.22
    dynamic_weight_demand_pressure: float = 1.52
    dynamic_score_strong_raise: float = 1.12
    dynamic_score_mild_raise: float = 0.36
    dynamic_score_strong_lower: float = -0.74
    dynamic_bucket_change_deadband: float = 0.26
    dynamic_strong_raise_allows_two_steps: bool = True
    dynamic_two_step_pace_ratio: float = 1.07
    dynamic_two_step_scarcity_fill: float = 0.82
    dynamic_two_step_demand_score: float = 0.72
    dynamic_pace_late_dampen: float = 0.30
    dynamic_scarcity_fill_ratio_1: float = 0.68
    dynamic_scarcity_fill_ratio_2: float = 0.84
    dynamic_demand_pressure_neutral_ratio: float = 1.02
    dynamic_demand_ratio_score_scale: float = 0.92
    dynamic_competitor_disable_fill_ratio: float = 0.78
    dynamic_competitor_late_ignore_days: int = 12
    dynamic_competitor_ignore_if_ahead_of_pace: bool = True
    dynamic_late_floor_days_until_departure: int = 10
    dynamic_min_bucket_index_late: int = 1
    dynamic_late_window_min_bucket_index: int = 2
    dynamic_min_days_between_bucket_changes: int = 0
    dynamic_policy_debug: bool = False
    static_bucket_index: int | None = None
    overbooking_enabled: bool = True
    denied_boarding_delay_hours: float = 2.5
    denied_boarding_compensation_multiplier: float = 4.0
    denied_boarding_compensation_cap: float = 2150.0
    goodwill_penalty_per_bumped_passenger: float = 150.0
