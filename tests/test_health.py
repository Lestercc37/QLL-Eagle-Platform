from fastapi.testclient import TestClient

from backend.main import app


def test_health_endpoint_returns_service_status() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "QLL Eagle Platform",
        "version": "0.1.0",
    }


def test_openapi_schema_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "QLL Eagle Platform"


def test_database_health_endpoint_checks_connection() -> None:
    with TestClient(app) as client:
        response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_docs_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
