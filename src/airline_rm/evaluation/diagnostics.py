"""Lightweight diagnostics for simulation outputs (text-friendly summaries)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from airline_rm.entities.simulation_state import FlightSimulationResult


def summarize_accepted_segment_mix(
    results: Sequence[FlightSimulationResult],
) -> dict[str, float]:
    """Aggregate accepted booking segment counts and shares across simulation runs.

    ``business_share_of_accepted`` for each run is ``bookings_business / (biz + leisure)``
    when the denominator is positive; otherwise 0.0 for that run.
    """

    if not results:
        raise ValueError("results must be non-empty")

    biz = np.array([r.bookings_business for r in results], dtype=float)
    lei = np.array([r.bookings_leisure for r in results], dtype=float)
    total = biz + lei
    share_biz = np.divide(biz, total, out=np.zeros_like(biz), where=total > 0)

    return {
        "mean_accepted_business": float(np.mean(biz)),
        "mean_accepted_leisure": float(np.mean(lei)),
        "mean_business_share_of_accepted": float(np.mean(share_biz)),
        "mean_leisure_share_of_accepted": float(np.mean(1.0 - share_biz)),
    }
