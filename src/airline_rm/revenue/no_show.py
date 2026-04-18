"""Departure-day no-show realization (Binomial)."""

from __future__ import annotations

import numpy as np

from airline_rm.types import SimulationConfig


class NoShowModel:
    """Independent Bernoulli no-shows aggregated as a Binomial draw per flight."""

    __slots__ = ("_p",)

    def __init__(self, no_show_probability: float) -> None:
        if not (0.0 <= no_show_probability <= 1.0):
            raise ValueError("no_show_probability must lie in [0, 1]")
        self._p = float(no_show_probability)

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> NoShowModel:
        return cls(float(config.no_show_mean))

    def sample_no_shows(self, booked_count: int, rng: np.random.Generator) -> int:
        """Draw the number of passengers who booked but do not show (Binomial)."""

        if booked_count < 0:
            raise ValueError("booked_count must be non-negative")
        if booked_count == 0:
            return 0
        return int(rng.binomial(booked_count, self._p))

    def boarded_count(self, booked_count: int, rng: np.random.Generator) -> int:
        """Passengers who show up at the gate (one independent Binomial draw)."""

        if booked_count < 0:
            raise ValueError("booked_count must be non-negative")
        if booked_count == 0:
            return 0
        return booked_count - int(rng.binomial(booked_count, self._p))
