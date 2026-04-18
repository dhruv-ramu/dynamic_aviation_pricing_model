"""Single-flight simulation engine with demand, pricing, and departure-day outcomes."""

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
from airline_rm.pricing.competitor_response import CompetitorPricingModel
from airline_rm.pricing.pricing_policy_base import PricingPolicy
from airline_rm.revenue.denied_boarding_cost import DeniedBoardingCostModel
from airline_rm.revenue.no_show import NoShowModel
from airline_rm.revenue.overbooking import OverbookingModel
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


def _variable_operating_cost_for_boarded(config: SimulationConfig, boarded_passengers: int) -> float:
    """Seat-mile variable cost for passengers who actually fly."""

    seat_miles = float(config.route_distance_miles) * float(boarded_passengers)
    return float(config.casm_ex) * seat_miles


def _departure_day_outcomes(
    config: SimulationConfig,
    rng: np.random.Generator,
    physical_capacity: int,
    booked: int,
    ticket_revenue: float,
) -> tuple[int, int, int, int, float, float]:
    """Return (no_shows, show_ups, boarded, denied, denied_cost, variable_cost)."""

    no_show_model = NoShowModel.from_simulation_config(config)
    no_shows = no_show_model.sample_no_shows(booked, rng)
    show_ups = booked - no_shows

    denied_model = DeniedBoardingCostModel.from_simulation_config(config)
    denied = denied_model.compute_denied_boardings(show_ups, physical_capacity)
    boarded = min(show_ups, physical_capacity)

    ref_fare = float(ticket_revenue / booked) if booked > 0 else float(config.base_fare)
    denied_cost = denied_model.compute_denied_boarding_cost(denied, ref_fare)
    variable_cost = _variable_operating_cost_for_boarded(config, boarded)
    return no_shows, show_ups, boarded, denied, denied_cost, variable_cost


def run_single_flight_simulation(
    config: SimulationConfig,
    policy: PricingPolicy,
    rng: np.random.Generator,
) -> FlightSimulationResult:
    """Simulate sales through the horizon, then realize no-shows, denied boardings, and costs."""

    flight = _build_flight(config)
    physical_capacity = int(flight.capacity)
    overbooking = OverbookingModel.from_simulation_config(config)
    booking_limit = overbooking.booking_limit(physical_capacity)

    state = SimulationState(flight=flight, booking_limit=booking_limit)

    booking_curve = BookingCurveModel.from_simulation_config(config)
    arrivals = DailyArrivalModel.from_simulation_config(config, booking_curve)
    segment_mix = SegmentMixModel.from_simulation_config(config)
    wtp_model = WTPModel.from_simulation_config(config)
    converter = BookingConverter()
    competitor = CompetitorPricingModel(config)

    total_intensity = float(config.expected_total_demand * config.demand_multiplier)

    for day in range(1, config.booking_horizon_days + 1):
        state.day_index = day
        days_until_departure = config.booking_horizon_days - day + 1

        expected_sold = min(
            physical_capacity,
            total_intensity * booking_curve.cumulative_share(days_until_departure),
        )
        state.booking_pace_gap = float(state.seats_sold - expected_sold)

        comp_fare = competitor.competitor_fare(days_until_departure, state.last_quoted_fare, rng)
        prev_bucket = state.current_bucket_index
        action = policy.decide(days_until_departure, state, competitor_fare=comp_fare)
        fare = action.fare
        if action.bucket_index != prev_bucket:
            state.dynamic_last_bucket_change_day = day
        state.current_bucket_index = action.bucket_index
        state.fare_history.append((day, fare, comp_fare))

        day_index_zero_based = day - 1
        n_arrivals = arrivals.sample_arrivals_for_day(day_index_zero_based, rng)

        for _ in range(n_arrivals):
            p_business = segment_mix.business_share(days_until_departure)
            segment = PassengerSegment.BUSINESS if rng.random() < p_business else PassengerSegment.LEISURE

            wtp = wtp_model.sample_wtp(segment, rng)

            if not converter.will_book(fare, wtp):
                state.rejected_due_to_price += 1
                continue

            if not overbooking.allowed_to_accept_more(state.seats_sold, booking_limit):
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

            if state.seats_sold >= booking_limit and state.sellout_day is None:
                state.sellout_day = day

        state.last_quoted_fare = fare

    booked = state.seats_sold
    no_shows, _show_ups, boarded, denied, denied_cost, variable_cost = _departure_day_outcomes(
        config,
        rng,
        physical_capacity,
        booked,
        state.total_ticket_revenue,
    )
    total_cost = float(config.fixed_flight_cost) + variable_cost + denied_cost
    fare_series = tuple(f for _, f, _ in state.fare_history)

    return FlightSimulationResult(
        flight=flight,
        booking_horizon_days=int(config.booking_horizon_days),
        seats_sold=booked,
        total_ticket_revenue=state.total_ticket_revenue,
        total_ancillary_revenue=state.total_ancillary_revenue,
        total_cost=total_cost,
        bookings_business=state.bookings_business,
        bookings_leisure=state.bookings_leisure,
        rejected_due_to_price=state.rejected_due_to_price,
        rejected_due_to_capacity=state.rejected_due_to_capacity,
        sellout_day=state.sellout_day,
        fare_series=fare_series,
        physical_capacity=physical_capacity,
        booking_limit=booking_limit,
        bookings_accepted=booked,
        boarded_passengers=boarded,
        no_shows=no_shows,
        denied_boardings=denied,
        denied_boarding_cost=denied_cost,
    )
