"""Time- and inventory-invariant pricing."""

from __future__ import annotations

from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.types import SimulationConfig


class StaticPricingPolicy(PricingPolicy):
    """Always quotes the same bucket fare (default: most expensive bucket for legacy parity)."""

    def __init__(self, config: SimulationConfig) -> None:
        self._buckets = FareBucketSystem.from_values(config.fare_buckets)
        if config.static_bucket_index is None:
            self._bucket_index = self._buckets.max_bucket()
        else:
            self._bucket_index = self._buckets.clamp_bucket_index(int(config.static_bucket_index))

    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        _ = days_until_departure, state, competitor_fare
        fare = self._buckets.current_fare(self._bucket_index)
        return PricingAction(
            bucket_index=self._bucket_index,
            fare=fare,
            note="static",
        )
