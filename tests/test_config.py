"""Tests for YAML configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from airline_rm.config import load_raw_config, load_simulation_config
from airline_rm.types import SimulationConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_load_base_config_with_extends() -> None:
    cfg = load_simulation_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    assert isinstance(cfg, SimulationConfig)
    assert cfg.booking_horizon_days == 60
    assert cfg.capacity == 180
    assert cfg.fare_buckets[0] == 220.0
    assert cfg.route_origin == "SEA"
    assert cfg.expected_total_demand == 210.0
    assert cfg.booking_curve_type == "logistic"
    assert cfg.leisure_wtp_mean == 208.0
    assert cfg.late_business_share == 0.42


def test_missing_required_key_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("booking_horizon_days: 1\n", encoding="utf-8")
    with pytest.raises(KeyError):
        load_simulation_config(bad)


def test_extends_merge_order() -> None:
    raw = load_raw_config(PROJECT_ROOT / "configs" / "base_config.yaml")
    assert raw["rng_seed"] == 42
