from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_health_cors_headers(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:1420"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_delete_account_returns_empty_204(client: TestClient) -> None:
    created = client.post(
        "/api/accounts",
        json={"name": "Cuenta temporal", "type": "bank", "current_balance": "0"},
    )
    assert created.status_code == 201
    deleted = client.delete(f"/api/accounts/{created.json()['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
