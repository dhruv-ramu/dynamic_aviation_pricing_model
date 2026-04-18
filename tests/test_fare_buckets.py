"""Tests for the fare bucket ladder."""

from __future__ import annotations

import pytest

from airline_rm.pricing.fare_buckets import FareBucketSystem


def test_fares_sorted_cheapest_at_zero() -> None:
    sys = FareBucketSystem.from_values((220.0, 119.0, 159.0))
    assert sys.fares == (119.0, 159.0, 220.0)
    assert sys.current_fare(0) == 119.0
    assert sys.current_fare(sys.max_bucket()) == 220.0


def test_clamp_and_moves() -> None:
    sys = FareBucketSystem.from_values((100.0, 200.0, 300.0))
    assert sys.raise_bucket(2, 5) == 2
    assert sys.lower_bucket(0, 3) == 0
    assert sys.raise_bucket(0, 1) == 1
    assert sys.lower_bucket(2, 1) == 1
    assert sys.clamp_bucket_index(99) == 2


def test_bucket_for_load_and_time() -> None:
    sys = FareBucketSystem.from_values((100.0, 200.0, 300.0))
    cheap = sys.bucket_for_load_and_time(
        50,
        95,
        100,
        early_window_days=45,
        late_window_days=14,
        low_load_factor_threshold=0.35,
        high_load_factor_threshold=0.85,
    )
    assert cheap == 0
    tight = sys.bucket_for_load_and_time(
        30,
        10,
        100,
        early_window_days=45,
        late_window_days=14,
        low_load_factor_threshold=0.35,
        high_load_factor_threshold=0.85,
    )
    assert tight == 2


def test_rejects_non_positive_fares() -> None:
    with pytest.raises(ValueError):
        FareBucketSystem.from_values((100.0, 0.0))
