from __future__ import annotations

from backend.domain.models import GammaAggregate, OptionChain
from backend.domain.ports import IGammaAggregateCalculator


class CalculateGammaAggregateUseCase:
    """Calculate strike-level Gamma Aggregate by delegating to the domain port."""

    def __init__(self, gamma_aggregate_calculator: IGammaAggregateCalculator) -> None:
        self._gamma_aggregate_calculator = gamma_aggregate_calculator

    def execute(self, chain: OptionChain) -> GammaAggregate:
        return self._gamma_aggregate_calculator.calculate(chain)
