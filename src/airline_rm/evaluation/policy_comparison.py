"""Run the same configuration under multiple pricing policies and summarize KPIs."""

from __future__ import annotations

import pandas as pd

from airline_rm.config import SimulationConfig
from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.pricing_policy_base import PricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.engine import run_single_flight_simulation
from airline_rm.simulation.random_state import make_generator


def compare_default_policies(config: SimulationConfig) -> pd.DataFrame:
    """Simulate static, rule-based, and dynamic policies with independent RNG draws per row."""

    policies: dict[str, PricingPolicy] = {
        "static": StaticPricingPolicy(config),
        "rule_based": RuleBasedPricingPolicy(config),
        "dynamic": DynamicPricingPolicy(config),
    }

    rows: list[dict[str, object]] = []
    for name, policy in policies.items():
        rng = make_generator(config)
        result = run_single_flight_simulation(config, policy, rng)
        metrics = compute_metrics(result)
        rows.append(
            {
                "policy": name,
                "seats_sold": result.seats_sold,
                "load_factor": metrics.load_factor,
                "avg_fare": metrics.avg_fare,
                "total_revenue": metrics.total_revenue,
                "profit": metrics.profit,
            }
        )

    return pd.DataFrame(rows)
