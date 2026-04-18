"""Single-parameter sweeps with small Monte Carlo replication."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Sequence

import numpy as np
import pandas as pd

from airline_rm.evaluation.metrics import compute_metrics
from airline_rm.pricing import build_pricing_policy
from airline_rm.simulation.runner import run_many, summarize_results
from airline_rm.types import SimulationConfig

SUPPORTED_SWEEP_PARAMS: frozenset[str] = frozenset(
    {
        "no_show_mean",
        "expected_total_demand",
        "early_business_share",
        "late_business_share",
        "overbooking_limit_pct",
    }
)


def sweep_parameter(
    config: SimulationConfig,
    param_name: str,
    values: Sequence[Any],
    *,
    n_runs: int = 5,
    base_seed: int = 0,
) -> pd.DataFrame:
    """Sweep ``param_name`` over ``values`` for the configured policy; aggregate with ``n_runs`` each."""

    pname = str(param_name).strip()
    if pname not in SUPPORTED_SWEEP_PARAMS:
        raise KeyError(f"Unsupported sweep parameter {param_name!r}. Supported: {sorted(SUPPORTED_SWEEP_PARAMS)}")

    rows: list[dict[str, object]] = []

    for v in values:
        cfg = replace(config, **{pname: v})
        pol = build_pricing_policy(cfg)
        results = run_many(pol, cfg, n_runs=n_runs, base_seed=base_seed)
        summary = summarize_results(results)
        m0 = compute_metrics(results[0])
        rows.append(
            {
                "param": pname,
                "value": v,
                "mean_profit": summary["mean_profit"],
                "mean_boarded_load_factor": summary["mean_boarded_load_factor"],
                "mean_denied_boardings": summary["mean_denied_boardings"],
                "bump_risk": summary["bump_risk"],
                "mean_no_show_count": summary["mean_no_show_count"],
                "bookings_business_sample": m0.bookings_business,
                "bookings_leisure_sample": m0.bookings_leisure,
            }
        )

    return pd.DataFrame(rows)
