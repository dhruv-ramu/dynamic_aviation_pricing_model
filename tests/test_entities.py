"""Tests for core entity construction and validation."""

from __future__ import annotations

from datetime import date

import pytest

from airline_rm.entities.booking_request import BookingRequest
from airline_rm.entities.flight import Flight
from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.entities.route import Route


def test_route_and_flight() -> None:
    route = Route(origin="SEA", destination="SFO", distance_miles=450.0)
    flight = Flight(
        flight_id="TEST1",
        route=route,
        departure_date=date(2026, 6, 1),
        capacity=180,
    )
    assert flight.route.distance_miles == 450.0


def test_route_rejects_nonpositive_distance() -> None:
    with pytest.raises(ValueError):
        Route(origin="SEA", destination="SFO", distance_miles=0.0)


def test_booking_request_fields() -> None:
    req = BookingRequest(
        days_until_departure=30,
        segment=PassengerSegment.LEISURE,
        offered_fare=139.0,
    )
    assert req.segment is PassengerSegment.LEISURE
