from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from backend.adapters.greeks.gamma_exposure import FakeGammaExposureCalculator
from backend.domain.models import GammaAggregate, GammaAggregateStrike, OptionChain
from backend.domain.ports import IGammaAggregateCalculator, IGammaExposureCalculator


class FakeGammaAggregateCalculator(IGammaAggregateCalculator):
    """Deterministic Gamma Aggregate calculator based on Gamma Exposure."""

    def __init__(
        self,
        gamma_exposure_calculator: IGammaExposureCalculator | None = None,
    ) -> None:
        self._gamma_exposure_calculator = (
            gamma_exposure_calculator or FakeGammaExposureCalculator()
        )

    def calculate(self, chain: OptionChain) -> GammaAggregate:
        exposures = self._gamma_exposure_calculator.calculate(chain)
        grouped_gamma: dict[Decimal, Decimal] = defaultdict(lambda: Decimal("0"))
        grouped_contract_count: dict[Decimal, int] = defaultdict(int)

        for exposure in exposures:
            grouped_gamma[exposure.strike] += exposure.dealer_gamma_exposure
            grouped_contract_count[exposure.strike] += 1

        cumulative_gamma = Decimal("0")
        strikes: list[GammaAggregateStrike] = []
        for strike in sorted(grouped_gamma):
            gamma = grouped_gamma[strike]
            cumulative_gamma += gamma
            strikes.append(
                GammaAggregateStrike(
                    strike=strike,
                    gamma=gamma,
                    cumulative_gamma=cumulative_gamma,
                    contract_count=grouped_contract_count[strike],
                )
            )

        return GammaAggregate(
            symbol=chain.symbol,
            as_of=chain.as_of,
            total_gamma=sum(grouped_gamma.values(), Decimal("0")),
            strikes=tuple(strikes),
            net_gamma=sum(grouped_gamma.values(), Decimal("0")),
            dealer_gamma_notional=sum(grouped_gamma.values(), Decimal("0")),
        )
