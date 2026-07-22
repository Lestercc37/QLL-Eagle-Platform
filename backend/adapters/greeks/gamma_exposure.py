from __future__ import annotations

from decimal import Decimal

from backend.domain.models import ContractType, GammaExposure, OptionChain, OptionContract
from backend.domain.ports import IGammaExposureCalculator


class FakeGammaExposureCalculator(IGammaExposureCalculator):
    """Deterministic per-contract Gamma Exposure calculator.

    The fake implementation intentionally uses only values already present on
    each option contract. It assigns a positive sign to calls, a negative sign
    to puts, and computes dealer_gamma_exposure as gamma * open_interest * sign.
    """

    def calculate(self, chain: OptionChain) -> tuple[GammaExposure, ...]:
        return tuple(self._calculate_contract_exposure(contract) for contract in chain.contracts)

    def _calculate_contract_exposure(self, contract: OptionContract) -> GammaExposure:
        sign = Decimal("1") if contract.contract_type == ContractType.CALL else Decimal("-1")
        dealer_gamma_exposure = contract.greeks.gamma * Decimal(contract.open_interest) * sign
        return GammaExposure(
            occ_symbol=contract.occ_symbol,
            strike=contract.strike,
            contract_type=contract.contract_type,
            expiration=contract.expiration,
            gamma=contract.greeks.gamma,
            open_interest=contract.open_interest,
            dealer_gamma_exposure=dealer_gamma_exposure,
            sign=sign,
        )
