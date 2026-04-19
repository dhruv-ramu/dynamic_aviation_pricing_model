"""Minimal evidence bundle for report writing: ``reports/chat_exp/``.

Run: ``PYTHONPATH=src python -m airline_rm.evaluation.chat_exp_export``
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from textwrap import dedent
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.final_report_export import (
    BASE_SEED,
    DEFAULT_CONFIG,
    N_RUNS,
    POLICY_MAP,
    POLICY_ORDER,
    PROJECT_ROOT,
    SCENARIOS,
    _collect_all,
    _plot_fare_overlay,
    _plot_grouped_bars,
)
from airline_rm.simulation.scenario import apply_scenario
from airline_rm.types import SimulationConfig

OUTPUT = PROJECT_ROOT / "reports" / "chat_exp"
VALIDATION_DIR = PROJECT_ROOT / "reports" / "validation"
REFERENCE_SEED = 2026

FARE_SCENARIOS = ("strong_demand", "very_strong_late_demand", "overbook_bump_stress")


def _winner_summary(policy_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scen in policy_df["scenario"].unique():
        sub = policy_df[policy_df["scenario"] == scen]
        p = {r["policy"]: float(r["mean_profit"]) for _, r in sub.iterrows()}
        s, rb, d = p["static"], p["rule_based"], p["dynamic"]
        tie_order = ("static", "rule_based", "dynamic")
        best_val = max(p.values())
        best = next(k for k in tie_order if abs(p[k] - best_val) < 1e-9)
        rows.append(
            {
                "scenario": scen,
                "winner": best,
                "profit_static": s,
                "profit_rule_based": rb,
                "profit_dynamic": d,
                "dynamic_minus_rule": d - rb,
                "rule_minus_static": rb - s,
            }
        )
    return pd.DataFrame(rows)


def _build_validation_summary(scenarios: tuple[str, ...]) -> pd.DataFrame:
    """Compress validation CSVs into categorical rows (approximate where noted)."""

    stab_win = VALIDATION_DIR / "validation_monte_carlo_stability_winners.csv"
    seed_csv = VALIDATION_DIR / "validation_seed_sensitivity.csv"
    stat_csv = VALIDATION_DIR / "validation_statistical_tests.csv"

    stab_df = pd.read_csv(stab_win) if stab_win.is_file() else None
    seed_df = pd.read_csv(seed_csv) if seed_csv.is_file() else None
    stat_df = pd.read_csv(stat_csv) if stat_csv.is_file() else None

    rows: list[dict[str, Any]] = []
    for scen in scenarios:
        notes: list[str] = []

        # Prefix winner vs n=500
        winner_stability = "medium"
        if stab_df is not None and not stab_df.empty:
            sub = stab_df[stab_df["scenario"] == scen]
            if sub.empty:
                winner_stability = "unknown"
            else:
                bad = int(sub["ranking_differs_from_winner_at_n500"].sum())
                if bad == 0:
                    winner_stability = "high"
                elif bad <= 1:
                    winner_stability = "medium"
                else:
                    winner_stability = "low"
                    notes.append("multiple prefix lengths disagree with n=500 winner")
        else:
            winner_stability = "unknown"
            notes.append("run validation suite for stability metrics")

        # Seed flips vs reference 2026
        seed_sensitivity = "stable"
        if seed_df is not None and not seed_df.empty:
            fl = seed_df[(seed_df["scenario"] == scen) & (seed_df["seed"] != REFERENCE_SEED)]
            n_flip = int(fl["winner_differs_from_seed_2026"].sum())
            if n_flip == 0:
                seed_sensitivity = "stable"
            elif n_flip == 1:
                seed_sensitivity = "some_variation"
                notes.append("one alternate-seed winner change")
            else:
                seed_sensitivity = "unstable"
                notes.append(f"{n_flip} alternate-seed winner changes")
        else:
            seed_sensitivity = "unknown"

        sig = "unknown"
        if stat_df is not None and not stat_df.empty:
            r = stat_df[stat_df["scenario"] == scen]
            if len(r):
                lo, hi = float(r["ci95_low"].iloc[0]), float(r["ci95_high"].iloc[0])
                sig = "yes" if (lo > 0 or hi < 0) else "no"
            else:
                sig = "unknown"
        else:
            notes.append("no statistical test table")

        rows.append(
            {
                "scenario": scen,
                "winner_stability": winner_stability,
                "seed_sensitivity": seed_sensitivity,
                "statistically_significant_dynamic_vs_rule": sig,
                "notes": "; ".join(notes) if notes else "",
            }
        )

    return pd.DataFrame(rows)


def _config_snapshot_yaml(base_cfg: SimulationConfig) -> dict[str, Any]:
    cfg = replace(apply_scenario(base_cfg, "baseline"), rng_seed=BASE_SEED)
    keys = (
        "capacity",
        "expected_total_demand",
        "demand_multiplier",
        "no_show_mean",
        "overbooking_limit_pct",
        "leisure_wtp_mean",
        "business_wtp_mean",
        "booking_curve_midpoint",
        "booking_curve_steepness",
    )
    out: dict[str, Any] = {}
    for k in keys:
        out[k] = getattr(cfg, k, None)
    out["capacity"] = int(cfg.capacity)
    return out


def _plot_bump_risk_bump_stress(policy_df: pd.DataFrame, path: Path) -> None:
    scen = "overbook_bump_stress"
    sub = policy_df[policy_df["scenario"] == scen]
    if sub.empty:
        return
    labels = []
    vals = []
    for pol in ("static", "rule_based", "dynamic"):
        r = sub[sub["policy"] == pol]
        if not r.empty:
            labels.append(pol.replace("_", " "))
            vals.append(float(r["bump_risk"].iloc[0]))
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.bar(labels, vals, color=["#5c6b73", "#2e6f95", "#c45c26"])
    ax.set_ylabel("Bump risk (share of runs with denied > 0)")
    ax.set_title("Bump risk — overbook_bump_stress")
    ax.set_ylim(0, max(1.0, max(vals) * 1.15) if vals else 1.0)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_key_results_md(policy_df: pd.DataFrame, winners: pd.DataFrame, val_sum: pd.DataFrame) -> str:
    lines = [
        "# Key results (factual)",
        "",
        "## Winners by scenario (mean profit)",
        "",
    ]
    for _, r in winners.iterrows():
        lines.append(f"- **{r['scenario']}**: `{r['winner']}` (static ${r['profit_static']:,.0f}; rule ${r['profit_rule_based']:,.0f}; dynamic ${r['profit_dynamic']:,.0f}).")

    lines += ["", "## Where dynamic leads on mean profit", ""]
    for _, r in winners.iterrows():
        if r["winner"] == "dynamic":
            lines.append(f"- `{r['scenario']}` (dynamic − rule = ${r['dynamic_minus_rule']:,.0f}).")

    lines += ["", "## Where rule-based leads", ""]
    for _, r in winners.iterrows():
        if r["winner"] == "rule_based":
            lines.append(f"- `{r['scenario']}`.")

    lines += ["", "## Weak / not statistically significant (dynamic vs rule, paired MC)", ""]
    if not val_sum.empty:
        weak = val_sum[val_sum["statistically_significant_dynamic_vs_rule"] == "no"]["scenario"].tolist()
        if weak:
            for s in weak:
                lines.append(f"- `{s}`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).")
        else:
            lines.append("- See `tables/validation_summary.csv` per scenario.")

    lines += [
        "",
        "## overbook_bump_stress",
        "",
        "- High denied-boarding cost regime; mean-profit winner and bump_risk differ by policy — see figures and `scenario_policy_results.csv`.",
        "",
    ]
    return "\n".join(lines)


def export_chat_exp() -> Path:
    shutil.rmtree(OUTPUT, ignore_errors=True)
    tables = OUTPUT / "tables"
    figures = OUTPUT / "figures"
    raw = OUTPUT / "raw"
    for d in (tables, figures, raw):
        d.mkdir(parents=True, exist_ok=True)

    base_cfg = load_simulation_config(DEFAULT_CONFIG)
    base_cfg = replace(base_cfg, rng_seed=BASE_SEED)

    policy_rows, run_rows, _ = _collect_all(base_cfg)
    policy_df = pd.DataFrame(policy_rows)

    cols = [
        "scenario",
        "policy",
        "mean_profit",
        "mean_revenue",
        "mean_boarded_load_factor",
        "mean_avg_fare",
        "mean_denied_boardings",
        "bump_risk",
    ]
    policy_df[cols].to_csv(tables / "scenario_policy_results.csv", index=False)

    winners = _winner_summary(policy_df)
    winners.to_csv(tables / "winner_summary.csv", index=False)

    val_df = _build_validation_summary(SCENARIOS)
    val_df.to_csv(tables / "validation_summary.csv", index=False)

    snap = _config_snapshot_yaml(base_cfg)
    with (tables / "config_snapshot.yaml").open("w", encoding="utf-8") as fh:
        yaml.safe_dump(snap, fh, default_flow_style=False, sort_keys=False)

    _plot_grouped_bars(
        policy_df,
        "mean_profit",
        "Mean profit ($)",
        "Mean profit by scenario and policy",
        figures / "mean_profit_by_scenario.png",
    )
    for scen in FARE_SCENARIOS:
        _plot_fare_overlay(base_cfg, scen, figures / f"fare_path_rule_vs_dynamic__{scen}.png")
    _plot_bump_risk_bump_stress(policy_df, figures / "bump_risk__overbook_bump_stress.png")

    run_df = pd.DataFrame(run_rows)
    sample = run_df[
        run_df["scenario"].isin(("baseline", "strong_demand", "overbook_bump_stress"))
        & (run_df["run_id"] < 2)
    ][["scenario", "policy", "run_id", "profit", "boarded_load_factor", "avg_fare", "denied_boardings"]]
    sample = sample.head(20)
    sample.to_csv(raw / "minimal_run_sample.csv", index=False)

    (OUTPUT / "key_results.md").write_text(_write_key_results_md(policy_df, winners, val_df), encoding="utf-8")

    (OUTPUT / "methodology.md").write_text(
        dedent(
            f"""\
            # Methodology (short)

            **Simulator:** single flight, discrete booking days, stochastic arrivals, segment mix (business/leisure),
            fare buckets, no-shows at departure, optional overbooking with denied-boarding costs. One simulation run
            yields bookings, revenues, costs, and profit.

            **Policies:** static (fixed bucket), rule-based (time/load thresholds + mild competitor response),
            dynamic (pace/scarcity/demand-pressure heuristic).

            **Scenarios:** named YAML-style overrides on a common base route ({len(SCENARIOS)} presets in this export).

            **Monte Carlo:** `n_runs={N_RUNS}`, policy RNG blocks `seed = {BASE_SEED} + policy_index×1_000_003`, run index
            `0…n−1`. Metrics are per-run from `compute_metrics`, then averaged unless noted.

            **Fare path figures:** one representative run per policy (profit closest to that policy’s mean profit), same
            convention as the full report export.
            """
        ),
        encoding="utf-8",
    )

    (OUTPUT / "limitations.md").write_text(
        dedent(
            """\
            # Limitations

            - **Synthetic calibration** — illustrative route parameters, not fit to a carrier’s data.
            - **No real airline PNR or fare data** — patterns are qualitative.
            - **Sensitivity** — winners can move with demand, no-show, and overbooking assumptions.
            - **Scenario dependence** — conclusions are conditional on the named presets.
            - **No network effects** — single leg only (no connections, no fleet rotation).
            """
        ),
        encoding="utf-8",
    )

    (OUTPUT / "README.md").write_text(
        dedent(
            f"""\
            # Chat / report evidence bundle

            Minimal artifacts to support a defensible write-up. **Regenerate** after changing simulator or configs:

            ```bash
            cd airline_rm_project
            PYTHONPATH=src python -m airline_rm.evaluation.chat_exp_export
            ```

            | Path | Use |
            |------|-----|
            | `tables/scenario_policy_results.csv` | Primary numbers: profit, revenue, load, fare, bumps |
            | `tables/winner_summary.csv` | Who wins per scenario and key gaps |
            | `tables/validation_summary.csv` | Compressed robustness (from `reports/validation/` if present) |
            | `tables/config_snapshot.yaml` | Baseline effective parameters |
            | `figures/*.png` | One profit chart, three fare overlays, bump-risk bar |
            | `raw/minimal_run_sample.csv` | Tiny MC sample for sanity checks |
            | `key_results.md` | Bullet factual interpretation |
            | `methodology.md` | Short methods blurb |
            | `limitations.md` | Honest scope limits |

            Monte Carlo: **n_runs={N_RUNS}**, **seed {BASE_SEED}** (policy blocks as in main experiments).
            """
        ),
        encoding="utf-8",
    )

    return OUTPUT


def main() -> None:
    p = export_chat_exp()
    print(f"Wrote chat_exp bundle to {p.resolve()}")


if __name__ == "__main__":
    main()
