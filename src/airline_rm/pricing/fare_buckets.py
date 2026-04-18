"""Discrete fare ladder with index-safe moves."""

from __future__ import annotations

from collections.abc import Sequence


class FareBucketSystem:
    """Sorted fare ladder: **index 0 = cheapest**, ``max_bucket()`` = most expensive.

    Input values may be supplied in any order; they are sorted ascending internally.
    """

    __slots__ = ("_fares",)

    def __init__(self, fares: Sequence[float]) -> None:
        if not fares:
            raise ValueError("At least one fare bucket is required")
        sorted_fares = tuple(sorted(float(x) for x in fares))
        if any(f <= 0 for f in sorted_fares):
            raise ValueError("All fares must be positive")
        self._fares = sorted_fares

    @classmethod
    def from_values(cls, values: tuple[float, ...]) -> FareBucketSystem:
        """Build from configured bucket values (e.g. YAML ``fare_buckets`` / ``fare_bucket_values``)."""

        return cls(values)

    @property
    def fares(self) -> tuple[float, ...]:
        return self._fares

    def min_bucket(self) -> int:
        return 0

    def max_bucket(self) -> int:
        return len(self._fares) - 1

    def clamp_bucket_index(self, bucket_index: int) -> int:
        return int(max(self.min_bucket(), min(bucket_index, self.max_bucket())))

    def current_fare(self, bucket_index: int) -> float:
        """Fare for ``bucket_index`` after clamping to the valid ladder range."""

        return float(self._fares[self.clamp_bucket_index(bucket_index)])

    def raise_bucket(self, bucket_index: int, steps: int = 1) -> int:
        """Move toward more expensive buckets by ``steps`` (clamped)."""

        if steps < 0:
            raise ValueError("steps must be non-negative")
        return self.clamp_bucket_index(bucket_index + steps)

    def lower_bucket(self, bucket_index: int, steps: int = 1) -> int:
        """Move toward cheaper buckets by ``steps`` (clamped)."""

        if steps < 0:
            raise ValueError("steps must be non-negative")
        return self.clamp_bucket_index(bucket_index - steps)

    def bucket_for_load_and_time(
        self,
        days_until_departure: int,
        seats_remaining: int,
        capacity: int,
        *,
        early_window_days: int,
        late_window_days: int,
        low_load_factor_threshold: float,
        high_load_factor_threshold: float,
    ) -> int:
        """Heuristic default bucket: cheap when far & loose, expensive when close or tight."""

        if capacity <= 0:
            raise ValueError("capacity must be positive")
        lf = seats_remaining / float(capacity)
        mid = (self.min_bucket() + self.max_bucket()) // 2

        if days_until_departure >= early_window_days and lf >= low_load_factor_threshold:
            return self.min_bucket()
        if days_until_departure <= late_window_days or lf <= high_load_factor_threshold:
            return self.max_bucket()
        return mid
