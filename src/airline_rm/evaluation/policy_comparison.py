"""Policy comparison: single-shot and Monte Carlo summaries."""

from __future__ import annotations

import numpy as np
import pandas as pd

from airline_rm.types import SimulationConfig
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.pricing_policy_base import PricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator
from airline_rm.simulation.runner import run_many, summarize_results


def compare_default_policies(config: SimulationConfig) -> pd.DataFrame:
    """One simulation per policy (independent RNG streams from ``config.rng_seed``)."""

    policies: dict[str, PricingPolicy] = {
        "static": StaticPricingPolicy(config),
        "rule_based": RuleBasedPricingPolicy(config),
        "dynamic": DynamicPricingPolicy(config),
    }

    rows: list[dict[str, object]] = []
    for name, policy in policies.items():
        rng = make_generator(config)
        result = run_single_flight_simulation(config, policy, rng)
        m = compute_metrics(result)
        rows.append(
            {
                "policy": name,
                "bookings_accepted": m.bookings_accepted,
                "mean_boarded_load_factor": m.boarded_load_factor,
                "mean_accepted_booking_load_factor": m.accepted_booking_load_factor,
                "mean_avg_fare": m.avg_fare,
                "mean_revenue": m.total_revenue,
                "mean_profit": m.profit,
                "mean_denied_boardings": float(m.denied_boardings),
                "bump_risk": float(m.denied_boardings > 0),
                "mean_no_show_count": float(m.no_shows),
            }
        )

    return pd.DataFrame(rows)


def compare_policies_monte_carlo(
    config: SimulationConfig,
    n_runs: int,
    base_seed: int = 0,
) -> pd.DataFrame:
    """``n_runs`` replications per policy with reproducible, separated seed blocks."""

    policies: dict[str, PricingPolicy] = {
        "static": StaticPricingPolicy(config),
        "rule_based": RuleBasedPricingPolicy(config),
        "dynamic": DynamicPricingPolicy(config),
    }

    rows: list[dict[str, object]] = []
    for idx, (name, policy) in enumerate(policies.items()):
        seed_block = int(base_seed) + idx * 1_000_003
        results = run_many(policy, config, n_runs=n_runs, base_seed=seed_block)
        summary = summarize_results(results)
        mean_rev = float(np.mean([compute_metrics(r).total_revenue for r in results]))
        rows.append(
            {
                "policy": name,
                "mean_profit": summary["mean_profit"],
                "mean_revenue": mean_rev,
                "mean_boarded_load_factor": summary["mean_boarded_load_factor"],
                "mean_avg_fare": summary["mean_avg_fare"],
                "mean_denied_boardings": summary["mean_denied_boardings"],
                "bump_risk": summary["bump_risk"],
            }
        )

    return pd.DataFrame(rows)
