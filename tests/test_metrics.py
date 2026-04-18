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
    )
    m = compute_metrics(result)

    assert m.total_revenue == result.total_ticket_revenue + result.total_ancillary_revenue
    assert m.profit == m.total_revenue - m.total_cost
    assert m.load_factor == 0.5
    assert m.avg_fare == 100.0
    assert m.bookings_business == 20
    assert m.bookings_leisure == 30
    assert m.sellout_day == 9
