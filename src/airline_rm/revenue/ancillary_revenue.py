"""Ancillary revenue helpers (flat mean per accepted booking in the current engine)."""

from __future__ import annotations


def total_ancillary_from_bookings(n_accepted: int, ancillary_mean: float) -> float:
    """Deterministic ancillary total when each accepted passenger pays ``ancillary_mean``."""

    if n_accepted < 0 or ancillary_mean < 0:
        raise ValueError("n_accepted and ancillary_mean must be non-negative")
    return float(n_accepted) * float(ancillary_mean)
