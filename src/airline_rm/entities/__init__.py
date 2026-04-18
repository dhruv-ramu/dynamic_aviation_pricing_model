"""Domain entities for routes, flights, and booking flow."""

from airline_rm.entities.booking_request import BookingRequest
from airline_rm.entities.flight import Flight
from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.entities.route import Route
from airline_rm.entities.simulation_state import FlightSimulationResult, SimulationState

__all__ = [
    "BookingRequest",
    "Flight",
    "FlightSimulationResult",
    "PassengerSegment",
    "Route",
    "SimulationState",
]
