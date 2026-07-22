from fastapi.testclient import TestClient

from backend.main import app


def test_options_endpoint_returns_option_chain() -> None:
    with TestClient(app) as client:
        response = client.get("/options/spy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["symbol"] == "SPY"
    assert payload["as_of"] == "2026-01-15T14:30:00Z"
    assert len(payload["contracts"]) == 6
    assert payload["contracts"][0] == {
        "occ_symbol": "SPY260220C00540000",
        "strike": 540,
        "type": "call",
        "bid": 1.2,
        "ask": 1.25,
        "iv": 0.18,
        "delta": 0.42,
        "gamma": 0.03,
        "open_interest": 8000,
        "volume": 3400,
    }


def test_options_endpoint_accepts_expiration_query() -> None:
    with TestClient(app) as client:
        response = client.get("/options/qqq?expiration=2026-03-20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "QQQ"
    assert {contract["occ_symbol"][3:9] for contract in payload["contracts"]} == {"260320"}
