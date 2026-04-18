"""Core configuration types and shared domain type aliases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

DayIndex: TypeAlias = int
SeatCount: TypeAlias = int
USD: TypeAlias = float
Miles: TypeAlias = float

CompetitorMode: TypeAlias = Literal["none", "mirror", "ignore"]
BookingCurveTypeName: TypeAlias = Literal["logistic"]


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
