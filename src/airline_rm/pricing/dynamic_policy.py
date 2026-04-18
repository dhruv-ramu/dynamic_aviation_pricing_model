"""Heuristic dynamic pricing using booking pace vs the configured curve."""

from __future__ import annotations

from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.types import SimulationConfig


class DynamicPricingPolicy(PricingPolicy):
    """Adjust buckets using pace vs expected cumulative demand and mild competitor nudges."""

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._buckets = FareBucketSystem.from_values(config.fare_buckets)
        self._curve = BookingCurveModel.from_simulation_config(config)

    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        cap = state.flight.capacity
        seats_rem = state.seats_remaining

        total_intensity = float(self._config.expected_total_demand * self._config.demand_multiplier)
        expected_sold = min(cap, total_intensity * self._curve.cumulative_share(days_until_departure))
        pace_gap = float(state.seats_sold - expected_sold)

        idx = self._buckets.bucket_for_load_and_time(
            days_until_departure,
            seats_rem,
            cap,
            early_window_days=self._config.early_window_days,
            late_window_days=self._config.late_window_days,
            low_load_factor_threshold=self._config.low_load_factor_threshold,
            high_load_factor_threshold=self._config.high_load_factor_threshold,
        )

        note = "dyn:anchor"
        if pace_gap < self._config.pace_gap_lower_threshold:
            idx = self._buckets.lower_bucket(idx, 1)
            note = "dyn:behind_pace"
        elif pace_gap > self._config.pace_gap_raise_threshold:
            idx = self._buckets.raise_bucket(idx, 1)
            note = "dyn:ahead_pace"

        if seats_rem / float(cap) <= self._config.low_load_factor_threshold:
            idx = self._buckets.raise_bucket(idx, 1)
            note = "dyn:tight_inventory"

        idx = self._buckets.clamp_bucket_index(idx)
        fare = self._buckets.current_fare(idx)

        if competitor_fare is not None and fare - competitor_fare > self._config.competitor_match_threshold:
            idx = self._buckets.lower_bucket(idx, 1)
            idx = self._buckets.clamp_bucket_index(idx)
            fare = self._buckets.current_fare(idx)
            note = "dyn:undercut_response"

        return PricingAction(bucket_index=idx, fare=fare, note=note)
