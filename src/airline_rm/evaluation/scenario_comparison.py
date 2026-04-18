"""Monte Carlo policy comparison across named environment scenarios."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from airline_rm.evaluation.policy_comparison import compare_policies_monte_carlo
from airline_rm.simulation.scenario import SCENARIO_PRESETS, apply_scenario, list_scenarios
from airline_rm.types import SimulationConfig

# Default table order (narrative grouping, not alphabetical).
DEFAULT_SCENARIO_ORDER: tuple[str, ...] = (
    "baseline",
    "weak_demand",
    "strong_demand",
    "very_strong_late_demand",
    "high_no_show",
    "low_no_show",
    "business_heavy",
    "leisure_heavy",
    "higher_overbooking",
    "strong_competitor_pressure",
)


def scenario_names_ordered(filter_names: Sequence[str] | None = None) -> tuple[str, ...]:
    """Return scenario keys in a stable order, optionally restricted to ``filter_names``."""

    all_names = set(SCENARIO_PRESETS.keys())
    if filter_names:
        missing = [n for n in filter_names if n not in all_names]
        if missing:
            raise KeyError(
                f"Unknown scenario(s): {', '.join(missing)}. "
                f"Available: {', '.join(sorted(all_names))}"
            )
        chosen = [n for n in DEFAULT_SCENARIO_ORDER if n in filter_names]
        extras = [n for n in filter_names if n not in chosen]
        return tuple(chosen + sorted(extras))
    return tuple(n for n in DEFAULT_SCENARIO_ORDER if n in all_names) + tuple(
        sorted(n for n in all_names if n not in DEFAULT_SCENARIO_ORDER)
    )


def compare_policies_across_scenarios(
    base_config: SimulationConfig,
    *,
    scenario_names: Sequence[str] | None = None,
    n_runs: int,
    base_seed: int | None = None,
) -> pd.DataFrame:
    """Run ``compare_policies_monte_carlo`` for each named scenario (independent configs)."""

    seed = int(base_config.rng_seed if base_seed is None else base_seed)
    names = scenario_names_ordered(scenario_names)
    frames: list[pd.DataFrame] = []
    for name in names:
        cfg = apply_scenario(base_config, name)
        cfg = type(cfg)(**{**{f.name: getattr(cfg, f.name) for f in type(cfg).__dataclass_fields__.values()}, "rng_seed": seed})  # noqa: SLF001
        # Preserve explicit seed on each scenario copy
        from dataclasses import replace

        cfg = replace(cfg, rng_seed=seed)
        df = compare_policies_monte_carlo(cfg, n_runs=n_runs, base_seed=seed)
        df.insert(0, "scenario", name)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def scenario_winner_table(comparison_long: pd.DataFrame) -> pd.DataFrame:
    """One row per scenario: best policy by ``mean_profit`` and profit gaps vs static."""

    if comparison_long.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for scenario, grp in comparison_long.groupby("scenario", sort=False):
        best = grp.loc[grp["mean_profit"].idxmax()]
        static_row = grp[grp["policy"] == "static"]
        static_p = float(static_row["mean_profit"].iloc[0]) if len(static_row) else float("nan")
        row: dict[str, Any] = {
            "scenario": scenario,
            "winner": str(best["policy"]),
            "mean_profit_static": static_p,
            "mean_profit_rule_based": float(grp.loc[grp["policy"] == "rule_based", "mean_profit"].iloc[0]),
            "mean_profit_dynamic": float(grp.loc[grp["policy"] == "dynamic", "mean_profit"].iloc[0]),
        }
        for pol in ("rule_based", "dynamic"):
            p = float(grp.loc[grp["policy"] == pol, "mean_profit"].iloc[0])
            row[f"{pol}_minus_static"] = p - static_p
        rows.append(row)
    return pd.DataFrame(rows)


def format_scenario_report(long_df: pd.DataFrame, winners: pd.DataFrame | None = None) -> str:
    """Human-readable block for CLI (wide profit pivot + optional winner summary)."""

    pivot = long_df.pivot(index="scenario", columns="policy", values="mean_profit")
    pivot = pivot.reindex([r for r in DEFAULT_SCENARIO_ORDER if r in pivot.index]).dropna(how="all")
    lines = ["--- mean_profit by scenario and policy ---", pivot.to_string(float_format=lambda x: f"{x:,.2f}")]
    if winners is not None and not winners.empty:
        lines.append("\n--- winner (max mean_profit) ---")
        sub = winners[
            [
                "scenario",
                "winner",
                "rule_based_minus_static",
                "dynamic_minus_static",
            ]
        ]
        lines.append(sub.to_string(index=False))
    return "\n".join(lines)
