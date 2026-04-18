"""Operational and financial KPIs (explicit load-factor definitions)."""

from __future__ import annotations

from dataclasses import dataclass

from airline_rm.entities.simulation_state import FlightSimulationResult


@dataclass(frozen=True, slots=True)
class SimulationMetrics:
    """KPI bundle: load factors distinguish accepted bookings vs boarded bodies."""

    accepted_booking_load_factor: float
    boarded_load_factor: float
    booking_rate: float
    no_show_rate_realized: float
    denied_boarding_rate_on_showups: float
    denied_boarding_rate_on_accepted: float
    denied_boarding_cost: float
    ticket_revenue: float
    ancillary_revenue: float
    total_revenue: float
    total_cost: float
    profit: float
    bookings_accepted: int
    boarded_passengers: int
    no_shows: int
    denied_boardings: int
    bookings_business: int
    bookings_leisure: int
    sellout_day: int | None
    load_factor: float
    avg_fare: float


def compute_metrics(result: FlightSimulationResult) -> SimulationMetrics:
    """Derive KPIs from a finished simulation (post departure-day processing)."""

    phys = int(result.physical_capacity or result.flight.capacity)
    blim = int(result.booking_limit or phys)
    accepted = int(result.bookings_accepted or result.seats_sold)
    boarded = int(result.boarded_passengers)
    nosh = int(result.no_shows)
    denied = int(result.denied_boardings)

    accepted_lf = float(accepted) / float(phys) if phys > 0 else 0.0
    boarded_lf = float(boarded) / float(phys) if phys > 0 else 0.0
    booking_rate = float(accepted) / float(blim) if blim > 0 else 0.0
    ns_rate = float(nosh) / float(accepted) if accepted > 0 else 0.0
    showups = max(accepted - nosh, 0)
    denied_on_show = float(denied) / float(showups) if showups > 0 else 0.0
    denied_on_acc = float(denied) / float(accepted) if accepted > 0 else 0.0

    ticket_rev = float(result.total_ticket_revenue)
    anc_rev = float(result.total_ancillary_revenue)
    total_rev = ticket_rev + anc_rev
    total_cost = float(result.total_cost)
    profit = total_rev - total_cost
    avg_fare = ticket_rev / float(accepted) if accepted > 0 else 0.0

    return SimulationMetrics(
        accepted_booking_load_factor=accepted_lf,
        boarded_load_factor=boarded_lf,
        booking_rate=booking_rate,
        no_show_rate_realized=ns_rate,
        denied_boarding_rate_on_showups=denied_on_show,
        denied_boarding_rate_on_accepted=denied_on_acc,
        denied_boarding_cost=float(result.denied_boarding_cost),
        ticket_revenue=ticket_rev,
        ancillary_revenue=anc_rev,
        total_revenue=total_rev,
        total_cost=total_cost,
        profit=profit,
        bookings_accepted=accepted,
        boarded_passengers=boarded,
        no_shows=nosh,
        denied_boardings=denied,
        bookings_business=result.bookings_business,
        bookings_leisure=result.bookings_leisure,
        sellout_day=result.sellout_day,
        load_factor=accepted_lf,
        avg_fare=avg_fare,
    )
