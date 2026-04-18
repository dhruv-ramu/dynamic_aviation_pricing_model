"""Command-line entrypoint for a single deterministic experiment run."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing import build_pricing_policy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator
from airline_rm.types import SimulationConfig


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single airline RM simulation experiment.")
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
        help="Override pricing_policy from config (static | rule_based | dynamic).",
    )
    return parser.parse_args()


def _with_policy_override(config: SimulationConfig, policy_name: str | None) -> SimulationConfig:
    if policy_name is None:
        return config
    return replace(config, pricing_policy=policy_name)


def main() -> None:
    args = _parse_args()
    base = load_simulation_config(args.config)
    config = _with_policy_override(base, args.policy)
    rng = make_generator(config)
    policy = build_pricing_policy(config)
    result = run_single_flight_simulation(config, policy, rng)
    metrics = compute_metrics(result)

    print("Airline RM — single flight experiment")
    print(f"  Config: {args.config.resolve()}")
    print(f"  Policy: {config.pricing_policy}")
    print(f"  Flight: {result.flight.flight_id} cap={result.flight.capacity}")
    print(f"  Horizon days: {result.booking_horizon_days}")
    print(f"  Seats sold: {result.seats_sold}")
    print(f"  Ticket revenue: ${result.total_ticket_revenue:,.2f}")
    print(f"  Ancillary revenue: ${result.total_ancillary_revenue:,.2f}")
    print(f"  Total cost: ${result.total_cost:,.2f}")
    print("---")
    print(f"  Load factor: {metrics.load_factor:.3f}")
    print(f"  Avg fare: ${metrics.avg_fare:,.2f}")
    print(f"  Total revenue: ${metrics.total_revenue:,.2f}")
    print(f"  Profit: ${metrics.profit:,.2f}")
    print(f"  Bookings (biz / leisure): {metrics.bookings_business} / {metrics.bookings_leisure}")
    print(f"  Sellout day (1-based horizon index): {metrics.sellout_day}")


if __name__ == "__main__":
    main()
