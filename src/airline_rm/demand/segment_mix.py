"""Leisure-heavy early bookings vs business-heavy close-in mix."""

from __future__ import annotations

import numpy as np

from airline_rm.types import SimulationConfig


class SegmentMixModel:
    """Smooth logistic shift in business share over ``days_until_departure``.

    Let :math:`d` be days until departure (large far out, small near departure). The business
    share is

    .. math::

        s_B(d) = s_{early} + (s_{late} - s_{early})\\,\\sigma\\big(k\\,(m - d)\\big),

    where :math:`\\sigma(z) = 1/(1+e^{-z})`, :math:`m` is ``transition_midpoint_days``,
    and :math:`k` is ``transition_steepness`` (>0).

    - For :math:`d \\gg m`, :math:`m-d \\ll 0` → :math:`\\sigma \\approx 0` → :math:`s_B \\approx s_{early}`.
    - For :math:`d \\ll m`, :math:`m-d \\gg 0` → :math:`\\sigma \\approx 1` → :math:`s_B \\approx s_{late}`.

    Thus business share **rises as departure approaches** when :math:`s_{late} > s_{early}`.
    """

    __slots__ = ("_horizon", "_early", "_late", "_midpoint", "_steepness")

    def __init__(
        self,
        booking_horizon_days: int,
        early_business_share: float,
        late_business_share: float,
        transition_midpoint_days: float,
        transition_steepness: float,
    ) -> None:
        if booking_horizon_days < 1:
            raise ValueError("booking_horizon_days must be >= 1")
        if not (0.0 < early_business_share < 1.0):
            raise ValueError("early_business_share must lie in (0, 1)")
        if not (0.0 < late_business_share < 1.0):
            raise ValueError("late_business_share must lie in (0, 1)")
        if early_business_share > late_business_share + 1e-6:
            raise ValueError("early_business_share should be <= late_business_share")
        if transition_midpoint_days <= 0:
            raise ValueError("segment_transition_midpoint_days must be positive")
        if transition_steepness <= 0:
            raise ValueError("segment_transition_steepness must be positive")

        self._horizon = int(booking_horizon_days)
        self._early = float(early_business_share)
        self._late = float(late_business_share)
        self._midpoint = float(transition_midpoint_days)
        self._steepness = float(transition_steepness)

    def business_share(self, day_to_departure: int) -> float:
        """Business share for a day with ``day_to_departure`` (:math:`d`)."""

        if not (1 <= day_to_departure <= self._horizon):
            raise ValueError(
                f"day_to_departure must be in [1, {self._horizon}], got {day_to_departure}"
            )
        d = float(day_to_departure)
        z = self._steepness * (self._midpoint - d)
        sig = 1.0 / (1.0 + float(np.exp(-z)))
        share = self._early + (self._late - self._early) * sig
        return float(min(max(share, 1e-9), 1.0 - 1e-9))

    def leisure_share(self, day_to_departure: int) -> float:
        """Leisure share = ``1 - business_share``."""

        return float(1.0 - self.business_share(day_to_departure))

    def business_shares_vector(self) -> np.ndarray:
        """Vector of business shares for simulated days ``t=1..H`` (index ``t-1``, :math:`d=H-t+1`)."""

        out = np.empty(self._horizon, dtype=float)
        for day in range(1, self._horizon + 1):
            d = self._horizon - day + 1
            out[day - 1] = self.business_share(d)
        return out

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> SegmentMixModel:
        """Instantiate segment-mix parameters from configuration."""

        return cls(
            booking_horizon_days=config.booking_horizon_days,
            early_business_share=config.early_business_share,
            late_business_share=config.late_business_share,
            transition_midpoint_days=config.segment_transition_midpoint_days,
            transition_steepness=config.segment_transition_steepness,
        )
