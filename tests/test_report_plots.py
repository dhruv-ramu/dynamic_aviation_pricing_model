"""Figure export smoke tests."""

from __future__ import annotations

from pathlib import Path

from dataclasses import replace

import pandas as pd

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.report_plots import plot_scenario_policy_profit_bars, write_scenario_figures
from airline_rm.simulation.scenario import apply_scenario


def test_plot_scenario_policy_profit_bars_writes_png(tmp_path: Path) -> None:
    long = pd.DataFrame(
        {
            "scenario": ["a", "a", "a", "b", "b", "b"],
            "policy": ["static", "rule_based", "dynamic"] * 2,
            "mean_profit": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "mean_revenue": [1.0] * 6,
            "mean_boarded_load_factor": [0.5] * 6,
            "mean_accepted_booking_load_factor": [0.5] * 6,
            "mean_booking_rate": [0.7] * 6,
            "mean_avg_fare": [150.0] * 6,
            "mean_denied_boardings": [0.0] * 6,
            "bump_risk": [0.0] * 6,
        }
    )
    out = tmp_path / "bars.png"
    plot_scenario_policy_profit_bars(long, out)
    assert out.is_file() and out.stat().st_size > 100


def test_write_scenario_figures_creates_trajectories(tmp_path: Path) -> None:
    base = replace(
        load_simulation_config(Path(__file__).resolve().parents[1] / "configs" / "base_config.yaml"),
        demand_stochastic=False,
        competitor_mode="none",
        rng_seed=99,
    )
    long = pd.DataFrame(
        {
            "scenario": ["baseline"] * 3,
            "policy": ["static", "rule_based", "dynamic"],
            "mean_profit": [1.0, 2.0, 3.0],
            "mean_revenue": [1.0, 2.0, 3.0],
            "mean_boarded_load_factor": [0.5, 0.6, 0.55],
            "mean_accepted_booking_load_factor": [0.5, 0.6, 0.55],
            "mean_booking_rate": [0.7, 0.8, 0.75],
            "mean_avg_fare": [150.0, 160.0, 155.0],
            "mean_denied_boardings": [0.0, 0.0, 0.0],
            "bump_risk": [0.0, 0.0, 0.0],
        }
    )
    paths = write_scenario_figures(
        long,
        base,
        tmp_path,
        trajectory_seed=99,
        trajectory_scenarios=("strong_demand",),
    )
    assert len(paths) == 2
    assert all(p.is_file() for p in paths)
