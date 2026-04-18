"""Generate report-ready artifacts under ``reports/final/`` (tables, figures, markdown).

Run from project root:
  PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
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

from airline_rm.config import load_raw_config, load_simulation_config
from airline_rm.evaluation.diagnostics import summarize_accepted_segment_mix
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.runner import run_many
from airline_rm.simulation.scenario import SCENARIO_PRESETS, apply_scenario
from airline_rm.types import SimulationConfig

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "base_config.yaml"
OUTPUT_ROOT = PROJECT_ROOT / "reports" / "final"

N_RUNS = 100
BASE_SEED = 2026

SCENARIOS: tuple[str, ...] = (
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

POLICY_ORDER: tuple[tuple[str, Any], ...] = (
    ("static", StaticPricingPolicy),
    ("rule_based", RuleBasedPricingPolicy),
    ("dynamic", DynamicPricingPolicy),
)
POLICY_MAP: dict[str, Any] = {name: cls for name, cls in POLICY_ORDER}

FIGURE_METRIC_FILES: tuple[tuple[str, str], ...] = (
    ("mean_profit", "scenario_policy_mean_profit.png"),
    ("mean_revenue", "scenario_policy_mean_revenue.png"),
    ("mean_boarded_load_factor", "scenario_policy_mean_boarded_load_factor.png"),
    ("mean_avg_fare", "scenario_policy_mean_avg_fare.png"),
    ("bump_risk", "scenario_policy_bump_risk.png"),
    ("mean_denied_boardings", "scenario_policy_mean_denied_boardings.png"),
)


def _policy_seed_block(policy_index: int) -> int:
    """Match ``compare_policies_monte_carlo`` seed blocks."""

    return int(BASE_SEED) + policy_index * 1_000_003


def _likely_regime(scenario: str) -> str:
    m = {
        "baseline": "baseline",
        "weak_demand": "weak demand",
        "strong_demand": "strong demand",
        "very_strong_late_demand": "late-demand-heavy",
        "high_no_show": "no-show-heavy",
        "low_no_show": "no-show-light",
        "business_heavy": "business-heavy mix",
        "leisure_heavy": "leisure-heavy mix",
        "higher_overbooking": "higher overbooking cap",
        "overbook_bump_stress": "bump-stress",
        "strong_competitor_pressure": "competitor-heavy",
    }
    return m.get(scenario, scenario)


def _takeaway_short(
    scenario: str,
    winner: str,
    d_rb: float,
    d_dyn: float,
    bump_dyn: float,
) -> str:
    parts = [f"Winner: {winner}."]
    if scenario == "overbook_bump_stress" and bump_dyn > 0.05:
        parts.append("Material bump risk under dynamic.")
    if abs(d_dyn - d_rb) < 200 and winner != "static":
        parts.append("Dynamic vs rule_based profit close.")
    if winner == "static":
        parts.append("Static list fare competitive on profit here.")
    return " ".join(parts)


def _collect_all(
    base_cfg: SimulationConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], list]]:
    """Return (policy_rows, run_rows, results_store)."""

    policy_rows: list[dict[str, Any]] = []
    run_rows: list[dict[str, Any]] = []
    results_store: dict[tuple[str, str], list] = {}

    for scen in SCENARIOS:
        cfg = replace(apply_scenario(base_cfg, scen), rng_seed=BASE_SEED)
        for pol_idx, (pname, PolCls) in enumerate(POLICY_ORDER):
            pol = PolCls(cfg)
            seed_block = _policy_seed_block(pol_idx)
            results = run_many(pol, cfg, n_runs=N_RUNS, base_seed=seed_block)
            results_store[(scen, pname)] = results
            metrics_list = [compute_metrics(r) for r in results]
            profits = np.array([m.profit for m in metrics_list], dtype=float)

            bump_risk = float(np.mean([m.denied_boardings > 0 for m in metrics_list]))
            policy_rows.append(
                {
                    "scenario": scen,
                    "policy": pname,
                    "mean_profit": float(np.mean(profits)),
                    "mean_revenue": float(np.mean([m.total_revenue for m in metrics_list])),
                    "mean_boarded_load_factor": float(np.mean([m.boarded_load_factor for m in metrics_list])),
                    "mean_accepted_booking_load_factor": float(
                        np.mean([m.accepted_booking_load_factor for m in metrics_list])
                    ),
                    "mean_booking_rate": float(np.mean([m.booking_rate for m in metrics_list])),
                    "mean_avg_fare": float(np.mean([m.avg_fare for m in metrics_list])),
                    "mean_denied_boardings": float(np.mean([m.denied_boardings for m in metrics_list])),
                    "bump_risk": bump_risk,
                    "mean_no_show_count": float(np.mean([m.no_shows for m in metrics_list])),
                    "mean_ticket_revenue": float(np.mean([m.ticket_revenue for m in metrics_list])),
                    "mean_ancillary_revenue": float(np.mean([m.ancillary_revenue for m in metrics_list])),
                    "mean_total_cost": float(np.mean([m.total_cost for m in metrics_list])),
                }
            )
            for run_id, (r, m) in enumerate(zip(results, metrics_list, strict=True)):
                run_rows.append(
                    {
                        "run_id": run_id,
                        "seed": int(seed_block + run_id),
                        "scenario": scen,
                        "policy": pname,
                        "profit": m.profit,
                        "revenue": m.total_revenue,
                        "boarded_load_factor": m.boarded_load_factor,
                        "accepted_booking_load_factor": m.accepted_booking_load_factor,
                        "booking_rate": m.booking_rate,
                        "avg_fare": m.avg_fare,
                        "denied_boardings": m.denied_boardings,
                        "no_show_count": m.no_shows,
                        "ticket_revenue": m.ticket_revenue,
                        "ancillary_revenue": m.ancillary_revenue,
                        "total_cost": m.total_cost,
                    }
                )

    return policy_rows, run_rows, results_store


def _winner_table(policy_df: pd.DataFrame) -> pd.DataFrame:
    p = policy_df.pivot(index="scenario", columns="policy", values="mean_profit")
    rows = []
    policy_names = ("static", "rule_based", "dynamic")
    for scen in p.index:
        profits_by = {name: float(p.loc[scen, name]) for name in policy_names}
        s, rb, d = profits_by["static"], profits_by["rule_based"], profits_by["dynamic"]
        best_val = max(profits_by.values())
        best: str | None = None
        for name in policy_names:
            if np.isclose(profits_by[name], best_val, rtol=1e-12, atol=1e-9):
                best = name
                break
        assert best is not None
        rows.append(
            {
                "scenario": scen,
                "winner": best,
                "mean_profit_static": s,
                "mean_profit_rule_based": rb,
                "mean_profit_dynamic": d,
                "rule_based_minus_static": rb - s,
                "dynamic_minus_static": d - s,
                "dynamic_minus_rule_based": d - rb,
            }
        )
    return pd.DataFrame(rows)


def _profit_delta_wide(winner_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scenario": winner_df["scenario"],
            "profit_static": winner_df["mean_profit_static"],
            "delta_rule_minus_static": winner_df["rule_based_minus_static"],
            "delta_dynamic_minus_static": winner_df["dynamic_minus_static"],
        }
    )


def _scenario_summary(policy_df: pd.DataFrame, winner_df: pd.DataFrame) -> pd.DataFrame:
    dyn = policy_df[policy_df["policy"] == "dynamic"].set_index("scenario")
    rb = policy_df[policy_df["policy"] == "rule_based"].set_index("scenario")
    out = []
    for _, w in winner_df.iterrows():
        scen = str(w["scenario"])
        d_gap = float(dyn.loc[scen, "mean_profit"]) - float(rb.loc[scen, "mean_profit"])
        out.append(
            {
                "scenario": scen,
                "likely_regime_type": _likely_regime(scen),
                "winner": w["winner"],
                "key_takeaway_short": _takeaway_short(
                    scen,
                    str(w["winner"]),
                    float(w["rule_based_minus_static"]),
                    float(w["dynamic_minus_static"]),
                    float(dyn.loc[scen, "bump_risk"]),
                ),
                "bump_risk_dynamic": float(dyn.loc[scen, "bump_risk"]),
                "mean_denied_dynamic": float(dyn.loc[scen, "mean_denied_boardings"]),
                "mean_book_rate_dynamic": float(dyn.loc[scen, "mean_booking_rate"]),
                "dynamic_vs_rule_profit_gap": d_gap,
            }
        )
    return pd.DataFrame(out)


def _bump_table(policy_df: pd.DataFrame) -> pd.DataFrame:
    return policy_df[
        [
            "scenario",
            "policy",
            "bump_risk",
            "mean_denied_boardings",
            "mean_accepted_booking_load_factor",
            "mean_boarded_load_factor",
        ]
    ].copy()


def _segment_table(results_store: dict[tuple[str, str], list]) -> pd.DataFrame:
    rows = []
    for scen in SCENARIOS:
        for pname, _ in POLICY_ORDER:
            mix = summarize_accepted_segment_mix(results_store[(scen, pname)])
            rows.append({"scenario": scen, "policy": pname, **mix})
    return pd.DataFrame(rows)


def _config_effective_rows(base_cfg: SimulationConfig) -> pd.DataFrame:
    cols = [
        "expected_total_demand",
        "demand_multiplier",
        "no_show_mean",
        "overbooking_limit_pct",
        "early_business_share",
        "late_business_share",
        "booking_curve_midpoint",
        "booking_curve_steepness",
        "leisure_wtp_mean",
        "business_wtp_mean",
        "competitor_mode",
        "competitor_response_strength",
    ]
    rows = []
    for scen in SCENARIOS:
        cfg = replace(apply_scenario(base_cfg, scen), rng_seed=BASE_SEED)
        row: dict[str, Any] = {"scenario": scen}
        for c in cols:
            row[c] = getattr(cfg, c)
        rows.append(row)
    return pd.DataFrame(rows)


def _metric_definitions() -> pd.DataFrame:
    defs: list[dict[str, str]] = [
        {
            "metric_name": "mean_profit",
            "plain_english_definition": "Average accounting profit per Monte Carlo run.",
            "formula_or_description": "total_revenue - total_cost per run, then mean over runs.",
            "interpretation_note": "Higher is better; includes denied-boarding and goodwill costs when applicable.",
        },
        {
            "metric_name": "mean_revenue",
            "plain_english_definition": "Average ticket plus ancillary revenue per run.",
            "formula_or_description": "ticket_revenue + ancillary_revenue from compute_metrics.",
            "interpretation_note": "Does not subtract operating or bump costs.",
        },
        {
            "metric_name": "mean_boarded_load_factor",
            "plain_english_definition": "Boarded passengers divided by physical cabin seats.",
            "formula_or_description": "boarded_passengers / physical_capacity.",
            "interpretation_note": "Can exceed 1.0 only if modeling artifact; here capped by simulation logic to cabin.",
        },
        {
            "metric_name": "mean_accepted_booking_load_factor",
            "plain_english_definition": "Accepted bookings divided by physical seats (not booking limit).",
            "formula_or_description": "bookings_accepted / physical_capacity.",
            "interpretation_note": "Values above 1 indicate selling past cabin capacity before no-shows.",
        },
        {
            "metric_name": "mean_booking_rate",
            "plain_english_definition": "Accepted bookings as a fraction of the booking limit.",
            "formula_or_description": "bookings_accepted / booking_limit.",
            "interpretation_note": "Near 1 means frequent sell-up against the authorization cap (overbooking pool).",
        },
        {
            "metric_name": "mean_avg_fare",
            "plain_english_definition": "Average realized ticket yield per accepted booking.",
            "formula_or_description": "ticket_revenue / bookings_accepted.",
            "interpretation_note": "Mix of bucket choices, conversion, and capacity binding.",
        },
        {
            "metric_name": "mean_denied_boardings",
            "plain_english_definition": "Mean count of involuntarily denied boardings per run.",
            "formula_or_description": "Departure-day outcome when show-ups exceed physical seats.",
            "interpretation_note": "Drives compensation and goodwill costs in total_cost.",
        },
        {
            "metric_name": "bump_risk",
            "plain_english_definition": "Fraction of Monte Carlo runs with at least one denied boarding.",
            "formula_or_description": "mean(1[denied_boardings > 0]).",
            "interpretation_note": "Operational tail risk indicator.",
        },
        {
            "metric_name": "mean_no_show_count",
            "plain_english_definition": "Average realized no-shows per run.",
            "formula_or_description": "Sampled from binomial model at departure.",
            "interpretation_note": "Interacts with overbooking to set bump frequency.",
        },
        {
            "metric_name": "mean_ticket_revenue",
            "plain_english_definition": "Average ticket (fare) revenue per run.",
            "formula_or_description": "Sum of accepted booking fares per run, then mean.",
            "interpretation_note": "Excludes ancillary; before denied-boarding refunds if modeled.",
        },
        {
            "metric_name": "mean_ancillary_revenue",
            "plain_english_definition": "Average total ancillary revenue per run.",
            "formula_or_description": "Each accepted booking adds `ancillary_mean` at sale; sum over the run.",
            "interpretation_note": "Scales with accepted bookings, not boarded bodies.",
        },
        {
            "metric_name": "mean_total_cost",
            "plain_english_definition": "Average total operating plus bump-related cost per run.",
            "formula_or_description": "CASM-based operating cost plus denied-boarding compensation and goodwill.",
            "interpretation_note": "Subtract from revenue to reconcile to profit where definitions align.",
        },
    ]
    return pd.DataFrame(defs)


def _plot_grouped_bars(
    policy_df: pd.DataFrame,
    value_col: str,
    ylabel: str,
    title: str,
    path: Path,
) -> None:
    pivot = policy_df.pivot(index="scenario", columns="policy", values=value_col)
    scenarios = list(pivot.index)
    x = np.arange(len(scenarios))
    width = 0.25
    fig, ax = plt.subplots(figsize=(max(11.0, len(scenarios) * 1.05), 5.2))
    for i, pol in enumerate(["static", "rule_based", "dynamic"]):
        if pol in pivot.columns:
            ax.bar(x + (i - 1) * width, pivot[pol].values, width=width, label=pol)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=40, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_profit_delta(winner_df: pd.DataFrame, path: Path) -> None:
    scenarios = winner_df["scenario"].tolist()
    x = np.arange(len(scenarios))
    width = 0.35
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    ax.bar(x - width / 2, winner_df["rule_based_minus_static"], width=width, label="rule_based - static")
    ax.bar(x + width / 2, winner_df["dynamic_minus_static"], width=width, label="dynamic - static")
    ax.axhline(0.0, color="k", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=40, ha="right")
    ax.set_ylabel("Profit delta ($)")
    ax.set_title("Mean profit vs static (by scenario)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _representative_run_id(profits: np.ndarray) -> int:
    mean_p = float(np.mean(profits))
    return int(np.argmin(np.abs(profits - mean_p)))


def _fare_trajectory_single(
    cfg: SimulationConfig,
    policy_name: str,
    run_id: int,
    pol_idx: int,
) -> tuple[np.ndarray, np.ndarray]:
    pol = POLICY_MAP[policy_name](cfg)
    seed_block = _policy_seed_block(pol_idx)
    rng = np.random.default_rng(int(seed_block + run_id))
    result = run_single_flight_simulation(cfg, pol, rng)
    fares = np.array(result.fare_series, dtype=float)
    h = len(fares)
    days = np.linspace(1, int(cfg.booking_horizon_days), num=h)
    return days, fares


def _export_fare_trajectories_csv(
    base_cfg: SimulationConfig,
    scenarios: Sequence[str],
    out_csv: Path,
) -> None:
    rows: list[dict[str, Any]] = []
    h = int(base_cfg.booking_horizon_days)
    for scen in scenarios:
        cfg = replace(apply_scenario(base_cfg, scen), rng_seed=BASE_SEED)
        for pname in ("rule_based", "dynamic"):
            pol_idx = 1 if pname == "rule_based" else 2
            results = run_many(POLICY_MAP[pname](cfg), cfg, N_RUNS, _policy_seed_block(pol_idx))
            profits = np.array([compute_metrics(r).profit for r in results])
            rid = _representative_run_id(profits)
            _, fares_arr = _fare_trajectory_single(cfg, pname, rid, pol_idx)
            for sales_day, fare in enumerate(fares_arr.tolist(), start=1):
                dtd = h - sales_day + 1
                rows.append(
                    {
                        "scenario": scen,
                        "policy": pname,
                        "sales_day": sales_day,
                        "day_to_departure": dtd,
                        "fare": float(fare),
                        "trajectory_id": rid,
                    }
                )
    pd.DataFrame(rows).to_csv(out_csv, index=False)


def _plot_fare_overlay(
    base_cfg: SimulationConfig,
    scenario: str,
    out_path: Path,
) -> None:
    cfg = replace(apply_scenario(base_cfg, scenario), rng_seed=BASE_SEED)
    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    for pname, pol_idx in (("rule_based", 1), ("dynamic", 2)):
        results = run_many(POLICY_MAP[pname](cfg), cfg, N_RUNS, _policy_seed_block(pol_idx))
        profits = np.array([compute_metrics(r).profit for r in results])
        rid = _representative_run_id(profits)
        days, fares = _fare_trajectory_single(cfg, pname, rid, pol_idx)
        ax.plot(days, fares, label=f"{pname} (run {rid})", linewidth=1.3)
    ax.set_xlabel("Sales day (linearly spaced over horizon)")
    ax.set_ylabel("Quoted fare ($)")
    ax.set_title(f"Fare paths — {scenario} (run closest to each policy mean profit)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_booking_vs_boarded(run_df: pd.DataFrame, scenario: str, out_path: Path) -> None:
    sub = run_df[run_df["scenario"] == scenario]
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    for pname, c in (("static", "C0"), ("rule_based", "C1"), ("dynamic", "C2")):
        s2 = sub[sub["policy"] == pname]
        ax.scatter(
            s2["accepted_booking_load_factor"],
            s2["boarded_load_factor"],
            s=22,
            alpha=0.45,
            label=pname,
            c=c,
        )
    lim = max(sub["accepted_booking_load_factor"].max(), sub["boarded_load_factor"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", linewidth=0.8, label="y=x (no gap)")
    ax.set_xlabel("Accepted booking load factor (vs physical seats)")
    ax.set_ylabel("Boarded load factor (vs physical seats)")
    ax.set_title(f"Booking vs boarded — {scenario}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_profit_distribution(run_df: pd.DataFrame, scenario: str, out_path: Path) -> None:
    sub = run_df[run_df["scenario"] == scenario]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for pname in ("static", "rule_based", "dynamic"):
        vals = sub[sub["policy"] == pname]["profit"].values
        ax.hist(vals, bins=18, alpha=0.38, label=pname)
    ax.set_xlabel("Profit ($)")
    ax.set_ylabel("Count")
    ax.set_title(f"Profit distribution — {scenario} (n={N_RUNS} per policy)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_denied_distribution(run_df: pd.DataFrame, out_path: Path) -> None:
    sub = run_df[run_df["scenario"] == "overbook_bump_stress"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for pname in ("static", "rule_based", "dynamic"):
        vals = sub[sub["policy"] == pname]["denied_boardings"].values
        vmax = int(max(4, vals.max()) + 1) if len(vals) else 4
        ax.hist(vals, bins=np.arange(-0.5, vmax + 0.5), alpha=0.4, label=pname)
    ax.set_xlabel("Denied boardings (count)")
    ax.set_ylabel("Runs")
    ax.set_title("Denied boarding distribution — overbook_bump_stress")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _write_readme_inventory(out_root: Path) -> None:
    paths = sorted(
        {p.relative_to(out_root).as_posix() for p in out_root.rglob("*") if p.is_file()} | {"README.md"}
    )
    body = dedent(
        f"""\
        # Final report artifact bundle

        Generated for **Monte Carlo**: `n_runs={N_RUNS}`, `seed_block = {BASE_SEED} + policy_index*1_000_003` (same as `compare_policies_monte_carlo`), `SimulationConfig.rng_seed={BASE_SEED}` after scenario apply.

        ## Regenerate

        ```bash
        cd airline_rm_project
        PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
        ```

        ## Trajectory convention

        Fare trajectory figures and `raw_exports/fare_trajectories_sampled.csv` use, **per policy**, the run whose realized **profit** is closest to that policy's mean profit (`trajectory_id` / `representative_run_id`). Rule-based and dynamic may use **different** run indices.

        ## Complete file inventory

        """
    )
    body += "\n".join(f"- `{p}`" for p in paths)
    (out_root / "README.md").write_text(body, encoding="utf-8")


def _write_markdown_templates(
    out_root: Path,
    policy_df: pd.DataFrame,
    winner_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:

    top_winners = winner_df["winner"].value_counts().to_string()
    best_dyn = summary_df.loc[summary_df["dynamic_vs_rule_profit_gap"].idxmax()]
    worst_dyn = summary_df.loc[summary_df["dynamic_vs_rule_profit_gap"].idxmin()]
    (out_root / "executive_summary.md").write_text(
        dedent(
            f"""\
            # Executive summary — factual bullets for the report writer

            ## Strongest findings (quantitative)

            - Winner counts across scenarios (by mean profit):  
            ```
            {top_winners}
            ```
            - Largest **dynamic minus rule_based** mean-profit gap (scenario: `{best_dyn["scenario"]}`): **{best_dyn["dynamic_vs_rule_profit_gap"]:,.2f}** USD.
            - Most negative dynamic vs rule gap (`{worst_dyn["scenario"]}`): **{worst_dyn["dynamic_vs_rule_profit_gap"]:,.2f}** USD.

            ## Surprising / scenario-dependent

            - `overbook_bump_stress`: compare **bump_risk** and **mean_denied_boardings** across policies in `tables/bump_risk_table.csv` — static vs dynamic pricing interacts with sell-up and IDB costs differently than mid-fare heuristics.
            - `strong_competitor_pressure` + reactive competitor: check fare and profit deltas vs baseline.

            ## Weakest / most uncertain

            - Single-leg, synthetic demand and WTP — not an econometric fit to a real market.
            - Fare trajectories are **single representative runs** per policy, not ensemble bands.
            - No network spill, no multi-leg, no government policy shocks.
            """
        ),
        encoding="utf-8",
    )

    (out_root / "methodology.md").write_text(
        dedent(
            f"""\
            # Methodology

            ## Simulator and config

            - Merged YAML: `configs/base_config.yaml` (extends `route_shorthaul_default.yaml`).
            - Full merged snapshot: `tables/config_snapshot_base.yaml`.

            ## Policies

            - **static**: fixed bucket from config (default max fare bucket).
            - **rule_based**: time/load heuristic ladder + mild competitor reaction.
            - **dynamic**: stateful score controller (pace, scarcity, demand pressure; weak competitor nudge).

            ## Scenarios

            Presets from `airline_rm.simulation.scenario.SCENARIO_PRESETS` applied via `dataclasses.replace`. Effective parameters per scenario: `tables/config_snapshot_effective_by_scenario.csv`.

            ## Monte Carlo

            - Replications: **{N_RUNS}** per scenario-policy pair.
            - RNG: `numpy.random.default_rng(seed_block + run_id)` with `seed_block = {BASE_SEED} + policy_index * 1_000_003`, `run_id = 0..{N_RUNS - 1}` — matches `run_many` / `compare_policies_monte_carlo` policy separation.
            - After scenario overrides, `SimulationConfig.rng_seed` set to **{BASE_SEED}** (for any code paths that read it; primary randomness is the injected Generator).

            ## Aggregated metrics

            - Per run: `compute_metrics` on `FlightSimulationResult`.
            - Table means: arithmetic mean across runs unless noted.

            ## Representative fare trajectories

            For each scenario and each of **rule_based** and **dynamic**:
            1. Re-run the same `{N_RUNS}` Monte Carlo block.
            2. Choose `representative_run_id = argmin_k |profit_k − mean(profit)|`.
            3. Re-simulate once with `Generator(seed_block + representative_run_id)` and export `fare_series`.

            Plots overlay both policies’ chosen runs (possibly different `representative_run_id`). See `raw_exports/fare_trajectories_sampled.csv` for long form.
            """
        ),
        encoding="utf-8",
    )

    (out_root / "assumptions_and_limitations.md").write_text(
        dedent(
            """\
            # Assumptions and limitations

            - **Synthetic calibration**: route YAML is illustrative, not fitted to a carrier PNR extract.
            - **Demand / WTP**: logistic booking curve, Poisson arrivals (if stochastic), segment mix, and lognormal WTP draws are stylized approximations.
            - **Scenario dependence**: results are conditional on discrete presets; small parameter shifts can reorder winners.
            - **Overbooking realism**: fixed percentage cap on accepted bookings vs cabin; no re-accommodation, no voluntary denied boarding modeling.
            - **No network effects**: isolated leg; no connecting traffic or hub gate constraints.
            - **No industrial optimization**: policies are heuristics, not a CDLP/DP/choice-optimizer benchmark.
            """
        ),
        encoding="utf-8",
    )

    scen_lines = ["# Scenario definitions\n"]
    for scen in SCENARIOS:
        ov = SCENARIO_PRESETS.get(scen, {})
        scen_lines.append(f"## `{scen}`\n")
        scen_lines.append(f"- **Overrides**: `{ov}`\n" if ov else "- **Overrides**: none (baseline)\n")
        scen_lines.append(f"- **Intent**: {_likely_regime(scen)} stress-test.\n")
    (out_root / "scenario_definitions.md").write_text("\n".join(scen_lines), encoding="utf-8")

    findings = ["# Key findings (draft bullets)\n"]
    for _, w in winner_df.iterrows():
        scen = w["scenario"]
        s = summary_df[summary_df["scenario"] == scen].iloc[0]
        findings.append(f"## {scen}\n")
        findings.append(f"- **Winner (mean profit)**: {w['winner']}\n")
        findings.append(
            f"- **Profit gaps vs static**: rule_based Δ {w['rule_based_minus_static']:,.0f}; dynamic Δ {w['dynamic_minus_static']:,.0f} USD.\n"
        )
        findings.append(f"- **Dynamic vs rule_based gap**: {s['dynamic_vs_rule_profit_gap']:,.0f} USD.\n")
        findings.append(f"- **Dynamic bump risk**: {s['bump_risk_dynamic']:.3f}; mean denied (dynamic): {s['mean_denied_dynamic']:.3f}.\n")
        findings.append(f"- **Note**: {s['key_takeaway_short']}\n")
    (out_root / "key_findings.md").write_text("".join(findings), encoding="utf-8")


def _write_appendices(out_root: Path, policy_df: pd.DataFrame) -> None:
    app = out_root / "appendices"
    app.mkdir(parents=True, exist_ok=True)
    (app / "monte_carlo_settings.md").write_text(
        dedent(
            f"""\
            # Monte Carlo settings

            - `n_runs`: **{N_RUNS}**
            - `BASE_SEED` (policy blocks): **{BASE_SEED}**
            - Per-policy `seed_block`: `{BASE_SEED} + policy_index * 1_000_003`
            - Per-run RNG: `default_rng(seed_block + run_id)` for `run_id` in `0..{N_RUNS - 1}`
            - Policies: static, rule_based, dynamic
            - Scenarios: {", ".join(SCENARIOS)}
            """
        ),
        encoding="utf-8",
    )
    (app / "policy_descriptions.md").write_text(
        dedent(
            """\
            # Policy descriptions (plain English)

            ## static
            Quotes a fixed fare bucket for the entire horizon (default: highest bucket). Does not react to load, time, or competitor. Useful as a high-list-price baseline.

            ## rule_based
            Maps time-to-departure and seat slack to a fare bucket using transparent thresholds, then applies a mild competitor undercut response. Designed to mimic a simple revenue-management playbook.

            ## dynamic
            Stateful controller: yesterday’s bucket carries forward. Each day adjusts using compact scores for booking pace vs the curve, physical-seat scarcity, and residual demand pressure vs seats left. Competitor influence is capped and muted late in the horizon. Aims for profit-oriented seat protection rather than pure load-chasing.
            """
        ),
        encoding="utf-8",
    )
    pivot = policy_df.pivot(index="scenario", columns="policy", values="mean_profit")
    (app / "scenario_matrix_full.md").write_text(
        "# Scenario × policy — mean profit\n\n```\n" + pivot.to_string(float_format=lambda x: f"{x:,.2f}") + "\n```\n",
        encoding="utf-8",
    )
    (app / "reproducibility.md").write_text(
        dedent(
            """\
            # Reproducibility

            From the `airline_rm_project` directory:

            ```bash
            PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
            ```

            This overwrites `reports/final/` tables, figures, markdown, and raw exports using the committed simulator code and `configs/base_config.yaml`.
            """
        ),
        encoding="utf-8",
    )


def export_final_bundle(
    *,
    config_path: Path = DEFAULT_CONFIG,
    output_root: Path = OUTPUT_ROOT,
) -> None:
    shutil.rmtree(output_root, ignore_errors=True)
    tables = output_root / "tables"
    figures = output_root / "figures"
    raw = output_root / "raw_exports"
    app = output_root / "appendices"
    for d in (tables, figures, raw, app):
        d.mkdir(parents=True, exist_ok=True)

    base_cfg = load_simulation_config(config_path)
    base_cfg = replace(base_cfg, rng_seed=BASE_SEED)

    policy_rows, run_rows, results_store = _collect_all(base_cfg)
    policy_df = pd.DataFrame(policy_rows)
    run_df = pd.DataFrame(run_rows)

    policy_df.to_csv(tables / "policy_results_by_scenario.csv", index=False)
    run_df.to_csv(raw / "run_level_results_full.csv", index=False)
    policy_df.to_csv(raw / "scenario_policy_results_full.csv", index=False)

    winner_df = _winner_table(policy_df)
    winner_df.to_csv(tables / "winner_table.csv", index=False)
    _profit_delta_wide(winner_df).to_csv(tables / "profit_delta_vs_static.csv", index=False)

    summary_df = _scenario_summary(policy_df, winner_df)
    summary_df.to_csv(tables / "scenario_summary_table.csv", index=False)
    _bump_table(policy_df).to_csv(tables / "bump_risk_table.csv", index=False)
    _segment_table(results_store).to_csv(tables / "segment_mix_table.csv", index=False)
    _config_effective_rows(base_cfg).to_csv(tables / "config_snapshot_effective_by_scenario.csv", index=False)
    _metric_definitions().to_csv(tables / "metric_definitions.csv", index=False)

    raw_yaml = load_raw_config(config_path)
    with (tables / "config_snapshot_base.yaml").open("w", encoding="utf-8") as fh:
        yaml.safe_dump(raw_yaml, fh, default_flow_style=False, sort_keys=False)

    for col, fname in FIGURE_METRIC_FILES:
        titles = {
            "mean_profit": ("Mean profit ($)", "Mean profit by scenario and policy"),
            "mean_revenue": ("Mean revenue ($)", "Mean revenue by scenario and policy"),
            "mean_boarded_load_factor": ("Mean boarded load factor", "Mean boarded load factor"),
            "mean_avg_fare": ("Mean avg fare ($)", "Mean average fare"),
            "bump_risk": ("Bump risk (fraction of runs)", "Bump risk (denied > 0)"),
            "mean_denied_boardings": ("Mean denied boardings", "Mean denied boardings"),
        }
        ylab, title = titles[col]
        _plot_grouped_bars(policy_df, col, ylab, title, figures / fname)

    _plot_profit_delta(winner_df, figures / "profit_delta_vs_static.png")

    for scen in ("baseline", "strong_demand", "very_strong_late_demand", "overbook_bump_stress"):
        _plot_fare_overlay(base_cfg, scen, figures / f"fare_trajectory_rule_vs_dynamic__{scen}.png")

    for scen in ("baseline", "strong_demand", "very_strong_late_demand", "overbook_bump_stress"):
        _plot_booking_vs_boarded(run_df, scen, figures / f"booking_vs_boarded_load_factor__{scen}.png")

    _plot_denied_distribution(run_df, figures / "denied_boarding_distribution__overbook_bump_stress.png")

    for scen in ("baseline", "strong_demand", "very_strong_late_demand", "overbook_bump_stress"):
        _plot_profit_distribution(run_df, scen, figures / f"profit_distribution__{scen}.png")

    _export_fare_trajectories_csv(
        base_cfg,
        ("baseline", "strong_demand", "very_strong_late_demand", "overbook_bump_stress"),
        raw / "fare_trajectories_sampled.csv",
    )

    _write_markdown_templates(output_root, policy_df, winner_df, summary_df)
    _write_appendices(output_root, policy_df)
    _write_readme_inventory(output_root)


def main() -> None:
    export_final_bundle()


if __name__ == "__main__":
    main()
