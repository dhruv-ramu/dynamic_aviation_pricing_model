"""No-show Binomial model tests."""

from __future__ import annotations

import numpy as np
import pytest

from airline_rm.revenue.no_show import NoShowModel


def test_no_show_bounds() -> None:
    m = NoShowModel(0.2)
    rng = np.random.default_rng(0)
    for booked in (0, 1, 50, 200):
        ns = m.sample_no_shows(booked, rng)
        assert 0 <= ns <= booked
        brd = m.boarded_count(booked, rng)
        assert 0 <= brd <= booked


def test_zero_booked() -> None:
    m = NoShowModel(0.5)
    rng = np.random.default_rng(1)
    assert m.sample_no_shows(0, rng) == 0
    assert m.boarded_count(0, rng) == 0


def test_invalid_probability() -> None:
    with pytest.raises(ValueError):
        NoShowModel(1.5)
