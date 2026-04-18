"""Monte Carlo policy comparison across named environment scenarios."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

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
    "overbook_bump_stress",
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
        extras = sorted(n for n in filter_names if n not in chosen)
        return tuple(chosen + extras)
    # Default matrix: narrative set only (extras such as ``no_overbooking`` require --scenarios).
    return tuple(n for n in DEFAULT_SCENARIO_ORDER if n in all_names)


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
        cfg = replace(apply_scenario(base_config, name), rng_seed=seed)
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
        rb = float(grp.loc[grp["policy"] == "rule_based", "mean_profit"].iloc[0])
        dyn = float(grp.loc[grp["policy"] == "dynamic", "mean_profit"].iloc[0])
        rows.append(
            {
                "scenario": scenario,
                "winner": str(best["policy"]),
                "mean_profit_static": static_p,
                "mean_profit_rule_based": rb,
                "mean_profit_dynamic": dyn,
                "rule_based_minus_static": rb - static_p,
                "dynamic_minus_static": dyn - static_p,
            }
        )
    return pd.DataFrame(rows)


def profit_delta_vs_static_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """Wide table: static profit plus rule/dynamic deltas vs static (per scenario)."""

    pivot = long_df.pivot(index="scenario", columns="policy", values="mean_profit")
    static = pivot["static"].astype(float)
    return pd.DataFrame(
        {
            "scenario": pivot.index.astype(str),
            "profit_static": static.values,
            "delta_rule_minus_static": (pivot["rule_based"] - static).values,
            "delta_dynamic_minus_static": (pivot["dynamic"] - static).values,
        }
    )


def compact_winner_table(long_df: pd.DataFrame, winners: pd.DataFrame) -> pd.DataFrame:
    """Single compact row per scenario: winner, deltas, bump risk, booking pressure."""

    bump_by = long_df.pivot(index="scenario", columns="policy", values="bump_risk")
    br = long_df.pivot(index="scenario", columns="policy", values="mean_booking_rate")
    denied = long_df.pivot(index="scenario", columns="policy", values="mean_denied_boardings")
    mx_bump = long_df.groupby("scenario", sort=False)["bump_risk"].max().rename("bump_risk_max")
    out = winners[
        ["scenario", "winner", "rule_based_minus_static", "dynamic_minus_static"]
    ].set_index("scenario")
    out["bump_risk_dynamic"] = bump_by["dynamic"]
    out["bump_risk_max"] = mx_bump
    out["mean_book_rate_dynamic"] = br["dynamic"]
    out["mean_denied_dynamic"] = denied["dynamic"]
    return out.reset_index()


def format_compact_scenario_output(
    winners: pd.DataFrame,
    compact: pd.DataFrame,
    deltas: pd.DataFrame,
) -> str:
    """ASCII summary: winner table + profit deltas (no wide long replication table)."""

    lines = [
        "=== winners (mean_profit) ===",
        winners.to_string(index=False),
        "",
        "=== profit vs static ===",
        deltas.to_string(index=False, float_format=lambda x: f"{x:,.2f}"),
        "",
        "=== bump / booking pressure (dynamic policy) ===",
        compact[
            [
                "scenario",
                "bump_risk_dynamic",
                "bump_risk_max",
                "mean_book_rate_dynamic",
                "mean_denied_dynamic",
            ]
        ].to_string(index=False, float_format=lambda x: f"{x:.3f}"),
    ]
    return "\n".join(lines)


def format_scenario_report(long_df: pd.DataFrame, winners: pd.DataFrame | None = None) -> str:
    """Wide mean_profit pivot (``winners`` kept for API compatibility; use compact tables separately)."""

    _ = winners
    pivot = long_df.pivot(index="scenario", columns="policy", values="mean_profit")
    order = [s for s in DEFAULT_SCENARIO_ORDER if s in pivot.index]
    order += [s for s in pivot.index if s not in order]
    pivot = pivot.reindex(order)
    return "--- mean_profit by scenario and policy ---\n" + pivot.to_string(float_format=lambda x: f"{x:,.2f}")


def list_scenario_names_for_cli() -> str:
    return ", ".join(list_scenarios())
