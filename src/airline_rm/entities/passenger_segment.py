"""Passenger segmentation for demand and pricing (skeleton)."""

from __future__ import annotations

from enum import Enum


class PassengerSegment(str, Enum):
    """High-level traveler purpose."""

    LEISURE = "leisure"
    BUSINESS = "business"
