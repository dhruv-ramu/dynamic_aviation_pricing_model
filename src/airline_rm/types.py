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
    static_bucket_index: int | None = None
    overbooking_enabled: bool = True
    denied_boarding_delay_hours: float = 2.5
    denied_boarding_compensation_multiplier: float = 4.0
    denied_boarding_compensation_cap: float = 2150.0
    goodwill_penalty_per_bumped_passenger: float = 150.0
