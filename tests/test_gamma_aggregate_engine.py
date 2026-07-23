from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from backend.adapters.greeks.gamma_aggregate import FakeGammaAggregateCalculator
from backend.application.use_cases import CalculateGammaAggregateUseCase
from backend.domain.models import (
    ContractType,
    GammaAggregate,
    GammaAggregateStrike,
    Greeks,
    OptionChain,
    OptionContract,
)
from backend.domain.ports import IGammaAggregateCalculator


def test_fake_gamma_aggregate_calculator_groups_gamma_exposure_by_strike() -> None:
    aggregate = FakeGammaAggregateCalculator().calculate(_chain())

    assert aggregate == GammaAggregate(
        symbol="SPY",
        as_of=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        total_gamma=Decimal("280.000"),
        strikes=(
            GammaAggregateStrike(
                strike=Decimal("540"),
                gamma=Decimal("90.000"),
                cumulative_gamma=Decimal("90.000"),
                contract_count=2,
            ),
            GammaAggregateStrike(
                strike=Decimal("545"),
                gamma=Decimal("190.000"),
                cumulative_gamma=Decimal("280.000"),
                contract_count=2,
            ),
        ),
        net_gamma=Decimal("280.000"),
        dealer_gamma_notional=Decimal("280.000"),
    )


def test_calculate_gamma_aggregate_use_case_depends_only_on_port() -> None:
    class RecordingGammaAggregateCalculator:
        def __init__(self) -> None:
            self.received: OptionChain | None = None

        def calculate(self, chain: OptionChain) -> GammaAggregate:
            self.received = chain
            return GammaAggregate(symbol=chain.symbol, as_of=chain.as_of)

    calculator: IGammaAggregateCalculator = RecordingGammaAggregateCalculator()
    use_case = CalculateGammaAggregateUseCase(calculator)
    chain = _chain()

    result = use_case.execute(chain)

    assert result.symbol == "SPY"
    assert calculator.received is chain


def test_gamma_aggregate_endpoint_returns_strike_aggregate() -> None:
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        response = client.post("/options/gamma-aggregate", json=_chain_payload())

    assert response.status_code == 200
    assert response.json() == {
        "schema_version": 1,
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "total_gamma": 280,
        "strikes": [
            {
                "strike": 540,
                "gamma": 90,
                "cumulative_gamma": 90,
                "contract_count": 2,
            },
            {
                "strike": 545,
                "gamma": 190,
                "cumulative_gamma": 280,
                "contract_count": 2,
            },
        ],
    }


def _chain() -> OptionChain:
    return OptionChain(
        symbol="SPY",
        as_of=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        contracts=(
            _contract(ContractType.CALL, "SPY260220C00540000", Decimal("540"), Decimal("0.030"), 8000),
            _contract(ContractType.PUT, "SPY260220P00540000", Decimal("540"), Decimal("0.025"), 6000),
            _contract(ContractType.CALL, "SPY260220C00545000", Decimal("545"), Decimal("0.040"), 5000),
            _contract(ContractType.PUT, "SPY260220P00545000", Decimal("545"), Decimal("0.010"), 1000),
        ),
    )


def _contract(contract_type: ContractType, occ_symbol: str, strike: Decimal, gamma: Decimal, open_interest: int) -> OptionContract:
    return OptionContract(
        underlying="SPY",
        strike=strike,
        expiration=date(2026, 2, 20),
        contract_type=contract_type,
        occ_symbol=occ_symbol,
        bid=Decimal("1.20"),
        ask=Decimal("1.25"),
        last=Decimal("1.22"),
        volume=3400,
        open_interest=open_interest,
        iv=Decimal("0.18"),
        greeks=Greeks(delta=Decimal("0"), gamma=gamma),
    )


def _chain_payload() -> dict[str, object]:
    return {
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "contracts": [
            {"occ_symbol": c.occ_symbol, "underlying": "SPY", "strike": float(c.strike), "expiration": "2026-02-20", "type": c.contract_type.value, "bid": 1.2, "ask": 1.25, "last": 1.22, "iv": 0.18, "delta": 0, "gamma": float(c.greeks.gamma), "open_interest": c.open_interest, "volume": 3400}
            for c in _chain().contracts
        ],
    }
