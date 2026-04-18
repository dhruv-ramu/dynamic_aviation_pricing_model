"""Lightweight competitor fare signals (not a game-theoretic model)."""

from __future__ import annotations

import numpy as np

from airline_rm.types import SimulationConfig


class CompetitorPricingModel:
    """Generate a daily competitor fare under ``competitor_mode``.

    Modes:

    - **none**: no competitor signal (returns ``None``).
    - **static**: anchor near ``base_fare + competitor_base_offset`` plus Gaussian noise.
    - **reactive**: anchor drifts with time-to-departure and is pulled toward ``our_fare`` when provided.

    All modes are **seed-driven** through the injected ``rng``.
    """

    __slots__ = (
        "_mode",
        "_horizon",
        "_base_fare",
        "_offset",
        "_noise_std",
        "_response_strength",
    )

    def __init__(self, config: SimulationConfig) -> None:
        self._mode = str(config.competitor_mode).strip().lower()
        self._horizon = max(int(config.booking_horizon_days), 1)
        self._base_fare = float(config.base_fare)
        self._offset = float(config.competitor_base_offset)
        self._noise_std = max(float(config.competitor_noise_std), 0.0)
        self._response_strength = float(config.competitor_response_strength)

    def competitor_fare(
        self,
        days_until_departure: int,
        our_fare: float | None,
        rng: np.random.Generator,
    ) -> float | None:
        """Return today's competitor fare (USD) or ``None`` if disabled."""

        if self._mode == "none":
            return None
        if self._mode not in {"static", "reactive"}:
            raise ValueError(
                f"Unsupported competitor_mode: {self._mode!r} (expected none, static, reactive)"
            )

        if not (1 <= days_until_departure <= self._horizon):
            raise ValueError(
                f"days_until_departure must be in [1, {self._horizon}], got {days_until_departure}"
            )

        time_tilt = 25.0 * (1.0 - float(days_until_departure) / float(self._horizon))
        anchor = self._base_fare + self._offset + time_tilt

        if self._mode == "reactive" and our_fare is not None:
            anchor += self._response_strength * (float(our_fare) - anchor)

        noise = float(rng.normal(0.0, self._noise_std)) if self._noise_std > 0 else 0.0
        return float(max(30.0, anchor + noise))
