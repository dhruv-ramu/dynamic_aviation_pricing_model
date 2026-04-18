"""Denied boarding counts and simplified compensation cost."""

from __future__ import annotations

from airline_rm.types import SimulationConfig


class DeniedBoardingCostModel:
    """DOT-inspired simplified cash compensation plus fixed goodwill per bumped passenger."""

    __slots__ = (
        "_delay_hours",
        "_comp_multiplier",
        "_comp_cap",
        "_goodwill",
    )

    def __init__(
        self,
        *,
        delay_hours: float,
        compensation_multiplier: float,
        compensation_cap: float,
        goodwill_penalty_per_bumped_passenger: float,
    ) -> None:
        self._delay_hours = float(delay_hours)
        self._comp_multiplier = float(compensation_multiplier)
        self._comp_cap = float(compensation_cap)
        self._goodwill = float(goodwill_penalty_per_bumped_passenger)

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> DeniedBoardingCostModel:
        return cls(
            delay_hours=float(config.denied_boarding_delay_hours),
            compensation_multiplier=float(config.denied_boarding_compensation_multiplier),
            compensation_cap=float(config.denied_boarding_compensation_cap),
            goodwill_penalty_per_bumped_passenger=float(config.goodwill_penalty_per_bumped_passenger),
        )

    @staticmethod
    def compute_denied_boardings(show_ups: int, physical_capacity: int) -> int:
        """Passengers who showed but cannot be seated on the aircraft."""

        if show_ups < 0 or physical_capacity < 0:
            raise ValueError("show_ups and physical_capacity must be non-negative")
        return int(max(0, show_ups - physical_capacity))

    def penalty_per_bumped_passenger(self, reference_fare: float) -> float:
        """Cash + goodwill for one denied boarding (``reference_fare`` is avg one-way ticket)."""

        if reference_fare < 0:
            raise ValueError("reference_fare must be non-negative")
        cash = min(self._comp_multiplier * reference_fare, self._comp_cap)
        return float(cash + self._goodwill)

    def compute_denied_boarding_cost(self, denied_boardings: int, reference_fare: float) -> float:
        """Total denied-boarding liability."""

        if denied_boardings < 0:
            raise ValueError("denied_boardings must be non-negative")
        if denied_boardings == 0:
            return 0.0
        return float(denied_boardings) * self.penalty_per_bumped_passenger(reference_fare)

    @property
    def delay_hours(self) -> float:
        """Documented delay severity (reserved for future schedule detail)."""

        return self._delay_hours
