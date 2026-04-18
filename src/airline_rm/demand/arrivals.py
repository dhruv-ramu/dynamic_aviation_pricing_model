"""Stochastic (or deterministic) daily shopper arrivals."""

from __future__ import annotations

import numpy as np

from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.types import SimulationConfig


class DailyArrivalModel:
    """Non-homogeneous Poisson arrivals scaled by a booking curve.

    For simulated day index ``t \\in \\{0,\\dots,H-1\\}`` (day ``t+1`` of sales), let
    :math:`w_t` be the booking-curve weight with :math:`\\sum_t w_t = 1`. Expected arrivals are

    .. math::

        \\lambda_t = \\texttt{expected\\_total\\_demand}
            \\times \\texttt{demand\\_multiplier} \\times w_t.

    Stochastic mode draws :math:`N_t \\sim \\mathrm{Poisson}(\\lambda_t)`.

    Deterministic mode (``stochastic=False``) sets
    :math:`N_t = \\max(0, \\mathrm{round}(\\lambda_t))` for tests and reproducible sanity checks.
    """

    __slots__ = (
        "_horizon",
        "_expected_total",
        "_multiplier",
        "_weights",
        "_stochastic",
        "_expected_by_day",
    )

    def __init__(
        self,
        booking_horizon_days: int,
        expected_total_demand: float,
        demand_multiplier: float,
        booking_curve: BookingCurveModel,
        *,
        stochastic: bool = True,
    ) -> None:
        if booking_horizon_days < 1:
            raise ValueError("booking_horizon_days must be >= 1")
        if expected_total_demand < 0:
            raise ValueError("expected_total_demand must be non-negative")
        if demand_multiplier < 0:
            raise ValueError("demand_multiplier must be non-negative")

        weights = booking_curve.daily_weights()
        if weights.shape[0] != booking_horizon_days:
            raise ValueError("Booking curve horizon does not match booking_horizon_days")

        self._horizon = int(booking_horizon_days)
        self._expected_total = float(expected_total_demand)
        self._multiplier = float(demand_multiplier)
        self._weights = weights.astype(float, copy=False)
        self._stochastic = bool(stochastic)
        self._expected_by_day = self._expected_total * self._multiplier * self._weights
        if np.any(self._expected_by_day < 0):
            raise ValueError("Computed expected arrivals are negative")

    def expected_arrivals_by_day(self) -> np.ndarray:
        """Shape ``(H,)`` expected Poisson means :math:`\\lambda_t` for ``t=0..H-1``."""

        return self._expected_by_day.copy()

    def sample_arrivals_for_day(self, day_index: int, rng: np.random.Generator) -> int:
        """Return arrivals for simulated sales-day index ``day_index`` (0-based)."""

        if not (0 <= day_index < self._horizon):
            raise ValueError(f"day_index must be in [0, {self._horizon - 1}], got {day_index}")

        lam = float(self._expected_by_day[day_index])
        if lam < 0:
            raise ValueError("Negative Poisson mean")

        if self._stochastic:
            return int(rng.poisson(lam))
        return int(max(round(lam), 0))

    @classmethod
    def from_simulation_config(
        cls,
        config: SimulationConfig,
        booking_curve: BookingCurveModel,
    ) -> DailyArrivalModel:
        """Build arrival intensities from a :class:`~airline_rm.types.SimulationConfig`."""

        return cls(
            booking_horizon_days=config.booking_horizon_days,
            expected_total_demand=float(config.expected_total_demand),
            demand_multiplier=float(config.demand_multiplier),
            booking_curve=booking_curve,
            stochastic=bool(config.demand_stochastic),
        )
