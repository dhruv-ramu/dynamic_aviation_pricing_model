"""Route-level geography and distance metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Route:
    """A directional origin–destination pair with stage length."""

    origin: str
    destination: str
    distance_miles: float

    def __post_init__(self) -> None:
        if self.distance_miles <= 0:
            raise ValueError("distance_miles must be positive")
        if not self.origin or not self.destination:
            raise ValueError("origin and destination must be non-empty codes")
