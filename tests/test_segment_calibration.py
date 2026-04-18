"""Calibration checks for business vs leisure accepted bookings (robust to RNG)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from airline_rm.config import load_simulation_config
from airline_rm.demand.segment_mix import SegmentMixModel
from airline_rm.demand.willingness_to_pay import WTPModel
from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.evaluation.diagnostics import summarize_accepted_segment_mix
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.simulation.runner import run_many

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_segment_mix_increases_toward_departure_not_instant_jump() -> None:
    mix = SegmentMixModel(
        booking_horizon_days=60,
        early_business_share=0.10,
        late_business_share=0.42,
        transition_midpoint_days=14.0,
        transition_steepness=0.24,
    )
    assert mix.business_share(60) < mix.business_share(15) < mix.business_share(1)


def test_leisure_wtp_can_clear_typical_fares_under_default_config() -> None:
    """Broad check: leisure WTP should exceed ~$200 often enough for non-degenerate conversion."""

    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    model = WTPModel.from_simulation_config(cfg)
    rng = np.random.default_rng(0)
    fares = (159.0, 189.0, 220.0)
    for fare in fares:
        samples = np.array([model.sample_wtp(PassengerSegment.LEISURE, rng) for _ in range(4000)])
        assert (samples >= fare).mean() > 0.08


def test_default_route_accepted_mix_not_business_dominated_over_many_runs() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
        demand_stochastic=True,
    )
    pol = StaticPricingPolicy(cfg)
    results = run_many(pol, cfg, n_runs=48, base_seed=2026)
    seg = summarize_accepted_segment_mix(results)

    assert 0.22 <= seg["mean_business_share_of_accepted"] <= 0.58
    assert seg["mean_accepted_leisure"] >= 25.0
    assert seg["mean_accepted_business"] >= 15.0


def test_summarize_segment_mix_rejects_empty() -> None:
    with pytest.raises(ValueError):
        summarize_accepted_segment_mix(())


def test_business_wtp_stochastically_exceeds_leisure_under_default_config() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    model = WTPModel.from_simulation_config(cfg)
    rng = np.random.default_rng(123)
    lb = np.array([model.sample_wtp(PassengerSegment.LEISURE, rng) for _ in range(2500)])
    bb = np.array([model.sample_wtp(PassengerSegment.BUSINESS, rng) for _ in range(2500)])
    assert bb.mean() > lb.mean()
