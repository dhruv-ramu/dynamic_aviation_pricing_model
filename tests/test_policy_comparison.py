"""Policy comparison across Monte Carlo blocks."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.policy_comparison import compare_policies_monte_carlo

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_compare_policies_monte_carlo_returns_three_policies() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
        overbooking_enabled=False,
    )
    df = compare_policies_monte_carlo(cfg, n_runs=4, base_seed=99)
    assert len(df) == 3
    assert set(df["policy"]) == {"static", "rule_based", "dynamic"}
    assert df["mean_profit"].notna().all()
