"""Tests for WTP conversion and WTP distribution ordering."""

from __future__ import annotations

import numpy as np
import pytest

from airline_rm.demand.conversion import BookingConverter
from airline_rm.demand.willingness_to_pay import WTPModel
from airline_rm.entities.passenger_segment import PassengerSegment


def test_threshold_conversion() -> None:
    c = BookingConverter()
    assert c.will_book(100.0, 100.0) is True
    assert c.will_book(100.0, 99.99) is False
    assert c.will_book(0.0, 5.0) is True


def test_conversion_rejects_negative_inputs() -> None:
    c = BookingConverter()
    with pytest.raises(ValueError):
        c.will_book(-1.0, 50.0)
    with pytest.raises(ValueError):
        c.will_book(50.0, -1.0)


def test_business_wtp_exceeds_leisure_on_average() -> None:
    model = WTPModel(
        leisure_wtp_mean=150.0,
        leisure_wtp_sigma=40.0,
        business_wtp_mean=320.0,
        business_wtp_sigma=80.0,
    )
    rng = np.random.default_rng(12345)
    n = 8000
    leisure = np.array([model.sample_wtp(PassengerSegment.LEISURE, rng) for _ in range(n)])
    business = np.array([model.sample_wtp(PassengerSegment.BUSINESS, rng) for _ in range(n)])
    assert business.mean() > leisure.mean()
