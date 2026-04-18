"""Time-varying booking intensity over the sales horizon."""

from __future__ import annotations

from typing import Literal

import numpy as np

from airline_rm.types import SimulationConfig

BookingCurveType = Literal["logistic"]


class BookingCurveModel:
    """Logistic booking-intensity curve over ``days_until_departure``.

    For each calendar sales day we use ``days_until_departure`` :math:`d \\in \\{1,\\dots,H\\}`
    where :math:`H` is ``booking_horizon_days``. The *first* simulated day corresponds to
    :math:`d=H` (far from departure) and the *last* day to :math:`d=1` (close to departure).

    **Raw intensity** (un-normalized, positive) follows a logistic in :math:`d`:

    .. math::

        r(d) = \\varepsilon + \\frac{1}{1 + \\exp\\big(-k\\,(m - d)\\big)}

    - :math:`m` is ``midpoint`` (days until departure where intensity ramps most sharply).
    - :math:`k > 0` is ``steepness``.
    - When :math:`d \\ll m`, the exponent is large negative → sigmoid ≈ 0 → *low* intensity
      (early bookings, far out).
    - When :math:`d \\gg m` is not possible for :math:`d \\le H`; as :math:`d` *decreases* toward
      departure (smaller :math:`d`), :math:`(m-d)` becomes more positive → sigmoid → *higher*
      intensity. So intensity **rises as departure approaches**, matching typical short-haul
      booking pace.

    **Daily weights** for simulated days :math:`t=1,\\dots,H` (with :math:`d = H-t+1`) are

    .. math::

        w_t = \\frac{r(d)}{\\sum_{u=1}^{H} r(H-u+1)}.

    Hence :math:`\\sum_t w_t = 1` and every :math:`w_t > 0` (because of :math:`\\varepsilon`).
    """

    __slots__ = ("_horizon", "_curve_type", "_steepness", "_midpoint", "_floor", "_weights")

    def __init__(
        self,
        booking_horizon_days: int,
        curve_type: BookingCurveType,
        steepness: float,
        midpoint: float,
        *,
        floor: float = 1e-6,
    ) -> None:
        if booking_horizon_days < 1:
            raise ValueError("booking_horizon_days must be >= 1")
        if curve_type != "logistic":
            raise ValueError(f"Unsupported booking_curve_type: {curve_type!r}")
        if steepness <= 0:
            raise ValueError("booking_curve_steepness must be positive")
        if midpoint <= 0:
            raise ValueError("booking_curve_midpoint must be positive")
        if floor <= 0:
            raise ValueError("floor must be positive")

        self._horizon = int(booking_horizon_days)
        self._curve_type: BookingCurveType = curve_type
        self._steepness = float(steepness)
        self._midpoint = float(midpoint)
        self._floor = float(floor)
        self._weights = self._compute_daily_weights()

    @property
    def booking_horizon_days(self) -> int:
        return self._horizon

    def _raw_intensity(self, days_until_departure: int) -> float:
        d = float(days_until_departure)
        z = self._steepness * (self._midpoint - d)
        return self._floor + 1.0 / (1.0 + float(np.exp(-z)))

    def _compute_daily_weights(self) -> np.ndarray:
        weights = np.empty(self._horizon, dtype=float)
        for day in range(1, self._horizon + 1):
            d = self._horizon - day + 1
            weights[day - 1] = self._raw_intensity(d)
        total = float(weights.sum())
        if total <= 0:
            raise ValueError("Booking curve produced a non-positive weight sum")
        weights /= total
        return weights

    def daily_weights(self) -> np.ndarray:
        """Return shape ``(H,)`` weights for simulated days ``t=1..H`` (index ``t-1``)."""

        return self._weights.copy()

    def incremental_share(self, day_to_departure: int) -> float:
        """Incremental share on the day identified by ``day_to_departure`` (:math:`d`)."""

        if not (1 <= day_to_departure <= self._horizon):
            raise ValueError(
                f"day_to_departure must be in [1, {self._horizon}], got {day_to_departure}"
            )
        sim_day = self._horizon - day_to_departure + 1
        return float(self._weights[sim_day - 1])

    def cumulative_share(self, day_to_departure: int) -> float:
        """Cumulative share from :math:`d'=H` down through ``day_to_departure`` inclusive."""

        if not (1 <= day_to_departure <= self._horizon):
            raise ValueError(
                f"day_to_departure must be in [1, {self._horizon}], got {day_to_departure}"
            )
        total = 0.0
        for d_prime in range(self._horizon, day_to_departure - 1, -1):
            total += self.incremental_share(d_prime)
        return float(total)

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> BookingCurveModel:
        """Instantiate from :class:`~airline_rm.types.SimulationConfig` booking-curve fields."""

        return cls(
            booking_horizon_days=config.booking_horizon_days,
            curve_type=config.booking_curve_type,
            steepness=config.booking_curve_steepness,
            midpoint=config.booking_curve_midpoint,
        )
