"""Tests for the logistic booking curve."""

from __future__ import annotations

import numpy as np
import pytest

from airline_rm.demand.booking_curve import BookingCurveModel


def test_daily_weights_sum_to_one() -> None:
    curve = BookingCurveModel(
        booking_horizon_days=60,
        curve_type="logistic",
        steepness=0.45,
        midpoint=18.0,
    )
    w = curve.daily_weights()
    assert w.shape == (60,)
    assert np.isclose(w.sum(), 1.0)
    assert bool(np.all(w > 0))


def test_intensity_rises_toward_departure() -> None:
    """First sales day is far out (d=H); last day is close-in (d=1): close-in weight should be larger."""

    curve = BookingCurveModel(60, "logistic", 0.45, 18.0)
    w = curve.daily_weights()
    assert w[-1] > w[0]


def test_incremental_and_cumulative_shares() -> None:
    curve = BookingCurveModel(10, "logistic", 0.5, 5.0)
    total = 0.0
    for d in range(10, 0, -1):
        total += curve.incremental_share(d)
    assert np.isclose(total, 1.0)
    assert np.isclose(curve.cumulative_share(1), 1.0)
    assert np.isclose(curve.cumulative_share(10), curve.incremental_share(10))


def test_invalid_curve_type() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        BookingCurveModel(5, "exponential", 1.0, 2.0)  # type: ignore[arg-type]
