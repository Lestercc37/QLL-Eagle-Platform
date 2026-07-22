from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import AsyncIterator

from backend.domain.models import ContractType, FlowEvent, Greeks, MarketSnapshot, OptionChain, OptionContract, utc_now


class MockDataProvider:
    def get_option_chain(self, underlying: str, expiration: date | None = None) -> OptionChain:
        symbol = underlying.upper()
        exp = expiration or (utc_now().date() + timedelta(days=30))
        contracts = []
        for strike in (Decimal("540"), Decimal("545"), Decimal("550"), Decimal("555"), Decimal("560")):
            contracts.append(_contract(symbol, strike, exp, ContractType.CALL))
            contracts.append(_contract(symbol, strike, exp, ContractType.PUT))
        return OptionChain(symbol=symbol, as_of=utc_now(), contracts=tuple(contracts))

    def get_underlying_snapshot(self, underlying: str) -> MarketSnapshot:
        return MarketSnapshot(symbol=underlying.upper(), as_of=utc_now(), price=Decimal("552.25"), volume=1_250_000)

    async def stream_trades(self, underlying: str) -> AsyncIterator[FlowEvent]:
        if False:
            yield


def _contract(symbol: str, strike: Decimal, expiration: date, contract_type: ContractType) -> OptionContract:
    suffix = "C" if contract_type == ContractType.CALL else "P"
    return OptionContract(
        underlying=symbol,
        strike=strike,
        expiration=expiration,
        contract_type=contract_type,
        occ_symbol=f"{symbol}{expiration:%y%m%d}{suffix}{int(strike * 1000):08d}",
        bid=Decimal("1.20"),
        ask=Decimal("1.25"),
        last=Decimal("1.22"),
        volume=3400,
        open_interest=12000 if strike == Decimal("555") and contract_type == ContractType.CALL else 8000,
        iv=Decimal("0.18"),
        greeks=Greeks(delta=Decimal("0.42") if contract_type == ContractType.CALL else Decimal("-0.40"), gamma=Decimal("0.03")),
    )
