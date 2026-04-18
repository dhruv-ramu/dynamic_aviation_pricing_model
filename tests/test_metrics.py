"""Tests for KPI calculations."""

from __future__ import annotations

from datetime import date

from airline_rm.entities.flight import Flight
from airline_rm.entities.route import Route
from airline_rm.entities.simulation_state import FlightSimulationResult
from airline_rm.evaluation.metrics import compute_metrics


def test_metrics_internal_consistency() -> None:
    route = Route("SEA", "SFO", 450.0)
    flight = Flight("X", route, date(2026, 1, 1), capacity=100)
    result = FlightSimulationResult(
        flight=flight,
        booking_horizon_days=10,
        seats_sold=50,
        total_ticket_revenue=5000.0,
        total_ancillary_revenue=1000.0,
        total_cost=4000.0,
        bookings_business=20,
        bookings_leisure=30,
        sellout_day=9,
        physical_capacity=100,
        booking_limit=100,
        bookings_accepted=50,
        boarded_passengers=48,
        no_shows=2,
        denied_boardings=0,
        denied_boarding_cost=0.0,
    )
    m = compute_metrics(result)

    assert m.ticket_revenue == result.total_ticket_revenue
    assert m.ancillary_revenue == result.total_ancillary_revenue
    assert m.total_revenue == m.ticket_revenue + m.ancillary_revenue
    assert m.profit == m.total_revenue - m.total_cost
    assert m.accepted_booking_load_factor == 0.5
    assert m.boarded_load_factor == 0.48
    assert m.no_show_rate_realized == 2.0 / 50.0
    assert m.avg_fare == 100.0
    assert m.bookings_business == 20
    assert m.bookings_leisure == 30
    assert m.sellout_day == 9
    assert m.load_factor == m.accepted_booking_load_factor
