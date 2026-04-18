"""Matplotlib figures for scenario experiments (non-interactive backend)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator
from airline_rm.simulation.scenario import apply_scenario
from airline_rm.types import SimulationConfig


def plot_scenario_policy_profit_bars(long_df: pd.DataFrame, out_path: Path) -> None:
    """Grouped bars: mean_profit by scenario for each policy."""

    pivot = long_df.pivot(index="scenario", columns="policy", values="mean_profit")
    scenarios = list(pivot.index)
    x = np.arange(len(scenarios))
    width = 0.25
    fig, ax = plt.subplots(figsize=(max(10.0, len(scenarios) * 1.1), 5.0))
    for i, pol in enumerate(["static", "rule_based", "dynamic"]):
        if pol not in pivot.columns:
            continue
        ax.bar(x + (i - 1) * width, pivot[pol].values, width=width, label=pol)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=35, ha="right")
    ax.set_ylabel("Mean profit ($)")
    ax.set_title("Mean profit by scenario and policy")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_fare_trajectory_pair(
    config: SimulationConfig,
    *,
    out_path: Path,
    seed: int,
) -> None:
    """Overlay rule_based vs dynamic quoted fares over the booking horizon (single run each, same RNG seed)."""

    policies = {
        "rule_based": RuleBasedPricingPolicy(config),
        "dynamic": DynamicPricingPolicy(config),
    }
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    horizon = int(config.booking_horizon_days)
    days = np.arange(1, horizon + 1)
    cfg_seeded = replace(config, rng_seed=int(seed))
    for name, pol in policies.items():
        rng = make_generator(cfg_seeded)
        result = run_single_flight_simulation(config, pol, rng)
        fares = list(result.fare_series)
        if len(fares) != horizon:
            xs = np.linspace(1, horizon, num=len(fares))
        else:
            xs = days
        ax.plot(xs, fares, label=name, linewidth=1.4, alpha=0.9)
    ax.set_xlabel("Sales day (1 = first day in horizon)")
    ax.set_ylabel("Quoted fare ($)")
    ax.set_title("Fare path: rule_based vs dynamic")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def write_scenario_figures(
    long_df: pd.DataFrame,
    base_config: SimulationConfig,
    report_dir: Path,
    *,
    trajectory_seed: int,
    trajectory_scenarios: tuple[str, ...] | None = None,
) -> list[Path]:
    """Write summary bar chart and fare trajectory PNGs. Returns paths written."""

    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    bar_path = report_dir / "scenario_policy_mean_profit.png"
    plot_scenario_policy_profit_bars(long_df, bar_path)
    written.append(bar_path)
    want = ("strong_demand", "very_strong_late_demand")
    if trajectory_scenarios is None:
        have = set(long_df["scenario"].astype(str))
        trajectory_scenarios = tuple(s for s in want if s in have)
        if not trajectory_scenarios and have:
            trajectory_scenarios = (sorted(have)[0],)
    for scen in trajectory_scenarios:
        cfg = replace(apply_scenario(base_config, scen), rng_seed=int(trajectory_seed))
        p = report_dir / f"fare_trajectory_rule_vs_dynamic__{scen}.png"
        plot_fare_trajectory_pair(cfg, out_path=p, seed=trajectory_seed)
        written.append(p)
    return written
