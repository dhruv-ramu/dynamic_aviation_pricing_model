"""Centralized RNG construction for reproducible simulations."""

from __future__ import annotations

import numpy as np

from airline_rm.types import SimulationConfig


def make_generator(config: SimulationConfig) -> np.random.Generator:
    """Create a NumPy ``Generator`` seeded from configuration."""

    return np.random.default_rng(int(config.rng_seed))
