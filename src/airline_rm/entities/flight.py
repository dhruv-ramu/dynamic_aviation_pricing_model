"""Flight instance metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from airline_rm.entities.route import Route


@dataclass(frozen=True, slots=True)
class Flight:
    """A single departure with capacity on a route."""

    flight_id: str
    route: Route
    departure_date: date
    capacity: int

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if not self.flight_id:
            raise ValueError("flight_id must be non-empty")
