from __future__ import annotations

from datetime import datetime, timezone, date
from decimal import Decimal

from backend.adapters.greeks.dealer_positioning import FakeDealerPositioningCalculator
from backend.application.use_cases import CalculateDealerPositioningUseCase
from backend.domain.models import (
    CallWall,
    ContractType,
    DealerPositioning,
    DealerPositioningInput,
    GammaAggregate,
    GammaAggregateItem,
    GammaExposure,
    GammaFlip,
    MaxPain,
    PutWall,
)
from backend.domain.ports import IDealerPositioningCalculator

AS_OF = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)


def test_fake_dealer_positioning_calculator_classifies_long_gamma() -> None:
    result = FakeDealerPositioningCalculator().calculate(_input(net_gamma=Decimal("90")))

    assert result == DealerPositioning(
        symbol="SPY",
        as_of=AS_OF,
        dealer_state="Long Gamma",
        dealer_bias="Bullish",
        hedging_pressure=Decimal("0.9"),
        expected_volatility="Low",
        liquidity_regime="Deep",
        confidence_score=Decimal("0.82"),
    )


def test_fake_dealer_positioning_calculator_classifies_short_gamma() -> None:
    result = FakeDealerPositioningCalculator().calculate(_input(net_gamma=Decimal("-90")))

    assert result.dealer_state == "Short Gamma"
    assert result.dealer_bias == "Bearish"
    assert result.expected_volatility == "High"
    assert result.liquidity_regime == "Thin"


def test_calculate_dealer_positioning_use_case_delegates_to_port() -> None:
    class RecordingDealerPositioningCalculator:
        def __init__(self) -> None:
            self.received: DealerPositioningInput | None = None

        def calculate(self, positioning_input: DealerPositioningInput) -> DealerPositioning:
            self.received = positioning_input
            return DealerPositioning(
                symbol="SPY",
                as_of=AS_OF,
                dealer_state="Neutral",
                dealer_bias="Neutral",
                hedging_pressure=Decimal("0"),
                expected_volatility="Normal",
                liquidity_regime="Balanced",
                confidence_score=Decimal("0.5"),
            )

    calculator: IDealerPositioningCalculator = RecordingDealerPositioningCalculator()
    positioning_input = _input(net_gamma=Decimal("0"))
    result = CalculateDealerPositioningUseCase(calculator).execute(positioning_input)

    assert calculator.received is positioning_input
    assert result.dealer_state == "Neutral"


def test_dealer_positioning_endpoint_returns_response_model() -> None:
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        response = client.post("/options/dealer-positioning", json=_payload())

    assert response.status_code == 200
    assert response.json() == {
        "schema_version": 1,
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "dealer_state": "Long Gamma",
        "dealer_bias": "Bullish",
        "hedging_pressure": 0.9,
        "expected_volatility": "Low",
        "liquidity_regime": "Deep",
        "confidence_score": 0.82,
    }


def _input(net_gamma: Decimal) -> DealerPositioningInput:
    return DealerPositioningInput(
        gamma_exposure=(
            GammaExposure("SPY260220C00540000", Decimal("540"), ContractType.CALL, date(2026, 2, 20), Decimal("0.03"), 8000, net_gamma, Decimal("1") if net_gamma >= 0 else Decimal("-1")),
        ),
        gamma_aggregate=GammaAggregate(
            symbol="SPY",
            as_of=AS_OF,
            items=(GammaAggregateItem(Decimal("540"), Decimal("100"), Decimal("100"), Decimal("0"), net_gamma, 1, Decimal("100")),),
            total_market_gamma=net_gamma,
            positive_gamma=max(net_gamma, Decimal("0")),
            negative_gamma=min(net_gamma, Decimal("0")),
            net_gamma=net_gamma,
        ),
        gamma_flip=GammaFlip(Decimal("535"), Decimal("530"), Decimal("540"), Decimal("-10"), Decimal("90"), Decimal("0.1"), True),
        call_wall=CallWall(Decimal("545"), Decimal("200"), 6000, 4200, Decimal("0.8")),
        put_wall=PutWall(Decimal("530"), Decimal("-100"), 5000, 3600, Decimal("0.4")),
        max_pain=MaxPain("SPY", AS_OF, Decimal("540"), Decimal("1000"), Decimal("900"), Decimal("1900")),
    )


def _payload() -> dict:
    return {
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "gamma_exposure": [
            {
                "occ_symbol": "SPY260220C00540000",
                "strike": 540,
                "contract_type": "call",
                "expiration": "2026-02-20",
                "gamma": 0.03,
                "open_interest": 8000,
                "dealer_gamma_exposure": 90,
                "sign": 1,
            }
        ],
        "gamma_aggregate": {
            "symbol": "SPY",
            "as_of": "2026-01-15T14:30:00Z",
            "items": [
                {
                    "strike": 540,
                    "total_gamma_exposure": 100,
                    "call_gamma_exposure": 100,
                    "put_gamma_exposure": 0,
                    "net_gamma": 90,
                    "contract_count": 1,
                    "absolute_gamma": 100,
                }
            ],
        },
        "gamma_flip": {
            "gamma_flip_price": 535,
            "lower_strike": 530,
            "upper_strike": 540,
            "lower_gamma": -10,
            "upper_gamma": 90,
            "interpolation_ratio": 0.1,
            "flip_found": True,
        },
        "call_wall": {"strike": 545, "gamma": 200, "open_interest": 6000, "volume": 4200, "confidence_score": 0.8},
        "put_wall": {"strike": 530, "gamma": -100, "open_interest": 5000, "volume": 3600, "confidence_score": 0.4},
        "max_pain": {"schema_version": 1, "symbol": "SPY", "as_of": "2026-01-15T14:30:00Z", "max_pain_strike": 540, "total_call_pain": 1000, "total_put_pain": 900, "total_pain": 1900, "ranking": []},
    }
