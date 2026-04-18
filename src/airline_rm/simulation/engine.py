"""Single-flight simulation engine with modular stochastic demand."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from airline_rm.demand.arrivals import DailyArrivalModel
from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.demand.conversion import BookingConverter
from airline_rm.demand.segment_mix import SegmentMixModel
from airline_rm.demand.willingness_to_pay import WTPModel
from airline_rm.entities.booking_request import BookingRequest
from airline_rm.entities.flight import Flight
from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.entities.route import Route
from airline_rm.entities.simulation_state import FlightSimulationResult, SimulationState
from airline_rm.pricing.pricing_policy_base import PricingPolicy
from airline_rm.types import SimulationConfig


def _build_flight(config: SimulationConfig) -> Flight:
    route = Route(
        origin=config.route_origin,
        destination=config.route_destination,
        distance_miles=float(config.route_distance_miles),
    )
    departure = date.today() + timedelta(days=config.booking_horizon_days)
    return Flight(
        flight_id=f"{route.origin}-{route.destination}-001",
        route=route,
        departure_date=departure,
        capacity=int(config.capacity),
    )


def _variable_operating_cost(config: SimulationConfig, seats_sold: int) -> float:
    """Seat-mile variable cost for sold seats (transparent placeholder)."""

    seat_miles = float(config.route_distance_miles) * float(seats_sold)
    return float(config.casm_ex) * seat_miles


def run_single_flight_simulation(
    config: SimulationConfig,
    policy: PricingPolicy,
    rng: np.random.Generator,
) -> FlightSimulationResult:
    """Simulate bookings day-by-day using the demand subsystem (curve, arrivals, WTP, conversion)."""

    flight = _build_flight(config)
    state = SimulationState(flight=flight)

    booking_curve = BookingCurveModel.from_simulation_config(config)
    arrivals = DailyArrivalModel.from_simulation_config(config, booking_curve)
    segment_mix = SegmentMixModel.from_simulation_config(config)
    wtp_model = WTPModel.from_simulation_config(config)
    converter = BookingConverter()

    for day in range(1, config.booking_horizon_days + 1):
        state.day_index = day
        days_until_departure = config.booking_horizon_days - day + 1
        fare = policy.quote_fare(days_until_departure, state)

        day_index_zero_based = day - 1
        n_arrivals = arrivals.sample_arrivals_for_day(day_index_zero_based, rng)

        for _ in range(n_arrivals):
            p_business = segment_mix.business_share(days_until_departure)
            segment = PassengerSegment.BUSINESS if rng.random() < p_business else PassengerSegment.LEISURE

            wtp = wtp_model.sample_wtp(segment, rng)

            if not converter.will_book(fare, wtp):
                state.rejected_due_to_price += 1
                continue

            if state.seats_remaining <= 0:
                state.rejected_due_to_capacity += 1
                continue

            request = BookingRequest(
                days_until_departure=days_until_departure,
                segment=segment,
                offered_fare=fare,
            )

            state.seats_sold += 1
            state.total_ticket_revenue += fare
            state.total_ancillary_revenue += float(config.ancillary_mean)
            state.accepted_bookings.append(request)

            if segment is PassengerSegment.BUSINESS:
                state.bookings_business += 1
            else:
                state.bookings_leisure += 1

            if state.seats_sold >= state.flight.capacity and state.sellout_day is None:
                state.sellout_day = day

    total_cost = float(config.fixed_flight_cost) + _variable_operating_cost(config, state.seats_sold)

    return FlightSimulationResult(
        flight=flight,
        booking_horizon_days=int(config.booking_horizon_days),
        seats_sold=state.seats_sold,
        total_ticket_revenue=state.total_ticket_revenue,
        total_ancillary_revenue=state.total_ancillary_revenue,
        total_cost=total_cost,
        bookings_business=state.bookings_business,
        bookings_leisure=state.bookings_leisure,
        rejected_due_to_price=state.rejected_due_to_price,
        rejected_due_to_capacity=state.rejected_due_to_capacity,
        sellout_day=state.sellout_day,
    )
