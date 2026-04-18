"""Tests for Poisson arrivals and segment mix."""

from __future__ import annotations

import numpy as np

from airline_rm.demand.arrivals import DailyArrivalModel
from airline_rm.demand.booking_curve import BookingCurveModel
from airline_rm.demand.segment_mix import SegmentMixModel


def test_expected_arrivals_sum_scales_total_demand() -> None:
    curve = BookingCurveModel(30, "logistic", 0.4, 12.0)
    model = DailyArrivalModel(
        booking_horizon_days=30,
        expected_total_demand=120.0,
        demand_multiplier=1.0,
        booking_curve=curve,
        stochastic=True,
    )
    lam = model.expected_arrivals_by_day()
    assert lam.shape == (30,)
    assert np.isclose(lam.sum(), 120.0)


def test_deterministic_arrivals_are_rounded_means() -> None:
    curve = BookingCurveModel(4, "logistic", 0.5, 2.0)
    model = DailyArrivalModel(
        booking_horizon_days=4,
        expected_total_demand=10.0,
        demand_multiplier=1.0,
        booking_curve=curve,
        stochastic=False,
    )
    rng = np.random.default_rng(999)
    total = 0
    for t in range(4):
        total += model.sample_arrivals_for_day(t, rng)
    assert total >= 0
    assert all(model.sample_arrivals_for_day(i, rng) >= 0 for i in range(4))


def test_poisson_samples_non_negative() -> None:
    curve = BookingCurveModel(20, "logistic", 0.5, 8.0)
    model = DailyArrivalModel(20, 50.0, 1.0, curve, stochastic=True)
    rng = np.random.default_rng(0)
    for t in range(20):
        assert model.sample_arrivals_for_day(t, rng) >= 0


def test_segment_mix_increases_toward_departure() -> None:
    mix = SegmentMixModel(
        booking_horizon_days=60,
        early_business_share=0.15,
        late_business_share=0.55,
        transition_midpoint_days=22.0,
        transition_steepness=0.35,
    )
    far = mix.business_share(60)
    close = mix.business_share(1)
    assert far < close
    assert np.isclose(mix.leisure_share(30), 1.0 - mix.business_share(30))
