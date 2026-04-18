"""Core configuration types and shared domain type aliases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

DayIndex: TypeAlias = int
SeatCount: TypeAlias = int
USD: TypeAlias = float
Miles: TypeAlias = float

CompetitorMode: TypeAlias = Literal["none", "mirror", "ignore"]


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
    route_origin: str = "UNK"
    route_destination: str = "UNK"
