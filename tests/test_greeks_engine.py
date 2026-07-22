from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.adapters.greeks.fake import FakeGreeksCalculator
from backend.application.use_cases import CalculateGreeksUseCase
from backend.domain.models import ContractType, Greeks, OptionChain, OptionContract
from backend.domain.ports import IGreeksCalculator
from backend.main import app


def test_fake_greeks_calculator_enriches_chain_deterministically() -> None:
    chain = _chain()

    enriched = FakeGreeksCalculator().calculate(chain)

    assert enriched is not chain
    assert len(enriched.contracts) == len(chain.contracts)
    assert enriched.contracts[0].greeks == Greeks(
        delta=Decimal("0.45"),
        gamma=Decimal("0.030"),
        theta=Decimal("-0.015"),
        vega=Decimal("0.120"),
    )
    assert enriched.contracts[1].greeks == Greeks(
        delta=Decimal("-0.55"),
        gamma=Decimal("0.030"),
        theta=Decimal("-0.016"),
        vega=Decimal("0.118"),
    )


def test_calculate_greeks_use_case_depends_only_on_port() -> None:
    class RecordingGreeksCalculator:
        def __init__(self) -> None:
            self.received: OptionChain | None = None

        def calculate(self, chain: OptionChain) -> OptionChain:
            self.received = chain
            return chain

    calculator: IGreeksCalculator = RecordingGreeksCalculator()
    use_case = CalculateGreeksUseCase(calculator)
    chain = _chain()

    result = use_case.execute(chain)

    assert result is chain
    assert calculator.received is chain


def test_greeks_endpoint_returns_enriched_chain() -> None:
    with TestClient(app) as client:
        response = client.post("/options/greeks", json=_chain_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "SPY"
    assert len(payload["contracts"]) == 2
    assert payload["contracts"][0]["delta"] == 0.45
    assert payload["contracts"][0]["gamma"] == 0.03
    assert payload["contracts"][0]["theta"] == -0.015
    assert payload["contracts"][0]["vega"] == 0.12
    assert payload["contracts"][1]["delta"] == -0.55
    assert payload["contracts"][1]["gamma"] == 0.03
    assert payload["contracts"][1]["theta"] == -0.016
    assert payload["contracts"][1]["vega"] == 0.118


def _chain() -> OptionChain:
    return OptionChain(
        symbol="SPY",
        as_of=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        contracts=(
            _contract(ContractType.CALL, "SPY260220C00540000"),
            _contract(ContractType.PUT, "SPY260220P00540000"),
        ),
    )


def _contract(contract_type: ContractType, occ_symbol: str) -> OptionContract:
    return OptionContract(
        underlying="SPY",
        strike=Decimal("540"),
        expiration=date(2026, 2, 20),
        contract_type=contract_type,
        occ_symbol=occ_symbol,
        bid=Decimal("1.20"),
        ask=Decimal("1.25"),
        last=Decimal("1.22"),
        volume=3400,
        open_interest=8000,
        iv=Decimal("0.18"),
        greeks=Greeks(delta=Decimal("0"), gamma=Decimal("0")),
    )


def _chain_payload() -> dict[str, object]:
    return {
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "contracts": [
            {
                "occ_symbol": "SPY260220C00540000",
                "underlying": "SPY",
                "strike": 540,
                "expiration": "2026-02-20",
                "type": "call",
                "bid": 1.2,
                "ask": 1.25,
                "last": 1.22,
                "iv": 0.18,
                "delta": 0,
                "gamma": 0,
                "open_interest": 8000,
                "volume": 3400,
            },
            {
                "occ_symbol": "SPY260220P00540000",
                "underlying": "SPY",
                "strike": 540,
                "expiration": "2026-02-20",
                "type": "put",
                "bid": 1.2,
                "ask": 1.25,
                "last": 1.22,
                "iv": 0.18,
                "delta": 0,
                "gamma": 0,
                "open_interest": 8000,
                "volume": 3400,
            },
        ],
    }
