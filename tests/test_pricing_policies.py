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
    cfg = replace(cfg, dynamic_pace_gap_lower_abs=-0.01, dynamic_pace_ratio_raise_threshold=50.0)
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=0)
    act = pol.decide(20, st, competitor_fare=None)
    buckets = FareBucketSystem.from_values(cfg.fare_buckets)
    anchor = buckets.bucket_for_load_and_time(
        20,
        max(0, 180 - 0),
        180,
        early_window_days=cfg.early_window_days,
        late_window_days=cfg.late_window_days,
        low_load_factor_threshold=cfg.low_load_factor_threshold,
        high_load_factor_threshold=cfg.high_load_factor_threshold,
    )
    assert "pace-" in act.note
    assert act.bucket_index == buckets.lower_bucket(anchor, cfg.dynamic_lower_bucket_steps_behind)


def test_dynamic_raises_when_far_ahead_on_pace() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, dynamic_pace_ratio_raise_threshold=0.5, dynamic_pace_gap_raise_abs=-1e9)
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=20)
    act = pol.decide(25, st, competitor_fare=None)
    buckets = FareBucketSystem.from_values(cfg.fare_buckets)
    anchor = buckets.bucket_for_load_and_time(
        25,
        160,
        180,
        early_window_days=cfg.early_window_days,
        late_window_days=cfg.late_window_days,
        low_load_factor_threshold=cfg.low_load_factor_threshold,
        high_load_factor_threshold=cfg.high_load_factor_threshold,
    )
    assert "pace+" in act.note
    assert act.bucket_index >= buckets.raise_bucket(anchor, cfg.dynamic_raise_bucket_steps_ahead)


def test_dynamic_scarcity_raises_bucket() -> None:
    base = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    neutral_pace = dict(
        dynamic_pace_ratio_raise_threshold=50.0,
        dynamic_pace_ratio_lower_threshold=0.01,
        dynamic_pace_gap_raise_abs=500.0,
        dynamic_pace_gap_lower_abs=-500.0,
    )
    tight = replace(
        base,
        **neutral_pace,
        dynamic_scarcity_fill_ratio_1=0.05,
        dynamic_scarcity_fill_ratio_2=0.08,
        dynamic_scarcity_raise_steps_1=0,
        dynamic_scarcity_raise_steps_2=4,
    )
    loose = replace(
        tight,
        dynamic_scarcity_fill_ratio_1=0.99,
        dynamic_scarcity_fill_ratio_2=0.995,
    )
    # Neutral pace, mid anchor (needs unsold share > high LF threshold), scarcity is the spread.
    st = _flight_state(capacity=180, sold=20)
    hi = DynamicPricingPolicy(tight).decide(25, st, competitor_fare=None)
    lo = DynamicPricingPolicy(loose).decide(25, st, competitor_fare=None)
    assert hi.bucket_index > lo.bucket_index
    assert "scar+" in hi.note


def test_dynamic_late_floor_blocks_deepest_discount() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(
        cfg,
        dynamic_late_floor_days_until_departure=60,
        dynamic_min_bucket_index_late=3,
        dynamic_pace_ratio_lower_threshold=5.0,
        dynamic_pace_gap_lower_abs=-1e9,
        dynamic_lower_bucket_steps_behind=1,
    )
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=0)
    act = pol.decide(5, st, competitor_fare=None)
    assert act.bucket_index >= cfg.dynamic_min_bucket_index_late


def test_dynamic_ignores_competitor_when_seats_tight() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, competitor_response_strength=1.0, competitor_match_threshold=1.0)
    pol = DynamicPricingPolicy(cfg)
    st = _flight_state(capacity=180, sold=165)
    no_comp = pol.decide(12, st, competitor_fare=None)
    cheap_comp = pol.decide(12, st, competitor_fare=1.0)
    assert no_comp.bucket_index == cheap_comp.bucket_index


def test_dynamic_bucket_always_in_bounds() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        dynamic_raise_bucket_steps_ahead=9,
        dynamic_scarcity_raise_steps_2=9,
        dynamic_pace_ratio_raise_threshold=0.5,
        dynamic_pace_gap_raise_abs=-1e9,
        dynamic_demand_pressure_ratio=1.0,
    )
    pol = DynamicPricingPolicy(cfg)
    mx = FareBucketSystem.from_values(cfg.fare_buckets).max_bucket()
    for sold in (0, 50, 179):
        for d in (1, 15, 45, 60):
            act = pol.decide(d, _flight_state(capacity=180, sold=sold), competitor_fare=None)
            assert 0 <= act.bucket_index <= mx


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
