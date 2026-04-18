"""Scenario presets and cross-scenario policy comparison."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from dataclasses import replace

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.policy_comparison import compare_policies_monte_carlo
from airline_rm.evaluation.scenario_comparison import (
    compare_policies_across_scenarios,
    compact_winner_table,
    profit_delta_vs_static_wide,
    scenario_names_ordered,
    scenario_winner_table,
)
from airline_rm.simulation.scenario import SCENARIO_PRESETS, apply_scenario, list_scenarios

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_baseline_scenario_is_identity() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    out = apply_scenario(cfg, "baseline")
    assert out == cfg


def test_all_named_scenarios_apply_cleanly() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    for name in SCENARIO_PRESETS:
        apply_scenario(cfg, name)


def test_scenario_matrix_smoke() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, demand_stochastic=False, competitor_mode="none")
    df = compare_policies_across_scenarios(cfg, scenario_names=("baseline", "weak_demand"), n_runs=3)
    assert set(df["scenario"]) == {"baseline", "weak_demand"}
    assert set(df["policy"]) == {"static", "rule_based", "dynamic"}
    assert "mean_profit" in df.columns


def test_winner_table_shape() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, demand_stochastic=False, competitor_mode="none")
    long_df = compare_policies_across_scenarios(cfg, scenario_names=("baseline",), n_runs=2)
    w = scenario_winner_table(long_df)
    assert len(w) == 1
    assert w["winner"].iloc[0] in {"static", "rule_based", "dynamic"}


def test_scenario_filter_order() -> None:
    names = scenario_names_ordered(["strong_demand", "baseline", "weak_demand"])
    assert names[0] == "baseline"
    assert "strong_demand" in names
    assert "weak_demand" in names


def test_list_scenarios_includes_core_environments() -> None:
    keys = set(list_scenarios())
    for required in (
        "baseline",
        "weak_demand",
        "strong_demand",
        "very_strong_late_demand",
        "high_no_show",
        "low_no_show",
        "business_heavy",
        "leisure_heavy",
        "higher_overbooking",
        "overbook_bump_stress",
        "strong_competitor_pressure",
    ):
        assert required in keys


def test_overbook_bump_stress_shows_bump_risk() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    cfg = replace(cfg, rng_seed=11)
    stressed = apply_scenario(cfg, "overbook_bump_stress")
    df = compare_policies_monte_carlo(stressed, n_runs=50, base_seed=2027)
    assert float(df["bump_risk"].max()) >= 0.15
    assert float(df["mean_booking_rate"].max()) >= 0.85


def test_compact_and_delta_helpers() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        demand_stochastic=False,
        competitor_mode="none",
    )
    long_df = compare_policies_across_scenarios(cfg, scenario_names=("baseline",), n_runs=2)
    w = scenario_winner_table(long_df)
    c = compact_winner_table(long_df, w)
    d = profit_delta_vs_static_wide(long_df)
    assert "bump_risk_dynamic" in c.columns
    assert "delta_rule_minus_static" in d.columns


def test_scenario_winner_columns_numeric() -> None:
    rows = [
        {"scenario": "s1", "policy": "static", "mean_profit": 1.0},
        {"scenario": "s1", "policy": "rule_based", "mean_profit": 5.0},
        {"scenario": "s1", "policy": "dynamic", "mean_profit": 3.0},
    ]
    w = scenario_winner_table(pd.DataFrame(rows))
    assert w["winner"].iloc[0] == "rule_based"
    assert w["rule_based_minus_static"].iloc[0] == 4.0
