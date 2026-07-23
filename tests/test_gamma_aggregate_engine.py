from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from backend.adapters.greeks.gamma_aggregate import FakeGammaAggregateCalculator
from backend.adapters.greeks.gamma_exposure import FakeGammaExposureCalculator
from backend.application.use_cases import CalculateGammaAggregateUseCase
from backend.domain.models import (
    ContractType,
    GammaAggregate,
    GammaAggregateItem,
    Greeks,
    OptionChain,
    OptionContract,
)
from backend.domain.ports import IGammaAggregateCalculator


def test_fake_gamma_aggregate_calculator_groups_gamma_exposure_by_strike() -> None:
    chain = _chain()
    exposures = FakeGammaExposureCalculator().calculate(chain)

    aggregate = FakeGammaAggregateCalculator().calculate(exposures, chain.symbol, chain.as_of)

    assert aggregate == GammaAggregate(
        symbol="SPY",
        as_of=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        items=(
            GammaAggregateItem(
                strike=Decimal("540"),
                total_gamma_exposure=Decimal("390.000"),
                call_gamma_exposure=Decimal("240.000"),
                put_gamma_exposure=Decimal("-150.000"),
                net_gamma=Decimal("90.000"),
                contract_count=2,
                absolute_gamma=Decimal("90.000"),
            ),
            GammaAggregateItem(
                strike=Decimal("545"),
                total_gamma_exposure=Decimal("210.000"),
                call_gamma_exposure=Decimal("200.000"),
                put_gamma_exposure=Decimal("-10.000"),
                net_gamma=Decimal("190.000"),
                contract_count=2,
                absolute_gamma=Decimal("190.000"),
            ),
        ),
        total_market_gamma=Decimal("280.000"),
        positive_gamma=Decimal("280.000"),
        negative_gamma=Decimal("0"),
        total_gamma=Decimal("280.000"),
        net_gamma=Decimal("280.000"),
        dealer_gamma_notional=Decimal("280.000"),
        peak_gamma_strike=Decimal("545"),
        peak_gamma_value=Decimal("190.000"),
    )


def test_fake_gamma_aggregate_calculator_selects_peak_by_absolute_gamma() -> None:
    chain = _chain()
    exposures = FakeGammaExposureCalculator().calculate(chain)

    aggregate = FakeGammaAggregateCalculator().calculate(exposures, chain.symbol, chain.as_of)

    assert aggregate.items[0].absolute_gamma == Decimal("90.000")
    assert aggregate.items[1].absolute_gamma == Decimal("190.000")
    assert aggregate.peak_gamma_strike == Decimal("545")
    assert aggregate.peak_gamma_value == Decimal("190.000")


def test_calculate_gamma_aggregate_use_case_uses_gamma_exposure_output() -> None:
    class RecordingGammaAggregateCalculator:
        def __init__(self) -> None:
            self.received_symbol: str | None = None
            self.received_exposure_count = 0

        def calculate(self, exposures, symbol, as_of) -> GammaAggregate:  # noqa: ANN001
            self.received_symbol = symbol
            self.received_exposure_count = len(exposures)
            return GammaAggregate(symbol=symbol, as_of=as_of)

    calculator: IGammaAggregateCalculator = RecordingGammaAggregateCalculator()
    use_case = CalculateGammaAggregateUseCase(FakeGammaExposureCalculator(), calculator)
    chain = _chain()

    result = use_case.execute(chain)

    assert result.symbol == "SPY"
    assert calculator.received_symbol == "SPY"
    assert calculator.received_exposure_count == len(chain.contracts)


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
        "total_market_gamma": 280,
        "positive_gamma": 280,
        "negative_gamma": 0,
        "peak_gamma_strike": 545,
        "peak_gamma_value": 190,
        "items": [
            {
                "strike": 540,
                "total_gamma_exposure": 390,
                "call_gamma_exposure": 240,
                "put_gamma_exposure": -150,
                "net_gamma": 90,
                "contract_count": 2,
                "absolute_gamma": 90,
            },
            {
                "strike": 545,
                "total_gamma_exposure": 210,
                "call_gamma_exposure": 200,
                "put_gamma_exposure": -10,
                "net_gamma": 190,
                "contract_count": 2,
                "absolute_gamma": 190,
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
