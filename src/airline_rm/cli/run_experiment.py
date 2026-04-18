"""Command-line entrypoint for single runs, Monte Carlo batches, and policy comparison."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.diagnostics import summarize_accepted_segment_mix
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.evaluation.policy_comparison import compare_default_policies, compare_policies_monte_carlo
from airline_rm.evaluation.sensitivity import sweep_parameter
from airline_rm.pricing import build_pricing_policy
from airline_rm.entities.simulation_state import FlightSimulationResult
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator
from airline_rm.simulation.runner import run_many, summarize_results
from airline_rm.simulation.scenario import apply_scenario
from airline_rm.types import SimulationConfig


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Airline RM simulation experiments.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/base_config.yaml"),
        help="Path to YAML config (may use extends).",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=None,
        choices=("static", "rule_based", "dynamic"),
        help="Override pricing_policy from config.",
    )
    parser.add_argument("--n-runs", type=int, default=1, help="Monte Carlo replications (>=1).")
    parser.add_argument(
        "--compare-policies",
        action="store_true",
        help="Compare static, rule-based, and dynamic policies.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Named scenario preset (see simulation.scenario.SCENARIO_PRESETS).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override rng_seed in config for reproducibility.",
    )
    parser.add_argument(
        "--sweep-param",
        type=str,
        default=None,
        help="If set with --sweep-values, run sensitivity sweep (e.g. no_show_mean).",
    )
    parser.add_argument(
        "--sweep-values",
        type=str,
        default=None,
        help="Comma-separated values for --sweep-param (e.g. 0.05,0.10,0.15).",
    )
    return parser.parse_args()


def _apply_overrides(base: SimulationConfig, args: argparse.Namespace) -> SimulationConfig:
    cfg = base
    if args.scenario:
        cfg = apply_scenario(cfg, args.scenario)
    if args.seed is not None:
        cfg = replace(cfg, rng_seed=int(args.seed))
    if args.policy is not None:
        cfg = replace(cfg, pricing_policy=args.policy)
    return cfg


def _print_single_run_summary(
    config: SimulationConfig, result: FlightSimulationResult, metrics: object
) -> None:
    print("Airline RM — single flight")
    print(f"  Config rng_seed: {config.rng_seed}")
    print(f"  Policy: {config.pricing_policy}")
    print(f"  Physical capacity / booking limit: {result.physical_capacity} / {result.booking_limit}")
    print(f"  Bookings accepted: {result.bookings_accepted}")
    print(f"  No-shows / boarded / denied: {result.no_shows} / {result.boarded_passengers} / {result.denied_boardings}")
    print(f"  Denied-boarding cost: ${result.denied_boarding_cost:,.2f}")
    print(f"  Ticket / ancillary revenue: ${metrics.ticket_revenue:,.2f} / ${metrics.ancillary_revenue:,.2f}")
    print(f"  Total cost (incl. bump penalties): ${metrics.total_cost:,.2f}")
    print(f"  Profit: ${metrics.profit:,.2f}")
    print("--- load factors ---")
    print(f"  Accepted-booking LF (vs physical seats): {metrics.accepted_booking_load_factor:.3f}")
    print(f"  Boarded LF (vs physical seats): {metrics.boarded_load_factor:.3f}")
    print(f"  Booking rate (accepted / booking limit): {metrics.booking_rate:.3f}")
    print(f"  Realized no-show rate: {metrics.no_show_rate_realized:.3f}")
    print(f"  Biz / leisure accepted: {metrics.bookings_business} / {metrics.bookings_leisure}")


def main() -> None:
    args = _parse_args()
    base = load_simulation_config(args.config)
    config = _apply_overrides(base, args)

    if args.sweep_param and args.sweep_values:
        values = [float(x.strip()) if "." in x.strip() else int(x.strip()) for x in args.sweep_values.split(",")]
        df = sweep_parameter(config, args.sweep_param, values, n_runs=max(3, min(args.n_runs, 10)), base_seed=config.rng_seed)
        print(df.to_string(index=False))
        return

    if args.compare_policies:
        if args.n_runs <= 1:
            df = compare_default_policies(config)
        else:
            df = compare_policies_monte_carlo(config, n_runs=args.n_runs, base_seed=config.rng_seed)
        print(df.to_string(index=False))
        return

    policy = build_pricing_policy(config)

    if args.n_runs > 1:
        results = run_many(policy, config, n_runs=args.n_runs, base_seed=config.rng_seed)
        summary = summarize_results(results)
        print(pd.Series(summary).to_string())
        seg = summarize_accepted_segment_mix(results)
        print("--- accepted segment mix (Monte Carlo) ---")
        print(f"  mean_accepted_business: {seg['mean_accepted_business']:.2f}")
        print(f"  mean_accepted_leisure: {seg['mean_accepted_leisure']:.2f}")
        print(f"  mean_business_share_of_accepted: {seg['mean_business_share_of_accepted']:.3f}")
        print(f"  mean_leisure_share_of_accepted: {seg['mean_leisure_share_of_accepted']:.3f}")
        return

    rng = make_generator(config)
    result = run_single_flight_simulation(config, policy, rng)
    metrics = compute_metrics(result)
    _print_single_run_summary(config, result, metrics)


if __name__ == "__main__":
    main()
