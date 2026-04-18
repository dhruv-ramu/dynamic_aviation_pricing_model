"""Pricing policies, fare buckets, and competitor signals."""

from __future__ import annotations

from airline_rm.pricing.competitor_response import CompetitorPricingModel
from airline_rm.pricing.dynamic_policy import DynamicPricingPolicy
from airline_rm.pricing.fare_buckets import FareBucketSystem
from airline_rm.pricing.pricing_policy_base import PricingAction, PricingPolicy
from airline_rm.pricing.rule_based_policy import RuleBasedPricingPolicy
from airline_rm.pricing.static_policy import StaticPricingPolicy
from airline_rm.types import SimulationConfig


def build_pricing_policy(config: SimulationConfig) -> PricingPolicy:
    """Instantiate the configured ``pricing_policy`` implementation."""

    name = str(config.pricing_policy).strip().lower()
    if name == "static":
        return StaticPricingPolicy(config)
    if name == "rule_based":
        return RuleBasedPricingPolicy(config)
    if name == "dynamic":
        return DynamicPricingPolicy(config)
    raise ValueError(f"Unknown pricing_policy: {config.pricing_policy!r}")


__all__ = [
    "build_pricing_policy",
    "CompetitorPricingModel",
    "DynamicPricingPolicy",
    "FareBucketSystem",
    "PricingAction",
    "PricingPolicy",
    "RuleBasedPricingPolicy",
    "StaticPricingPolicy",
]
