"""Alta de activos con autorresolución y refresco de precios sin veto manual."""
from decimal import Decimal
from unittest.mock import patch


def _create_broker_account(client) -> str:
    return client.post("/api/accounts", json={"name": "Trade Republic", "type": "broker"}).json()["id"]


def test_search_endpoint_hits_known_registry(client):
    with patch("yfinance.Search", side_effect=Exception("offline")):
        r = client.get("/api/investments/assets/search?q=iberdrola")
    assert r.status_code == 200
    results = r.json()
    assert results and results[0]["ticker"] == "IBE.MC"
    assert results[0]["currency"] == "EUR"


def test_create_asset_autoresolves_bare_ticker(client):
    r = client.post("/api/investments/assets", json={
        "name": "Iberdrola", "ticker": "IBE", "asset_type": "stock",
    })
    assert r.status_code == 201
    asset = r.json()
    assert asset["ticker"] == "IBE.MC"
    assert asset["currency"] == "EUR"
    assert asset["price_source"] == "yfinance"


def test_refresh_fetches_price_for_manual_assets_with_ticker(client):
    account_id = _create_broker_account(client)
    with patch("app.modules.investments.asset_resolution.resolve_asset") as resolver:
        resolver.return_value.selected = None
        response = client.post("/api/investments/assets", json={
            "name": "Fondo Manual XYZ", "ticker": "XYZ.MC", "asset_type": "fund",
        })
    assert response.status_code == 201
    asset = response.json()
    assert asset["price_source"] == "manual"  # no está en el registro
    client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset["id"],
        "quantity": "10", "average_price": "5",
    })

    with patch(
        "app.modules.investments.price_service.PriceService.fetch_ticker_price",
        return_value=Decimal("6.50"),
    ):
        r = client.post("/api/investments/prices/refresh")

    assert r.status_code == 200
    body = r.json()
    assert body["updated"] == 1
    holdings = client.get("/api/investments/holdings").json()
    assert holdings[0]["current_price"] == "6.5000"
    assert holdings[0]["market_value"] == "65.00"
