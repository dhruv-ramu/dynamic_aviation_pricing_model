"""Monte Carlo replication helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from airline_rm.entities.simulation_state import FlightSimulationResult
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.pricing_policy_base import PricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.types import SimulationConfig


def run_many(
    policy: PricingPolicy,
    config: SimulationConfig,
    n_runs: int,
    base_seed: int,
) -> list[FlightSimulationResult]:
    """Run ``n_runs`` independent simulations with seeds ``base_seed + i``."""

    if n_runs < 1:
        raise ValueError("n_runs must be >= 1")
    results = []
    for i in range(n_runs):
        rng = np.random.default_rng(int(base_seed) + i)
        results.append(run_single_flight_simulation(config, policy, rng))
    return results


def summarize_results(results: list[FlightSimulationResult]) -> dict[str, float]:
    """Aggregate mean/std of key metrics across simulation results."""

    if not results:
        raise ValueError("results must be non-empty")

    metrics_list = [compute_metrics(r) for r in results]
    profits = np.array([m.profit for m in metrics_list], dtype=float)
    acc_lf = np.array([m.accepted_booking_load_factor for m in metrics_list])
    bd_lf = np.array([m.boarded_load_factor for m in metrics_list])
    avg_fares = np.array([m.avg_fare for m in metrics_list])
    denied = np.array([m.denied_boardings for m in metrics_list], dtype=float)
    nosh = np.array([m.no_shows for m in metrics_list], dtype=float)
    book_rate = np.array([m.booking_rate for m in metrics_list], dtype=float)

    bump_risk = float(np.mean(denied > 0.0))

    return {
        "mean_profit": float(np.mean(profits)),
        "std_profit": float(np.std(profits, ddof=0)),
        "mean_accepted_booking_load_factor": float(np.mean(acc_lf)),
        "mean_boarded_load_factor": float(np.mean(bd_lf)),
        "mean_booking_rate": float(np.mean(book_rate)),
        "mean_avg_fare": float(np.mean(avg_fares)),
        "mean_denied_boardings": float(np.mean(denied)),
        "bump_risk": bump_risk,
        "mean_no_show_count": float(np.mean(nosh)),
    }


def summarize_results_dataframe(results: list[FlightSimulationResult]) -> pd.DataFrame:
    """Per-run metrics as a DataFrame (useful for diagnostics)."""

    rows = []
    for r in results:
        m = compute_metrics(r)
        rows.append(
            {
                "profit": m.profit,
                "accepted_booking_load_factor": m.accepted_booking_load_factor,
                "boarded_load_factor": m.boarded_load_factor,
                "avg_fare": m.avg_fare,
                "denied_boardings": m.denied_boardings,
                "no_shows": m.no_shows,
            }
        )
    return pd.DataFrame(rows)
