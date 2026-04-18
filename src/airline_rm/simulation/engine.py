"""Minimal single-flight simulation engine (Phase 1 placeholder demand)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

import numpy as np

from airline_rm.types import SimulationConfig
from airline_rm.constants import PLACEHOLDER_BOOKINGS_PER_DAY
from airline_rm.entities.booking_request import BookingRequest
from airline_rm.entities.flight import Flight
from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.entities.route import Route
from airline_rm.entities.simulation_state import FlightSimulationResult, SimulationState
from airline_rm.pricing.pricing_policy_base import PricingPolicy


class DailyDemandModel(Protocol):
    """Protocol for future stochastic demand modules."""

    def booking_attempts_today(
        self,
        days_until_departure: int,
        state: SimulationState,
        rng: np.random.Generator,
    ) -> int:
        """Return how many booking attempts occur today."""


@dataclass(slots=True)
class FixedDailyDemand:
    """Deterministic placeholder demand (constant attempts per day)."""

    attempts_per_day: int = PLACEHOLDER_BOOKINGS_PER_DAY

    def booking_attempts_today(
        self,
        days_until_departure: int,
        state: SimulationState,
        rng: np.random.Generator,
    ) -> int:
        _ = days_until_departure, state, rng
        return self.attempts_per_day


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
    demand_model: DailyDemandModel | None = None,
) -> FlightSimulationResult:
    """Simulate bookings day-by-day until the horizon ends."""

    flight = _build_flight(config)
    state = SimulationState(flight=flight)
    demand = demand_model or FixedDailyDemand()

    for day in range(1, config.booking_horizon_days + 1):
        state.day_index = day
        days_until_departure = config.booking_horizon_days - day + 1
        fare = policy.quote_fare(days_until_departure, state)
        attempts = demand.booking_attempts_today(days_until_departure, state, rng)

        for _ in range(attempts):
            if state.seats_remaining <= 0:
                break

            segment = (
                PassengerSegment.BUSINESS
                if rng.random() < 0.5
                else PassengerSegment.LEISURE
            )
            request = BookingRequest(
                days_until_departure=days_until_departure,
                segment=segment,
                offered_fare=fare,
            )

            state.seats_sold += 1
            state.total_ticket_revenue += fare
            state.total_ancillary_revenue += float(config.ancillary_mean)
            state.accepted_bookings.append(request)

    total_cost = float(config.fixed_flight_cost) + _variable_operating_cost(config, state.seats_sold)

    return FlightSimulationResult(
        flight=flight,
        booking_horizon_days=int(config.booking_horizon_days),
        seats_sold=state.seats_sold,
        total_ticket_revenue=state.total_ticket_revenue,
        total_ancillary_revenue=state.total_ancillary_revenue,
        total_cost=total_cost,
    )
