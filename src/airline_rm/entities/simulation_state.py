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
    current_bucket_index: int = 0
    dynamic_last_bucket_change_day: int = 0
    last_quoted_fare: float | None = None
    booking_pace_gap: float = 0.0
    fare_history: list[tuple[int, float, float | None]] = field(default_factory=list)
    booking_limit: int = 0

    @property
    def seats_remaining(self) -> int:
        """Remaining booking authorizations (respects overbooking limit when set)."""

        limit = self.booking_limit if self.booking_limit > 0 else self.flight.capacity
        return max(0, limit - self.seats_sold)


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
    fare_series: tuple[float, ...] = ()
    physical_capacity: int = 0
    booking_limit: int = 0
    bookings_accepted: int = 0
    boarded_passengers: int = 0
    no_shows: int = 0
    denied_boardings: int = 0
    denied_boarding_cost: float = 0.0
