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
    # --- Dynamic policy heuristics (profit-oriented; ignored by static/rule_based) ---
    dynamic_pace_ratio_raise_threshold: float = 1.05
    dynamic_pace_ratio_lower_threshold: float = 0.95
    dynamic_pace_gap_raise_abs: float = 10.0
    dynamic_pace_gap_lower_abs: float = -10.0
    dynamic_raise_bucket_steps_ahead: int = 2
    dynamic_lower_bucket_steps_behind: int = 1
    dynamic_pace_tight_seats_rem_frac: float = 0.45
    dynamic_pace_extra_raise_when_tight: int = 1
    dynamic_late_floor_days_until_departure: int = 10
    dynamic_min_bucket_index_late: int = 1
    dynamic_scarcity_fill_ratio_1: float = 0.70
    dynamic_scarcity_fill_ratio_2: float = 0.85
    dynamic_scarcity_raise_steps_1: int = 1
    dynamic_scarcity_raise_steps_2: int = 2
    dynamic_demand_pressure_ratio: float = 1.15
    dynamic_competitor_disable_fill_ratio: float = 0.80
    dynamic_policy_debug: bool = False
    static_bucket_index: int | None = None
    overbooking_enabled: bool = True
    denied_boarding_delay_hours: float = 2.5
    denied_boarding_compensation_multiplier: float = 4.0
    denied_boarding_compensation_cap: float = 2150.0
    goodwill_penalty_per_bumped_passenger: float = 150.0
