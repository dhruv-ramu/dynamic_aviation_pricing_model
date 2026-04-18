"""Tests for the simulation engine with stochastic demand."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.entities.simulation_state import FlightSimulationResult
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_engine_returns_typed_result_within_limits() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        overbooking_enabled=False,
        demand_stochastic=False,
        competitor_mode="none",
    )
    rng = make_generator(cfg)
    policy = StaticPricingPolicy(cfg)
    result = run_single_flight_simulation(cfg, policy, rng)

    assert isinstance(result, FlightSimulationResult)
    assert 0 <= result.seats_sold <= result.booking_limit
    assert result.booking_limit == cfg.capacity
    assert result.boarded_passengers <= cfg.capacity
    assert result.bookings_business + result.bookings_leisure == result.seats_sold
    max_fare = max(cfg.fare_buckets)
    assert result.total_ticket_revenue == result.seats_sold * max_fare
    assert len(set(result.fare_series)) == 1


def test_engine_is_reproducible_for_fixed_seed() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        overbooking_enabled=False,
        demand_stochastic=False,
        competitor_mode="none",
    )
    r1 = run_single_flight_simulation(cfg, StaticPricingPolicy(cfg), make_generator(cfg))
    r2 = run_single_flight_simulation(cfg, StaticPricingPolicy(cfg), make_generator(cfg))
    assert r1.seats_sold == r2.seats_sold
    assert r1.rejected_due_to_price == r2.rejected_due_to_price
    assert r1.rejected_due_to_capacity == r2.rejected_due_to_capacity
    assert r1.boarded_passengers == r2.boarded_passengers
