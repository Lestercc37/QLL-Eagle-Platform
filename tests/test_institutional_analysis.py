from fastapi.testclient import TestClient

from backend.adapters.providers.fake import FakeMarketDataProvider
from backend.application.use_cases import CalculateInstitutionalAnalysisUseCase
from backend.core.container import build_container
from backend.main import app


def _payload() -> dict:
    provider = FakeMarketDataProvider()
    chain = provider.get_option_chain("SPY")
    return {
        "symbol": chain.symbol,
        "as_of": chain.as_of.isoformat().replace("+00:00", "Z"),
        "contracts": [
            {
                "occ_symbol": c.occ_symbol,
                "underlying": c.underlying,
                "strike": float(c.strike),
                "expiration": c.expiration.isoformat(),
                "type": c.contract_type.value,
                "bid": float(c.bid),
                "ask": float(c.ask),
                "last": float(c.last),
                "iv": float(c.iv),
                "delta": float(c.greeks.delta),
                "gamma": float(c.greeks.gamma),
                "theta": float(c.greeks.theta) if c.greeks.theta is not None else None,
                "vega": float(c.greeks.vega) if c.greeks.vega is not None else None,
                "open_interest": c.open_interest,
                "volume": c.volume,
            }
            for c in chain.contracts
        ],
    }


def test_calculate_institutional_analysis_use_case_composes_all_engines() -> None:
    container = build_container()
    chain = FakeMarketDataProvider().get_option_chain("SPY")
    use_case = CalculateInstitutionalAnalysisUseCase(
        container.get_market_snapshot_use_case,
        container.calculate_greeks_use_case,
        container.calculate_gamma_exposure_use_case,
        container.calculate_gamma_aggregate_use_case,
        container.calculate_gamma_flip_use_case,
        container.calculate_walls_use_case,
        container.calculate_max_pain_use_case,
        container.calculate_dealer_positioning_use_case,
    )

    analysis = use_case.execute(chain)

    assert analysis.schema_version == 1
    assert analysis.market_snapshot.symbol == "SPY"
    assert analysis.option_chain.symbol == "SPY"
    assert len(analysis.gamma_exposure) == len(chain.contracts)
    assert analysis.gamma_aggregate.items
    assert analysis.gamma_aggregate.peak_gamma_strike > 0
    assert analysis.max_pain.max_pain_strike > 0
    assert analysis.dealer_positioning.symbol == "SPY"
    assert analysis.overall_bias in {"Bullish", "Bearish", "Neutral"}
    assert 0 <= analysis.confidence_score <= 1
    assert analysis.market_regime in {"High Volatility", "Low Volatility", "Normal"}


def test_institutional_analysis_endpoint_returns_complete_analysis() -> None:
    with TestClient(app) as client:
        response = client.post("/options/institutional-analysis", json=_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["market_snapshot"]["symbol"] == "SPY"
    assert payload["option_chain"]["symbol"] == "SPY"
    assert len(payload["gamma_exposure"]["items"]) == 6
    assert payload["gamma_aggregate"]["items"]
    assert payload["peak_gamma_strike"] == payload["gamma_aggregate"]["peak_gamma_strike"]
    assert payload["gamma_flip"]["flip_found"] in {True, False}
    assert payload["max_pain"]["max_pain_strike"] > 0
    assert payload["dealer_positioning"]["symbol"] == "SPY"
    assert payload["overall_bias"] == payload["dealer_positioning"]["dealer_bias"]
    assert 0 <= payload["confidence_score"] <= 1
    assert payload["timestamp"].endswith("Z")


def test_openapi_documents_institutional_analysis_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi = response.json()
    operation = openapi["paths"]["/options/institutional-analysis"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/OptionChainRequest"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/InstitutionalAnalysisResponse")
    schema = openapi["components"]["schemas"]["InstitutionalAnalysisResponse"]
    assert schema["properties"]["dealer_positioning"]["$ref"].endswith(
        "/DealerPositioningResponse"
    )
