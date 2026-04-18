"""Tests for pricing policies and policy comparison."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np

from airline_rm.config import load_simulation_config
from airline_rm.entities.flight import Flight
from airline_rm.entities.route import Route
from airline_rm.entities.simulation_state import SimulationState
from airline_rm.evaluation.policy_comparison import compare_default_policies
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _flight_state(*, capacity: int, sold: int) -> SimulationState:
    route = Route("SEA", "SFO", 400.0)
    flight = Flight("T", route, date(2026, 6, 1), capacity=capacity)
    return SimulationState(flight=flight, seats_sold=sold, booking_limit=capacity)


def test_static_policy_constant_fare() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    pol = StaticPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=0)
    fares = {pol.decide(d, st, competitor_fare=None).fare for d in (60, 30, 1)}
    assert len(fares) == 1


def test_rule_based_cheap_when_far_and_loose() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    pol = RuleBasedPricingPolicy(cfg)
    st = _flight_state(capacity=100, sold=2)
    act = pol.decide(55, st, competitor_fare=None)
    assert act.bucket_index == 0


def test_rule_based_expensive_when_tight_inventory() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    pol = RuleBasedPricingPolicy(cfg)
    st = _flight_state(capacity=100, sold=96)
    act = pol.decide(20, st, competitor_fare=None)
    assert act.bucket_index == FareBucketSystem.from_values(cfg.fare_buckets).max_bucket()


def test_dynamic_lowers_when_far_behind_pace() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, pace_gap_lower_threshold=-0.01, pace_gap_raise_threshold=500.0)
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=0)
    act = pol.decide(3, st, competitor_fare=None)
    assert "behind_pace" in act.note or act.bucket_index == FareBucketSystem.from_values(cfg.fare_buckets).min_bucket()


def test_dynamic_raises_when_far_ahead_on_pace() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, pace_gap_raise_threshold=-500.0, pace_gap_lower_threshold=-1_000.0)
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=175)
    act = pol.decide(25, st, competitor_fare=None)
    max_b = FareBucketSystem.from_values(cfg.fare_buckets).max_bucket()
    assert "ahead_pace" in act.note or act.bucket_index >= max_b - 1


def test_compare_default_policies_returns_three_rows() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
    )
    df = compare_default_policies(cfg)
    assert len(df) == 3
    assert set(df["policy"]) == {"static", "rule_based", "dynamic"}
    assert "mean_profit" in df.columns


def test_rule_based_fares_vary_across_horizon_in_engine() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        pricing_policy="rule_based",
        competitor_mode="none",
        demand_stochastic=False,
    )
    result = run_single_flight_simulation(cfg, RuleBasedPricingPolicy(cfg), make_generator(cfg))
    assert len(set(result.fare_series)) >= 2


def test_dynamic_fares_vary_across_horizon_in_engine() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        pricing_policy="dynamic",
        competitor_mode="none",
        demand_stochastic=False,
    )
    result = run_single_flight_simulation(cfg, DynamicPricingPolicy(cfg), make_generator(cfg))
    assert len(set(result.fare_series)) >= 2


def test_engine_runs_each_policy() -> None:
    base = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
    )
    for name, pol in (
        ("static", StaticPricingPolicy(base)),
        ("rule_based", RuleBasedPricingPolicy(base)),
        ("dynamic", DynamicPricingPolicy(base)),
    ):
        rng = make_generator(base)
        result = run_single_flight_simulation(base, pol, rng)
        assert result.seats_sold <= result.booking_limit, name
