from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from backend.domain.models import ContractType, Greeks, OptionChain
from backend.domain.ports import IGreeksCalculator


class FakeGreeksCalculator(IGreeksCalculator):
    """Deterministic Greeks calculator for architecture validation.

    This adapter intentionally avoids financial formulas and market inputs so it
    can be replaced by a real implementation without changing the use case.
    """

    _CALL_GREEKS = Greeks(
        delta=Decimal("0.45"),
        gamma=Decimal("0.030"),
        theta=Decimal("-0.015"),
        vega=Decimal("0.120"),
    )
    _PUT_GREEKS = Greeks(
        delta=Decimal("-0.55"),
        gamma=Decimal("0.030"),
        theta=Decimal("-0.016"),
        vega=Decimal("0.118"),
    )

    def calculate(self, chain: OptionChain) -> OptionChain:
        contracts = tuple(
            replace(contract, greeks=self._greeks_for(contract.contract_type))
            for contract in chain.contracts
        )
        return replace(chain, contracts=contracts)

    def _greeks_for(self, contract_type: ContractType) -> Greeks:
        if contract_type == ContractType.CALL:
            return self._CALL_GREEKS
        return self._PUT_GREEKS
