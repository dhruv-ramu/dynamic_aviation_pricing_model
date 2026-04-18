"""Sensitivity sweep smoke tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.sensitivity import sweep_parameter

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sweep_no_show_mean() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=False,
        overbooking_enabled=True,
    )
    df = sweep_parameter(cfg, "no_show_mean", [0.05, 0.12, 0.18], n_runs=3, base_seed=5)
    assert len(df) == 3
    assert df["param"].eq("no_show_mean").all()
