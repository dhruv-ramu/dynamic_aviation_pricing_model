"""Time- and inventory-invariant pricing."""

from __future__ import annotations

from airline_rm.types import SimulationConfig
from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.pricing_policy_base import PricingPolicy


class StaticPricingPolicy(PricingPolicy):
    """Always quotes the same fare (first bucket or base fare)."""

    def __init__(self, config: SimulationConfig) -> None:
        self._fare = float(config.fare_buckets[0]) if config.fare_buckets else float(config.base_fare)

    def quote_fare(self, days_until_departure: int, state: SimulationState) -> float:
        _ = days_until_departure, state
        return self._fare
