"""Purchase conversion from fare quotes vs willingness to pay."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BookingConverter:
    """Deterministic threshold purchase rule (extensible to logit later)."""

    def will_book(self, offered_fare: float, wtp: float) -> bool:
        """Return True iff the traveler purchases at ``offered_fare``."""

        if offered_fare < 0:
            raise ValueError("offered_fare must be non-negative")
        if wtp < 0:
            raise ValueError("wtp must be non-negative")
        return wtp >= offered_fare
