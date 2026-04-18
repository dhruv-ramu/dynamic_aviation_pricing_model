"""Booking attempt representation."""

from __future__ import annotations

from dataclasses import dataclass

from airline_rm.entities.passenger_segment import PassengerSegment


@dataclass(slots=True)
class BookingRequest:
    """A single booking attempt prior to acceptance."""

    days_until_departure: int
    segment: PassengerSegment
    offered_fare: float
