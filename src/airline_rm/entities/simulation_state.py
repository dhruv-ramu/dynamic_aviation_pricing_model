"""Mutable simulation state and terminal result envelope."""

from __future__ import annotations

from dataclasses import dataclass, field

from airline_rm.entities.booking_request import BookingRequest
from airline_rm.entities.flight import Flight


@dataclass(slots=True)
class SimulationState:
    """Working state for a single-flight simulation."""

    flight: Flight
    day_index: int = 0
    seats_sold: int = 0
    total_ticket_revenue: float = 0.0
    total_ancillary_revenue: float = 0.0
    accepted_bookings: list[BookingRequest] = field(default_factory=list)
    bookings_business: int = 0
    bookings_leisure: int = 0
    rejected_due_to_price: int = 0
    rejected_due_to_capacity: int = 0
    sellout_day: int | None = None

    @property
    def seats_remaining(self) -> int:
        return max(self.flight.capacity - self.seats_sold, 0)


@dataclass(frozen=True, slots=True)
class FlightSimulationResult:
    """Aggregated outputs after a simulation episode completes."""

    flight: Flight
    booking_horizon_days: int
    seats_sold: int
    total_ticket_revenue: float
    total_ancillary_revenue: float
    total_cost: float
    bookings_business: int = 0
    bookings_leisure: int = 0
    rejected_due_to_price: int = 0
    rejected_due_to_capacity: int = 0
    sellout_day: int | None = None
