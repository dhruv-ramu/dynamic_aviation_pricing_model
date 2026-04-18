"""Abstract pricing policy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from airline_rm.entities.simulation_state import SimulationState


class PricingPolicy(ABC):
    """Policy objects map calendar state to a quoted fare."""

    @abstractmethod
    def quote_fare(self, days_until_departure: int, state: SimulationState) -> float:
        """Return the fare offered to arriving shoppers for the current day."""
