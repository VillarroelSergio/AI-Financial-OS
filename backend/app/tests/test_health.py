from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_health_cors_headers(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:1420"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
