"""Stateful dynamic pricing: pace, scarcity, and demand-pressure scores; weak competitor nudge."""

from __future__ import annotations

import logging

from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.entities.simulation_state import SimulationState
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.types import SimulationConfig

logger = logging.getLogger(__name__)

_PACE_EPS = 1e-6
_SEATS_EPS = 0.5


class DynamicPricingPolicy(PricingPolicy):
    """Bucket carries over day-to-day; each day moves a bounded step from compact weighted scores."""

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._buckets = FareBucketSystem.from_values(config.fare_buckets)
        self._curve = BookingCurveModel.from_simulation_config(config)

    def _total_expected_demand(self) -> float:
        return float(self._config.expected_total_demand * self._config.demand_multiplier)

    def _initial_bucket(self) -> int:
        cfg = self._config
        if cfg.dynamic_initial_bucket_index is not None:
            return self._buckets.clamp_bucket_index(int(cfg.dynamic_initial_bucket_index))
        # Default: start one step below the most expensive bucket (profit-oriented, not mid-ladder).
        mx = self._buckets.max_bucket()
        return self._buckets.clamp_bucket_index(mx - 1 if mx >= 1 else mx)

    def _base_bucket(self, state: SimulationState) -> int:
        """Yesterday's bucket once sales have started; otherwise configured or middle bucket."""

        if not state.fare_history:
            return self._initial_bucket()
        return self._buckets.clamp_bucket_index(int(state.current_bucket_index))

    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        cfg = self._config
        cap = int(state.flight.capacity)
        sold = int(state.seats_sold)
        phys_sold = min(sold, cap) if cap > 0 else 0
        phys_rem = max(0.0, float(cap - phys_sold))

        cum = float(self._curve.cumulative_share(days_until_departure))
        total_int = self._total_expected_demand()
        expected_cum = cum * total_int
        pace_gap = float(sold - expected_cum)
        pace_ratio = float(sold / max(expected_cum, _PACE_EPS))
        seat_fill = float(phys_sold / float(cap)) if cap > 0 else 0.0

        expected_remaining = (1.0 - cum) * total_int

        pace_score = self._pace_score(
            pace_ratio,
            pace_gap,
            expected_cum,
            days_until_departure,
        )
        scarcity_score = self._scarcity_score(seat_fill)
        demand_score, demand_ratio = self._demand_pressure_score(expected_remaining, phys_rem)

        base = self._base_bucket(state)
        our_fare = self._buckets.current_fare(base)

        competitor_score = self._competitor_score(
            our_fare,
            competitor_fare,
            seat_fill,
            days_until_departure,
            pace_ratio,
        )

        # Competitor is excluded from core_net so it cannot dominate; at most one bucket down via comp_bucket.
        core_net = (
            cfg.dynamic_weight_pace * pace_score
            + cfg.dynamic_weight_scarcity * scarcity_score
            + cfg.dynamic_weight_demand_pressure * demand_score
        )

        strong_for_move = (
            pace_ratio >= cfg.dynamic_two_step_pace_ratio
            or seat_fill >= cfg.dynamic_two_step_scarcity_fill
            or demand_score >= cfg.dynamic_two_step_demand_score
        )

        if abs(core_net) < cfg.dynamic_bucket_change_deadband:
            core_move = 0
        elif core_net >= cfg.dynamic_score_strong_raise:
            if cfg.dynamic_strong_raise_allows_two_steps and strong_for_move:
                core_move = 2
            else:
                core_move = 1
        elif core_net >= cfg.dynamic_score_mild_raise:
            core_move = 1
        elif core_net <= cfg.dynamic_score_strong_lower:
            core_move = -1
        else:
            core_move = 0

        if cfg.dynamic_min_days_between_bucket_changes > 0 and state.dynamic_last_bucket_change_day > 0:
            gap_days = state.day_index - state.dynamic_last_bucket_change_day
            if gap_days < cfg.dynamic_min_days_between_bucket_changes and not strong_for_move:
                core_move = 0

        if days_until_departure <= cfg.late_window_days and core_move < 0:
            core_move = 0

        comp_bucket = self._competitor_bucket_step(
            our_fare,
            competitor_fare,
            seat_fill,
            days_until_departure,
            pace_ratio,
        )

        max_up = 2 if cfg.dynamic_strong_raise_allows_two_steps and strong_for_move else 1
        combined = core_move + comp_bucket
        combined = max(-1, min(max_up, combined))
        raw_idx = base + combined
        new_idx = self._buckets.clamp_bucket_index(raw_idx)

        if days_until_departure <= cfg.dynamic_late_floor_days_until_departure:
            new_idx = max(new_idx, cfg.dynamic_min_bucket_index_late)
        if days_until_departure <= cfg.late_window_days:
            new_idx = max(new_idx, cfg.dynamic_late_window_min_bucket_index)
        new_idx = self._buckets.clamp_bucket_index(new_idx)
        fare = self._buckets.current_fare(new_idx)

        note = self._reason_note(core_move, comp_bucket, core_net, strong_for_move)

        diagnostics: tuple[tuple[str, str | float | int], ...] | None = None
        if cfg.dynamic_policy_debug:
            diagnostics = (
                ("base_bucket", base),
                ("new_bucket", new_idx),
                ("pace_score", round(pace_score, 4)),
                ("scarcity_score", round(scarcity_score, 4)),
                ("demand_pressure_score", round(demand_score, 4)),
                ("demand_pressure_ratio", round(demand_ratio, 4)),
                ("competitor_score", round(competitor_score, 4)),
                ("core_net", round(core_net, 4)),
                ("core_move", core_move),
                ("comp_bucket", comp_bucket),
                ("combined_move", combined),
                ("note", note),
            )
            logger.info("dynamic_policy %s", dict(diagnostics))

        return PricingAction(bucket_index=new_idx, fare=fare, note=note, diagnostics=diagnostics)

    def _pace_score(
        self,
        pace_ratio: float,
        pace_gap: float,
        expected_cum: float,
        days_until_departure: int,
    ) -> float:
        cfg = self._config
        denom = max(expected_cum, _PACE_EPS)
        g_rel = pace_gap / denom
        r_ex = pace_ratio - 1.0
        raw = r_ex * 2.75 + max(-1.25, min(1.25, g_rel)) * 0.85
        if raw < 0.0:
            horizon = max(1, cfg.booking_horizon_days)
            rel = min(1.0, float(days_until_departure) / float(horizon))
            damp = cfg.dynamic_pace_late_dampen + (1.0 - cfg.dynamic_pace_late_dampen) * rel
            raw *= damp
        return float(max(-1.65, min(2.05, raw)))

    def _scarcity_score(self, seat_fill: float) -> float:
        cfg = self._config
        t1 = cfg.dynamic_scarcity_fill_ratio_1
        t2 = cfg.dynamic_scarcity_fill_ratio_2
        if seat_fill <= t1:
            return 0.0
        if seat_fill <= t2:
            span = max(t2 - t1, _PACE_EPS)
            return float(((seat_fill - t1) / span) * 1.12)
        span = max(1.0 - t2, _PACE_EPS)
        return float(1.12 + ((seat_fill - t2) / span) * 1.08)

    def _demand_pressure_score(
        self,
        expected_remaining: float,
        phys_rem: float,
    ) -> tuple[float, float]:
        cfg = self._config
        denom = max(float(phys_rem), _SEATS_EPS)
        ratio = float(expected_remaining / denom)
        excess = ratio - cfg.dynamic_demand_pressure_neutral_ratio
        if excess <= 0.0:
            return 0.0, ratio
        raw = excess * cfg.dynamic_demand_ratio_score_scale * 1.18
        return float(min(2.0, max(0.0, raw))), ratio

    def _competitor_score(
        self,
        our_fare: float,
        competitor_fare: float | None,
        seat_fill: float,
        days_until_departure: int,
        pace_ratio: float,
    ) -> float:
        if competitor_fare is None:
            return 0.0
        cfg = self._config
        if seat_fill >= cfg.dynamic_competitor_disable_fill_ratio:
            return 0.0
        if days_until_departure <= cfg.dynamic_competitor_late_ignore_days:
            if seat_fill > cfg.dynamic_scarcity_fill_ratio_1:
                return 0.0
        if cfg.dynamic_competitor_ignore_if_ahead_of_pace and pace_ratio > 1.01:
            return 0.0
        if cfg.competitor_response_strength <= 1e-9:
            return 0.0
        strength = min(1.0, max(0.06, cfg.competitor_response_strength))
        eff = cfg.competitor_match_threshold / strength
        if our_fare - competitor_fare > eff:
            return -0.42
        return 0.0

    def _competitor_bucket_step(
        self,
        our_fare: float,
        competitor_fare: float | None,
        seat_fill: float,
        days_until_departure: int,
        pace_ratio: float,
    ) -> int:
        if days_until_departure <= self._config.late_window_days:
            return 0
        if self._competitor_score(
            our_fare,
            competitor_fare,
            seat_fill,
            days_until_departure,
            pace_ratio,
        ) < -0.01:
            return -1
        return 0

    @staticmethod
    def _reason_note(core_move: int, comp_bucket: int, core_net: float, strong: bool) -> str:
        parts = ["dyn"]
        if core_move > 0:
            parts.append(f"up{core_move}" + ("*" if strong and core_move > 1 else ""))
        elif core_move < 0:
            parts.append("down1")
        if comp_bucket < 0:
            parts.append("comp-")
        if core_move == 0 and comp_bucket == 0:
            if abs(core_net) < 1e-9:
                parts.append("hold0")
            else:
                parts.append("hold")
        return ":".join(parts)


__all__ = ["DynamicPricingPolicy"]
