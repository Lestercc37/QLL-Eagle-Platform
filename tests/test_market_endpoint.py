from fastapi.testclient import TestClient

from backend.main import app


def test_market_endpoint_returns_market_snapshot() -> None:
    with TestClient(app) as client:
        response = client.get("/market/spy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["symbol"] == "SPY"
    assert payload["price"] == 552.25
    assert payload["volume"] == 1_250_000
    assert "as_of" in payload


def test_openapi_documents_market_response_model() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    response_schema = response.json()["paths"]["/market/{symbol}"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert response_schema["$ref"].endswith("/MarketSnapshotResponse")
    assert "additionalProp1" not in str(response_schema)
