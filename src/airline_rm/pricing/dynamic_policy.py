"""Heuristic dynamic pricing: summed bucket deltas from pace, scarcity, demand pressure, competitor."""

from __future__ import annotations

import logging

from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.types import SimulationConfig

logger = logging.getLogger(__name__)

_PACE_EPS = 1e-6


class DynamicPricingPolicy(PricingPolicy):
    """Combine pace, scarcity, residual-demand, and mild competitor signals into one bucket move."""

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._buckets = FareBucketSystem.from_values(config.fare_buckets)
        self._curve = BookingCurveModel.from_simulation_config(config)

    def _total_expected_demand(self) -> float:
        return float(self._config.expected_total_demand * self._config.demand_multiplier)

    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        cfg = self._config
        cap = state.flight.capacity
        sold = int(state.seats_sold)
        phys_sold = min(sold, cap) if cap > 0 else 0
        seats_rem_phys = max(0, cap - phys_sold)

        cum = float(self._curve.cumulative_share(days_until_departure))
        total_int = self._total_expected_demand()
        expected_cum = cum * total_int
        pace_gap = float(sold - expected_cum)
        pace_ratio = sold / max(expected_cum, _PACE_EPS)

        seat_fill_ratio = phys_sold / float(cap) if cap > 0 else 0.0

        anchor = self._buckets.bucket_for_load_and_time(
            days_until_departure,
            seats_rem_phys,
            cap,
            early_window_days=cfg.early_window_days,
            late_window_days=cfg.late_window_days,
            low_load_factor_threshold=cfg.low_load_factor_threshold,
            high_load_factor_threshold=cfg.high_load_factor_threshold,
        )

        pace_adjustment = self._pace_bucket_delta(
            pace_ratio,
            pace_gap,
            seats_rem_phys,
            cap,
        )
        scarcity_adjustment = self._scarcity_bucket_delta(seat_fill_ratio)
        expected_remaining_demand = (1.0 - cum) * total_int
        demand_pressure_adjustment = self._demand_pressure_bucket_delta(
            expected_remaining_demand,
            seats_rem_phys,
        )

        pre_comp_idx = self._buckets.clamp_bucket_index(
            anchor + pace_adjustment + scarcity_adjustment + demand_pressure_adjustment
        )
        our_pre_comp_fare = self._buckets.current_fare(pre_comp_idx)
        competitor_adjustment = self._competitor_bucket_delta(
            our_pre_comp_fare,
            competitor_fare,
            seat_fill_ratio,
        )

        delta = (
            pace_adjustment
            + scarcity_adjustment
            + demand_pressure_adjustment
            + competitor_adjustment
        )
        new_idx = self._buckets.clamp_bucket_index(anchor + delta)

        if days_until_departure <= cfg.dynamic_late_floor_days_until_departure:
            new_idx = max(new_idx, cfg.dynamic_min_bucket_index_late)
        new_idx = self._buckets.clamp_bucket_index(new_idx)
        fare = self._buckets.current_fare(new_idx)

        if cfg.dynamic_policy_debug:
            logger.info(
                "dynamic_policy day=%s bucket=%s pace_gap=%.3f seat_fill=%.3f "
                "rem_dem=%.2f chosen=%s delta=%s",
                days_until_departure,
                anchor,
                pace_gap,
                seat_fill_ratio,
                expected_remaining_demand,
                new_idx,
                delta,
            )

        note = self._note_from_adjustments(
            pace_adjustment,
            scarcity_adjustment,
            demand_pressure_adjustment,
            competitor_adjustment,
        )
        return PricingAction(bucket_index=new_idx, fare=fare, note=note)

    def _pace_bucket_delta(
        self,
        pace_ratio: float,
        pace_gap: float,
        seats_rem_phys: int,
        cap: int,
    ) -> int:
        cfg = self._config
        ahead = (
            pace_ratio > cfg.dynamic_pace_ratio_raise_threshold
            or pace_gap > cfg.dynamic_pace_gap_raise_abs
        )
        behind = (
            pace_ratio < cfg.dynamic_pace_ratio_lower_threshold
            or pace_gap < cfg.dynamic_pace_gap_lower_abs
        )
        if ahead:
            steps = cfg.dynamic_raise_bucket_steps_ahead
            if (
                cap > 0
                and (seats_rem_phys / float(cap)) <= cfg.dynamic_pace_tight_seats_rem_frac
            ):
                steps += cfg.dynamic_pace_extra_raise_when_tight
            return steps
        if behind:
            return -cfg.dynamic_lower_bucket_steps_behind
        return 0

    def _scarcity_bucket_delta(self, seat_fill_ratio: float) -> int:
        cfg = self._config
        if seat_fill_ratio > cfg.dynamic_scarcity_fill_ratio_2:
            return cfg.dynamic_scarcity_raise_steps_2
        if seat_fill_ratio > cfg.dynamic_scarcity_fill_ratio_1:
            return cfg.dynamic_scarcity_raise_steps_1
        return 0

    def _demand_pressure_bucket_delta(
        self,
        expected_remaining_demand: float,
        seats_rem_phys: int,
    ) -> int:
        if seats_rem_phys <= 0:
            return 0
        if expected_remaining_demand > seats_rem_phys * self._config.dynamic_demand_pressure_ratio:
            return 1
        return 0

    def _competitor_bucket_delta(
        self,
        our_fare: float,
        competitor_fare: float | None,
        seat_fill_ratio: float,
    ) -> int:
        if competitor_fare is None:
            return 0
        cfg = self._config
        if seat_fill_ratio > cfg.dynamic_competitor_disable_fill_ratio:
            return 0
        if cfg.competitor_response_strength <= 1e-9:
            return 0
        strength = min(1.0, max(0.05, cfg.competitor_response_strength))
        effective_threshold = cfg.competitor_match_threshold / strength
        if our_fare - competitor_fare > effective_threshold:
            return -1
        return 0

    @staticmethod
    def _note_from_adjustments(
        pace: int,
        scarcity: int,
        demand_pressure: int,
        competitor: int,
    ) -> str:
        parts = ["dyn"]
        if pace > 0:
            parts.append("pace+")
        elif pace < 0:
            parts.append("pace-")
        if scarcity > 0:
            parts.append("scar+")
        if demand_pressure > 0:
            parts.append("dmd+")
        if competitor < 0:
            parts.append("comp-")
        if len(parts) == 1:
            parts.append("neutral")
        return ":".join(parts)

