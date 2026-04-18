"""Ticket revenue recognition (booking-time cash; refunds not modeled in Phase 4)."""

from __future__ import annotations

from typing import Sequence


def total_ticket_revenue_from_bookings(accepted_fares: Sequence[float]) -> float:
    """Sum of quoted fares for accepted bookings (simple cash-at-booking view)."""

    return float(sum(accepted_fares))
