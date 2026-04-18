"""Transparent rule-based bucket selection with mild competitor reactions."""

from __future__ import annotations

from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.types import SimulationConfig


class RuleBasedPricingPolicy(PricingPolicy):
    """Heuristic mapping from time-to-departure, load factor, and competitor fare to a bucket."""

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._buckets = FareBucketSystem.from_values(config.fare_buckets)

    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        cap = state.flight.capacity
        seats_rem = max(0, cap - min(state.seats_sold, cap))

        idx = self._buckets.bucket_for_load_and_time(
            days_until_departure,
            seats_rem,
            cap,
            early_window_days=self._config.early_window_days,
            late_window_days=self._config.late_window_days,
            low_load_factor_threshold=self._config.low_load_factor_threshold,
            high_load_factor_threshold=self._config.high_load_factor_threshold,
        )

        our = self._buckets.current_fare(idx)
        note = "rules:base"

        if competitor_fare is not None:
            if our - competitor_fare > self._config.competitor_match_threshold:
                idx = self._buckets.lower_bucket(idx, 1)
                note = "rules:match_down"
            elif (
                competitor_fare - our > self._config.competitor_match_threshold
                and seats_rem / float(cap) <= self._config.low_load_factor_threshold
            ):
                idx = self._buckets.raise_bucket(idx, 1)
                note = "rules:match_up_tight"

        idx = self._buckets.clamp_bucket_index(idx)
        fare = self._buckets.current_fare(idx)
        return PricingAction(bucket_index=idx, fare=fare, note=note)
