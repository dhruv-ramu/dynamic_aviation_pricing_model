"""Overbooking limits and denied boarding cost tests."""

from __future__ import annotations

import pytest

from airline_rm.revenue.denied_boarding_cost import DeniedBoardingCostModel
from airline_rm.revenue.overbooking import OverbookingModel


def test_booking_limit_disabled_matches_capacity() -> None:
    ob = OverbookingModel(enabled=False, limit_pct=0.10)
    assert ob.booking_limit(180) == 180


def test_booking_limit_with_margin() -> None:
    ob = OverbookingModel(enabled=True, limit_pct=0.03)
    assert ob.booking_limit(180) == 180 + int(180 * 0.03)


def test_allowed_to_accept_more() -> None:
    ob = OverbookingModel(enabled=True, limit_pct=0.0)
    lim = ob.booking_limit(100)
    assert ob.allowed_to_accept_more(99, lim) is True
    assert ob.allowed_to_accept_more(100, lim) is False


def test_denied_boardings_and_cap() -> None:
    assert DeniedBoardingCostModel.compute_denied_boardings(190, 180) == 10
    assert DeniedBoardingCostModel.compute_denied_boardings(175, 180) == 0

    m = DeniedBoardingCostModel(
        delay_hours=2.5,
        compensation_multiplier=4.0,
        compensation_cap=500.0,
        goodwill_penalty_per_bumped_passenger=50.0,
    )
    per = m.penalty_per_bumped_passenger(200.0)
    assert per == min(4.0 * 200.0, 500.0) + 50.0
    assert m.compute_denied_boarding_cost(2, 200.0) == 2 * per
