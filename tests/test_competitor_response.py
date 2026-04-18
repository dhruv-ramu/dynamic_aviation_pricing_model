"""Tests for competitor fare generation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from airline_rm.config import load_simulation_config
from airline_rm.pricing.competitor_response import CompetitorPricingModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_none_mode_returns_none() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="none",
    )
    m = CompetitorPricingModel(cfg)
    rng = np.random.default_rng(0)
    assert m.competitor_fare(10, 200.0, rng) is None


def test_static_mode_reproducible_with_fixed_seed() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="static",
        competitor_noise_std=0.0,
    )
    m = CompetitorPricingModel(cfg)
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    a = m.competitor_fare(15, None, rng1)
    b = m.competitor_fare(15, None, rng2)
    assert a is not None and b is not None
    assert a == b


def test_reactive_uses_our_fare() -> None:
    cfg = replace(
        load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"),
        competitor_mode="reactive",
        competitor_noise_std=0.0,
    )
    m = CompetitorPricingModel(cfg)
    rng = np.random.default_rng(0)
    without = m.competitor_fare(10, None, rng)
    rng = np.random.default_rng(0)
    with_fare = m.competitor_fare(10, 400.0, rng)
    assert without is not None and with_fare is not None
    assert with_fare != without


def test_invalid_mode_on_call() -> None:
    cfg = replace(load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml"), competitor_mode="mirror")
    m = CompetitorPricingModel(cfg)
    with pytest.raises(ValueError, match="Unsupported competitor_mode"):
        m.competitor_fare(5, None, np.random.default_rng(0))
