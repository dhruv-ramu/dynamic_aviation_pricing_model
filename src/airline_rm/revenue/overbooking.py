"""Booking limit vs physical cabin capacity (fixed overbooking margin only)."""

from __future__ import annotations

import math

from airline_rm.types import SimulationConfig


class OverbookingModel:
    """Compute maximum accepted bookings relative to physical seats."""

    __slots__ = ("_enabled", "_limit_pct")

    def __init__(self, *, enabled: bool, limit_pct: float) -> None:
        if limit_pct < 0:
            raise ValueError("overbooking_limit_pct must be non-negative")
        self._enabled = bool(enabled)
        self._limit_pct = float(limit_pct)

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> OverbookingModel:
        return cls(enabled=bool(config.overbooking_enabled), limit_pct=float(config.overbooking_limit_pct))

    def booking_limit(self, physical_capacity: int) -> int:
        """Maximum accepted bookings (physical seats plus optional overbook pool)."""

        if physical_capacity <= 0:
            raise ValueError("physical_capacity must be positive")
        if not self._enabled:
            return physical_capacity
        extra = int(math.floor(physical_capacity * self._limit_pct))
        return physical_capacity + max(0, extra)

    def allowed_to_accept_more(self, booked_count: int, booking_limit: int) -> bool:
        """Return True iff another booking may still be accepted."""

        if booked_count < 0 or booking_limit < 0:
            raise ValueError("counts must be non-negative")
        return booked_count < booking_limit
