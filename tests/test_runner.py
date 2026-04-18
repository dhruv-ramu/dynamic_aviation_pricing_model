"""Monte Carlo runner tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.runner import run_many, summarize_results

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_run_many_reproducible() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
        overbooking_enabled=False,
    )
    pol = StaticPricingPolicy(cfg)
    a = run_many(pol, cfg, n_runs=4, base_seed=123)
    b = run_many(pol, cfg, n_runs=4, base_seed=123)
    assert [compute_metrics(r).profit for r in a] == [compute_metrics(r).profit for r in b]


def test_summarize_results_shapes() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
        overbooking_enabled=False,
    )
    results = run_many(StaticPricingPolicy(cfg), cfg, n_runs=5, base_seed=7)
    s = summarize_results(results)
    assert "mean_profit" in s and "bump_risk" in s
