from fastapi.testclient import TestClient


def test_market_snapshot_bootstraps_when_ingestion_empty(client: TestClient) -> None:
    response = client.get("/api/market-intelligence/snapshot/market")

    assert response.status_code == 200
    data = response.json()
    assert data["indices"]
    assert data["crypto"]
    assert data["commodities"]
    assert any("quality" in warning for warning in data["warnings"])


def test_macro_snapshot_bootstraps_when_ingestion_empty(client: TestClient) -> None:
    response = client.get("/api/market-intelligence/snapshot/macro")

    assert response.status_code == 200
    data = response.json()
    assert data["spain"]
    assert data["eurozone"]
    assert any("quality" in warning for warning in data["warnings"])


def test_forex_snapshot_bootstraps_when_ingestion_empty(client: TestClient) -> None:
    response = client.get("/api/market-intelligence/snapshot/forex")

    assert response.status_code == 200
    data = response.json()
    assert data["rates"]
    assert any(rate["base_currency"] == "EUR" and rate["quote_currency"] == "USD" for rate in data["rates"])
    assert any("quality" in warning for warning in data["warnings"])


def test_bond_snapshot_bootstraps_when_ingestion_empty(client: TestClient) -> None:
    response = client.get("/api/market-intelligence/snapshot/bonds")

    assert response.status_code == 200
    data = response.json()
    assert data["yields"]
    assert {"2Y", "10Y", "30Y"}.issubset({item["maturity"] for item in data["yields"]})
    assert any("quality" in warning for warning in data["warnings"])
