from __future__ import annotations

from backend.domain.models import DealerPositioning, DealerPositioningInput
from backend.domain.ports import IDealerPositioningCalculator


class CalculateDealerPositioningUseCase:
    """Calculate institutional Dealer Positioning from options engines output."""

    def __init__(self, dealer_positioning_calculator: IDealerPositioningCalculator) -> None:
        self._dealer_positioning_calculator = dealer_positioning_calculator

    def execute(self, positioning_input: DealerPositioningInput) -> DealerPositioning:
        return self._dealer_positioning_calculator.calculate(positioning_input)
