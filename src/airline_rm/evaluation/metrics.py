"""Lightweight financial and operational KPIs."""

from __future__ import annotations

from dataclasses import dataclass

from airline_rm.entities.simulation_state import FlightSimulationResult


@dataclass(frozen=True, slots=True)
class SimulationMetrics:
    """Derived KPI bundle for reporting and tests."""

    load_factor: float
    avg_fare: float
    total_revenue: float
    total_cost: float
    profit: float
    bookings_business: int
    bookings_leisure: int
    sellout_day: int | None


def compute_metrics(result: FlightSimulationResult) -> SimulationMetrics:
    """Compute transparent KPIs from a finished simulation."""

    capacity = result.flight.capacity
    seats = result.seats_sold

    load_factor = float(seats) / float(capacity) if capacity > 0 else 0.0
    avg_fare = result.total_ticket_revenue / float(seats) if seats > 0 else 0.0
    total_revenue = result.total_ticket_revenue + result.total_ancillary_revenue

    return SimulationMetrics(
        load_factor=load_factor,
        avg_fare=avg_fare,
        total_revenue=total_revenue,
        total_cost=result.total_cost,
        profit=total_revenue - result.total_cost,
        bookings_business=result.bookings_business,
        bookings_leisure=result.bookings_leisure,
        sellout_day=result.sellout_day,
    )
