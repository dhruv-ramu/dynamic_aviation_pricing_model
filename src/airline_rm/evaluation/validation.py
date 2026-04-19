"""Validation, robustness, and statistical checks for Monte Carlo policy comparisons.

Does not alter simulator logic — measures and reports only. Writes CSVs under ``reports/validation/``.
"""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.evaluation.scenario_comparison import (
    DEFAULT_SCENARIO_ORDER,
    compare_policies_across_scenarios,
    scenario_winner_table,
)
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.runner import run_many
from airline_rm.simulation.scenario import SCENARIO_PRESETS, apply_scenario
from airline_rm.types import SimulationConfig

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "validation"

POLICY_CLASSES: tuple[tuple[str, Any], ...] = (
    ("static", StaticPricingPolicy),
    ("rule_based", RuleBasedPricingPolicy),
    ("dynamic", DynamicPricingPolicy),
)

STABILITY_LEVELS: tuple[int, ...] = (50, 100, 200, 500)
SEED_LIST: tuple[int, ...] = (1, 42, 2026, 7777, 9999)

# Reference seed for "changed vs" comparisons in summaries
REFERENCE_SEED = 2026


def _policy_seed_block(base_seed: int, policy_index: int) -> int:
    return int(base_seed) + policy_index * 1_000_003


def _t_crit_95(df: int) -> float:
    """Two-sided 95% Student t critical value (approximation for df >= 1)."""
    if df < 1:
        return float("nan")
    # Normal approximation for large df
    if df >= 120:
        return 1.959964
    # Short table (two-sided 95%)
    table = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        15: 2.131,
        20: 2.086,
        25: 2.060,
        30: 2.042,
        40: 2.021,
        60: 2.000,
        80: 1.990,
        100: 1.984,
    }
    keys = sorted(table.keys())
    if df in table:
        return float(table[df])
    for k in keys:
        if k > df:
            return float(table[k])
    return 1.984


def _ci95_mean(x: np.ndarray) -> tuple[float, float, float, float]:
    """Return mean, std (sample), se, half-width of 95% CI (t on mean)."""
    x = np.asarray(x, dtype=float)
    n = x.size
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    mu = float(np.mean(x))
    if n == 1:
        return mu, 0.0, 0.0, 0.0
    s = float(np.std(x, ddof=1))
    se = s / math.sqrt(n)
    hw = _t_crit_95(n - 1) * se
    return mu, s, se, hw


def _coef_variation(mean: float, std: float) -> float:
    if mean == 0.0 or (isinstance(mean, float) and math.isnan(mean)):
        return float("nan")
    return std / abs(mean)


def _run_policy_profits(
    cfg: SimulationConfig,
    *,
    n_runs: int,
    base_seed: int,
) -> dict[str, np.ndarray]:
    """Per-policy profit vectors (same ``n_runs``, separated seed blocks)."""

    out: dict[str, np.ndarray] = {}
    for idx, (name, cls) in enumerate(POLICY_CLASSES):
        pol = cls(cfg)
        seed_block = _policy_seed_block(base_seed, idx)
        results = run_many(pol, cfg, n_runs=n_runs, base_seed=seed_block)
        out[name] = np.array([compute_metrics(r).profit for r in results], dtype=float)
    return out


def _run_policy_full_metrics(
    cfg: SimulationConfig,
    *,
    n_runs: int,
    base_seed: int,
) -> dict[str, dict[str, np.ndarray]]:
    """Per-policy arrays for profit decomposition."""

    out: dict[str, dict[str, np.ndarray]] = {}
    for idx, (name, cls) in enumerate(POLICY_CLASSES):
        pol = cls(cfg)
        seed_block = _policy_seed_block(base_seed, idx)
        results = run_many(pol, cfg, n_runs=n_runs, base_seed=seed_block)
        mlist = [compute_metrics(r) for r in results]
        out[name] = {
            "profit": np.array([m.profit for m in mlist], dtype=float),
            "ticket_revenue": np.array([m.ticket_revenue for m in mlist], dtype=float),
            "ancillary_revenue": np.array([m.ancillary_revenue for m in mlist], dtype=float),
            "total_cost": np.array([m.total_cost for m in mlist], dtype=float),
            "denied_boarding_cost": np.array([m.denied_boarding_cost for m in mlist], dtype=float),
        }
    return out


def build_monte_carlo_stability(
    base_cfg: SimulationConfig,
    *,
    max_runs: int = 500,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prefix statistics at 50/100/200/500 from the same RNG stream (first ``max_runs`` per policy)."""

    rows: list[dict[str, Any]] = []
    winner_rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)
    mr = min(max_runs, max(STABILITY_LEVELS))

    for scenario in DEFAULT_SCENARIO_ORDER:
        if scenario not in SCENARIO_PRESETS:
            continue
        cfg = replace(apply_scenario(base_cfg, scenario), rng_seed=base_seed)
        policy_means_at_n: dict[int, dict[str, float]] = {}

        for pol_idx, (policy, _) in enumerate(POLICY_CLASSES):
            pol = POLICY_CLASSES[pol_idx][1](cfg)
            seed_block = _policy_seed_block(base_seed, pol_idx)
            results = run_many(pol, cfg, n_runs=mr, base_seed=seed_block)
            profits = np.array([compute_metrics(r).profit for r in results], dtype=float)

            for n in STABILITY_LEVELS:
                if n > mr:
                    continue
                sub = profits[:n]
                mu, std, _se, hw = _ci95_mean(sub)
                cv = _coef_variation(mu, std)
                rows.append(
                    {
                        "scenario": scenario,
                        "policy": policy,
                        "n_runs": n,
                        "mean_profit": mu,
                        "std_profit": std,
                        "coef_of_variation": cv,
                        "ci95_low": mu - hw,
                        "ci95_high": mu + hw,
                    }
                )
                if n not in policy_means_at_n:
                    policy_means_at_n[n] = {}
                policy_means_at_n[n][policy] = mu

        w_at_max = None
        max_n = max([x for x in STABILITY_LEVELS if x <= mr], default=0)
        if max_n in policy_means_at_n:
            mmax = policy_means_at_n[max_n]
            w_at_max = max(mmax, key=lambda k: mmax[k])
        w500 = None
        if 500 in policy_means_at_n:
            m5 = policy_means_at_n[500]
            w500 = max(m5, key=lambda k: m5[k])

        for n in STABILITY_LEVELS:
            if n > mr or n not in policy_means_at_n:
                continue
            means = policy_means_at_n[n]
            w = max(means, key=lambda k: means[k])
            differs = False
            if w500 is not None and n != 500:
                differs = w != w500
            winner_rows.append(
                {
                    "scenario": scenario,
                    "n_runs": n,
                    "winner_by_mean_profit": w,
                    "winner_at_max_prefix_length": w_at_max,
                    "max_prefix_n_available": max_n,
                    "ranking_differs_from_winner_at_n500": differs,
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(winner_rows)


def build_seed_sensitivity(
    base_cfg: SimulationConfig,
    *,
    seeds: tuple[int, ...] = SEED_LIST,
    n_runs: int,
) -> pd.DataFrame:
    """Winner and mean profits per scenario for each RNG seed (aggregate Monte Carlo)."""

    cfg_ref = replace(base_cfg, rng_seed=REFERENCE_SEED)
    long_ref = compare_policies_across_scenarios(cfg_ref, n_runs=n_runs, base_seed=REFERENCE_SEED)
    ref_winners = {str(r["scenario"]): str(r["winner"]) for _, r in scenario_winner_table(long_ref).iterrows()}

    rows: list[dict[str, Any]] = []
    for seed in seeds:
        cfg = replace(base_cfg, rng_seed=int(seed))
        long_df = compare_policies_across_scenarios(cfg, n_runs=n_runs, base_seed=int(seed))
        wtab = scenario_winner_table(long_df)
        for _, r in wtab.iterrows():
            scen = str(r["scenario"])
            win = str(r["winner"])
            rows.append(
                {
                    "seed": seed,
                    "scenario": scen,
                    "winner": win,
                    "mean_profit_static": float(r["mean_profit_static"]),
                    "mean_profit_rule_based": float(r["mean_profit_rule_based"]),
                    "mean_profit_dynamic": float(r["mean_profit_dynamic"]),
                    "winner_differs_from_seed_2026": ref_winners.get(scen) != win,
                }
            )

    return pd.DataFrame(rows)


def build_parameter_sensitivity(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """One-parameter grids on baseline scenario; compare three policies."""

    cfg0 = replace(apply_scenario(base_cfg, "baseline"), rng_seed=int(base_cfg.rng_seed))
    etd0 = float(cfg0.expected_total_demand)
    dm0 = float(cfg0.demand_multiplier)
    ns0 = float(cfg0.no_show_mean)
    ob0 = float(cfg0.overbooking_limit_pct)
    lw0 = float(cfg0.leisure_wtp_mean)
    bw0 = float(cfg0.business_wtp_mean)

    grids: list[tuple[str, list[float]]] = [
        ("expected_total_demand", [etd0 * (0.8 + 0.1 * i) for i in range(5)]),
        ("demand_multiplier", [0.85 + 0.05 * i for i in range(8)]),
        ("no_show_mean", [0.03 + 0.17 / 6 * i for i in range(7)]),
        ("overbooking_limit_pct", [0.0 + 0.15 / 7 * i for i in range(8)]),
        ("leisure_wtp_mean", [lw0 * m for m in (0.85, 0.9, 1.0, 1.1, 1.15)]),
        ("business_wtp_mean", [bw0 * m for m in (0.85, 0.9, 1.0, 1.1, 1.15)]),
    ]

    rows: list[dict[str, Any]] = []
    mc = max(25, min(n_runs, 80))

    for param, values in grids:
        for v in values:
            try:
                cfg = replace(cfg0, **{param: float(v)})
            except (TypeError, ValueError):
                continue
            profits_mean: dict[str, float] = {}
            for idx, (name, cls) in enumerate(POLICY_CLASSES):
                pol = cls(cfg)
                sb = _policy_seed_block(int(cfg.rng_seed), idx)
                results = run_many(pol, cfg, n_runs=mc, base_seed=sb)
                profits_mean[name] = float(np.mean([compute_metrics(r).profit for r in results]))
            s = profits_mean["static"]
            rows.append(
                {
                    "parameter": param,
                    "parameter_value": float(v),
                    "n_runs": mc,
                    "mean_profit_static": s,
                    "mean_profit_rule_based": profits_mean["rule_based"],
                    "mean_profit_dynamic": profits_mean["dynamic"],
                    "delta_rule_minus_static": profits_mean["rule_based"] - s,
                    "delta_dynamic_minus_static": profits_mean["dynamic"] - s,
                    "delta_dynamic_minus_rule": profits_mean["dynamic"] - profits_mean["rule_based"],
                }
            )

    return pd.DataFrame(rows)


def build_scenario_robustness(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """Slight perturbations to selected presets; compare winner to unperturbed."""

    perturbations: list[tuple[str, str, dict[str, Any]]] = [
        ("strong_demand", "strong_demand_etd_minus_10pct", {"expected_total_demand": 255.0 * 0.9}),
        ("strong_demand", "strong_demand_etd_plus_10pct", {"expected_total_demand": 255.0 * 1.1}),
        ("overbook_bump_stress", "bump_stress_ns_higher", {"no_show_mean": 0.065}),
        ("overbook_bump_stress", "bump_stress_ns_lower", {"no_show_mean": 0.03}),
        ("very_strong_late_demand", "late_dm_minus", {"demand_multiplier": 1.05}),
        ("very_strong_late_demand", "late_dm_plus", {"demand_multiplier": 1.18}),
    ]

    rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)

    def winner_for(cfg: SimulationConfig) -> tuple[str, dict[str, float]]:
        pm = {}
        for idx, (name, cls) in enumerate(POLICY_CLASSES):
            pol = cls(cfg)
            sb = _policy_seed_block(base_seed, idx)
            results = run_many(pol, cfg, n_runs=n_runs, base_seed=sb)
            pm[name] = float(np.mean([compute_metrics(r).profit for r in results]))
        w = max(pm, key=lambda k: pm[k])
        return w, pm

    for base_scen, label, overrides in perturbations:
        if base_scen not in SCENARIO_PRESETS:
            continue
        cfg_base = replace(apply_scenario(base_cfg, base_scen), rng_seed=base_seed)
        w0, p0 = winner_for(cfg_base)
        cfg_p = replace(cfg_base, **overrides)
        w1, p1 = winner_for(cfg_p)
        rows.append(
            {
                "base_scenario": base_scen,
                "perturbation_label": label,
                "winner_baseline": w0,
                "winner_perturbed": w1,
                "winner_unchanged": w0 == w1,
                "mean_profit_static_base": p0["static"],
                "mean_profit_rule_base": p0["rule_based"],
                "mean_profit_dynamic_base": p0["dynamic"],
                "mean_profit_static_pert": p1["static"],
                "mean_profit_rule_pert": p1["rule_based"],
                "mean_profit_dynamic_pert": p1["dynamic"],
            }
        )

    return pd.DataFrame(rows)


def build_edge_cases(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """Extreme parameter sets; record crashes and coarse sanity."""

    cases: list[tuple[str, dict[str, Any]]] = [
        ("near_zero_demand", {"expected_total_demand": 8.0}),
        ("extreme_high_demand", {"expected_total_demand": 420.0, "demand_multiplier": 1.35}),
        ("zero_no_show", {"no_show_mean": 0.0}),
        ("very_high_no_show", {"no_show_mean": 0.33}),
        ("no_competitor", {"competitor_mode": "none"}),
        (
            "hyper_reactive_competitor",
            {
                "competitor_mode": "reactive",
                "competitor_response_strength": 0.92,
                "competitor_base_offset": -48.0,
                "competitor_noise_std": 10.0,
            },
        ),
    ]

    rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)
    mc = max(15, min(n_runs, 40))

    for label, overrides in cases:
        err = ""
        means: dict[str, float] = {}
        try:
            cfg = replace(apply_scenario(base_cfg, "baseline"), rng_seed=base_seed, **overrides)
            for idx, (name, cls) in enumerate(POLICY_CLASSES):
                pol = cls(cfg)
                sb = _policy_seed_block(base_seed, idx)
                results = run_many(pol, cfg, n_runs=mc, base_seed=sb)
                profits = [compute_metrics(r).profit for r in results]
                means[name] = float(np.mean(profits))
                if any(not math.isfinite(p) for p in profits):
                    err = "non_finite_profit"
        except Exception as e:  # noqa: BLE001 — validation harness
            err = f"{type(e).__name__}: {e}"
            means = {n: float("nan") for n, _ in POLICY_CLASSES}

        absurd = ""
        if means:
            mx = max(abs(means.get("static", 0.0)), abs(means.get("rule_based", 0.0)), abs(means.get("dynamic", 0.0)))
            if mx > 1e9:
                absurd = "very_large_profit_magnitude"
            if any(means.get(p, 0.0) < -1e7 for p, _ in POLICY_CLASSES):
                absurd = (absurd + " very_negative_profit").strip()

        rows.append(
            {
                "case_name": label,
                "n_runs": mc,
                "error": err,
                "sanity_flag": absurd,
                "mean_profit_static": means.get("static", float("nan")),
                "mean_profit_rule_based": means.get("rule_based", float("nan")),
                "mean_profit_dynamic": means.get("dynamic", float("nan")),
            }
        )

    return pd.DataFrame(rows)


def build_profit_decomposition(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """Mean revenue/cost components by scenario and policy."""

    rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)

    for scenario in DEFAULT_SCENARIO_ORDER:
        if scenario not in SCENARIO_PRESETS:
            continue
        cfg = replace(apply_scenario(base_cfg, scenario), rng_seed=base_seed)
        full = _run_policy_full_metrics(cfg, n_runs=n_runs, base_seed=base_seed)
        for pol in ("static", "rule_based", "dynamic"):
            d = full[pol]
            ticket_m = float(np.mean(d["ticket_revenue"]))
            anc_m = float(np.mean(d["ancillary_revenue"]))
            cost_m = float(np.mean(d["total_cost"]))
            dbc_m = float(np.mean(d["denied_boarding_cost"]))
            prof_m = float(np.mean(d["profit"]))
            identity = ticket_m + anc_m - cost_m
            rows.append(
                {
                    "scenario": scenario,
                    "policy": pol,
                    "n_runs": n_runs,
                    "mean_ticket_revenue": ticket_m,
                    "mean_ancillary_revenue": anc_m,
                    "mean_total_cost": cost_m,
                    "mean_denied_boarding_cost": dbc_m,
                    "mean_profit": prof_m,
                    "identity_ticket_plus_anc_minus_cost": identity,
                    "identity_minus_mean_profit": identity - prof_m,
                }
            )

    return pd.DataFrame(rows)


def build_winner_consistency(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """Per-run winner counts (independent policy RNG streams)."""

    rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)

    for scenario in DEFAULT_SCENARIO_ORDER:
        if scenario not in SCENARIO_PRESETS:
            continue
        cfg = replace(apply_scenario(base_cfg, scenario), rng_seed=base_seed)
        profs = _run_policy_profits(cfg, n_runs=n_runs, base_seed=base_seed)
        wins = {p: 0 for p, _ in POLICY_CLASSES}
        ties = 0
        for i in range(n_runs):
            vals = {p: float(profs[p][i]) for p, _ in POLICY_CLASSES}
            m = max(vals.values())
            leaders = [p for p, v in vals.items() if v == m]
            if len(leaders) > 1:
                ties += 1
            else:
                wins[leaders[0]] += 1
        for p, _ in POLICY_CLASSES:
            rows.append(
                {
                    "scenario": scenario,
                    "policy": p,
                    "n_runs": n_runs,
                    "win_count": wins[p],
                    "win_rate": wins[p] / float(n_runs),
                    "tie_runs": ties,
                }
            )

    return pd.DataFrame(rows)


def build_statistical_tests(
    base_cfg: SimulationConfig,
    *,
    n_runs: int,
) -> pd.DataFrame:
    """Paired dynamic − rule_based profit differences per scenario."""

    rows: list[dict[str, Any]] = []
    base_seed = int(base_cfg.rng_seed)

    for scenario in DEFAULT_SCENARIO_ORDER:
        if scenario not in SCENARIO_PRESETS:
            continue
        cfg = replace(apply_scenario(base_cfg, scenario), rng_seed=base_seed)
        profs = _run_policy_profits(cfg, n_runs=n_runs, base_seed=base_seed)
        d = profs["dynamic"] - profs["rule_based"]
        mu, std, se, hw = _ci95_mean(d)
        t_stat = mu / se if se and se > 0 else float("nan")
        rows.append(
            {
                "scenario": scenario,
                "n_runs": n_runs,
                "mean_diff_dynamic_minus_rule": mu,
                "std_diff": std,
                "stderr": se,
                "t_statistic_vs_zero": t_stat,
                "ci95_low": mu - hw,
                "ci95_high": mu + hw,
            }
        )

    return pd.DataFrame(rows)


def write_validation_summary_md(
    out_dir: Path,
    *,
    dfs: dict[str, pd.DataFrame],
) -> None:
    """Markdown narrative from computed tables."""

    lines: list[str] = [
        "# Validation summary",
        "",
        "Auto-generated from validation CSVs. **Interpretation:** paired policy comparisons use the same run index "
        "across policies but **different RNG streams** (policy seed blocks), so per-run “wins” are indicative—not a "
        "common random path experiment.",
        "",
    ]

    seed_df = dfs.get("seed")
    if seed_df is not None and not seed_df.empty:
        flips = int(
            seed_df[
                (seed_df["winner_differs_from_seed_2026"] == True) & (seed_df["seed"] != REFERENCE_SEED)  # noqa: E712
            ].shape[0]
        )
        lines += [
            "## Seed sensitivity",
            f"- **{flips}** (scenario, seed) cells where seed ≠ {REFERENCE_SEED} and winner differs from the "
            f"reference run at seed {REFERENCE_SEED}.",
            "",
        ]

    wc = dfs.get("winner_consistency")
    if wc is not None and not wc.empty:
        # scenarios where max win_rate < 0.5 (no majority)
        mx = wc.groupby("scenario")["win_rate"].max()
        borderline = [s for s, v in mx.items() if v < 0.45]
        lines += [
            "## Winner consistency (per-run)",
            f"- Scenarios with **max win_rate below 0.45** (no policy dominates run-by-run): {', '.join(borderline) or 'none'}.",
            "",
        ]

    st = dfs.get("stats")
    if st is not None and not st.empty:
        sig = st[st["ci95_low"].notna() & (st["ci95_high"].notna())]
        sig = sig[(sig["ci95_low"] > 0) | (sig["ci95_high"] < 0)]
        lines += [
            "## Dynamic vs rule-based (paired difference of profits)",
            f"- Scenarios where **95% CI for (dynamic − rule) excludes zero**: {', '.join(sig['scenario'].astype(str)) or 'none'}.",
            "",
        ]

    rob = dfs.get("robustness")
    if rob is not None and not rob.empty:
        unchanged = int(rob["winner_unchanged"].sum())
        lines += [
            "## Scenario perturbations",
            f"- Perturbations with **same winner** as baseline: **{unchanged} / {len(rob)}**.",
            "",
        ]

    stab_w = dfs.get("stability_winners")
    if stab_w is not None and not stab_w.empty and "ranking_differs_from_winner_at_n500" in stab_w.columns:
        diff = stab_w[stab_w["ranking_differs_from_winner_at_n500"] == True]  # noqa: E712
        lines += [
            "## Monte Carlo stability (prefix lengths)",
            f"- Scenario×n rows where **winner at n ≠ winner at n=500**: **{len(diff)}**.",
            "",
        ]

    lines += [
        "## Strongest vs weakest claims",
        "- **Strongest:** scenarios where paired CI excludes zero and perturbations preserve the winner.",
        "- **Weakest / borderline:** high per-run tie counts, seed flips, or winner changes between n=50 and n=500.",
        "",
    ]

    (out_dir / "validation_summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_validation_suite(
    base_cfg: SimulationConfig,
    *,
    output_dir: Path | None = None,
    n_runs: int = 100,
    stability_max_runs: int = 500,
) -> dict[str, Path]:
    """Run all validation blocks and write CSVs + ``validation_summary.md``."""

    out = output_dir or DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    base_cfg = replace(base_cfg, rng_seed=int(base_cfg.rng_seed))

    print("Validation: Monte Carlo stability (prefixes)...", flush=True)
    stab, stab_win = build_monte_carlo_stability(base_cfg, max_runs=stability_max_runs)
    stab.to_csv(out / "validation_monte_carlo_stability.csv", index=False)
    stab_win.to_csv(out / "validation_monte_carlo_stability_winners.csv", index=False)

    print("Validation: seed sensitivity...", flush=True)
    seed_df = build_seed_sensitivity(base_cfg, seeds=SEED_LIST, n_runs=n_runs)
    seed_df.to_csv(out / "validation_seed_sensitivity.csv", index=False)

    print("Validation: parameter sweeps...", flush=True)
    param_df = build_parameter_sensitivity(base_cfg, n_runs=n_runs)
    param_df.to_csv(out / "validation_parameter_sensitivity.csv", index=False)

    print("Validation: scenario robustness...", flush=True)
    rob_df = build_scenario_robustness(base_cfg, n_runs=n_runs)
    rob_df.to_csv(out / "validation_scenario_robustness.csv", index=False)

    print("Validation: edge cases...", flush=True)
    edge_df = build_edge_cases(base_cfg, n_runs=n_runs)
    edge_df.to_csv(out / "validation_edge_cases.csv", index=False)

    print("Validation: profit decomposition...", flush=True)
    decomp = build_profit_decomposition(base_cfg, n_runs=n_runs)
    decomp.to_csv(out / "validation_profit_decomposition.csv", index=False)

    print("Validation: winner consistency...", flush=True)
    wc = build_winner_consistency(base_cfg, n_runs=n_runs)
    wc.to_csv(out / "validation_winner_consistency.csv", index=False)

    print("Validation: statistical tests...", flush=True)
    stats = build_statistical_tests(base_cfg, n_runs=n_runs)
    stats.to_csv(out / "validation_statistical_tests.csv", index=False)

    dfs = {
        "seed": seed_df,
        "winner_consistency": wc,
        "stats": stats,
        "robustness": rob_df,
        "stability_winners": stab_win,
    }
    write_validation_summary_md(out, dfs=dfs)

    print(f"Wrote validation artifacts to {out.resolve()}", flush=True)
    names = (
        "validation_monte_carlo_stability.csv",
        "validation_monte_carlo_stability_winners.csv",
        "validation_seed_sensitivity.csv",
        "validation_parameter_sensitivity.csv",
        "validation_scenario_robustness.csv",
        "validation_edge_cases.csv",
        "validation_profit_decomposition.csv",
        "validation_winner_consistency.csv",
        "validation_statistical_tests.csv",
        "validation_summary.md",
    )
    return {n: out / n for n in names}
