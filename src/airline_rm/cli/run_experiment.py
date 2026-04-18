"""Command-line entrypoint for a single deterministic experiment run."""

from __future__ import annotations

import argparse
from pathlib import Path

from airline_rm.config import load_simulation_config
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single airline RM simulation experiment.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/base_config.yaml"),
        help="Path to YAML config (may use extends).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = load_simulation_config(args.config)
    rng = make_generator(config)
    policy = StaticPricingPolicy(config)
    result = run_single_flight_simulation(config, policy, rng)
    metrics = compute_metrics(result)

    print("Airline RM — single flight experiment")
    print(f"  Config: {args.config.resolve()}")
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


if __name__ == "__main__":
    main()
