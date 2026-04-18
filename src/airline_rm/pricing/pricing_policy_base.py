"""Abstract pricing policy interface and lightweight decision envelope."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from airline_rm.entities.simulation_state import SimulationState


@dataclass(frozen=True, slots=True)
class PricingAction:
    """Single-day pricing decision (bucket index + realized fare)."""

    bucket_index: int
    fare: float
    note: str = ""


class PricingPolicy(ABC):
    """Policies map calendar and inventory state to a :class:`PricingAction`."""

    @abstractmethod
    def decide(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None,
    ) -> PricingAction:
        """Choose bucket index and fare for the current sales day."""

    def quote_fare(
        self,
        days_until_departure: int,
        state: SimulationState,
        *,
        competitor_fare: float | None = None,
    ) -> float:
        """Convenience: quoted fare only (backward compatible with demand hooks)."""

        return self.decide(days_until_departure, state, competitor_fare=competitor_fare).fare
