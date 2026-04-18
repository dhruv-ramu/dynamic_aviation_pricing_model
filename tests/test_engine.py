"""Tests for the simulation engine skeleton."""

from __future__ import annotations

from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.entities.simulation_state import FlightSimulationResult
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_engine_returns_typed_result() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    rng = make_generator(cfg)
    policy = StaticPricingPolicy(cfg)
    result = run_single_flight_simulation(cfg, policy, rng)

    assert isinstance(result, FlightSimulationResult)
    assert result.seats_sold <= cfg.capacity
    assert result.seats_sold == cfg.booking_horizon_days * 2
    assert result.total_ticket_revenue == result.seats_sold * cfg.fare_buckets[0]
