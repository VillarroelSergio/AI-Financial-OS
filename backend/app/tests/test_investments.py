from sqlalchemy import inspect


def test_investment_tables_are_created(client):
    from app.core.database import engine
    tables = inspect(engine).get_table_names()
    assert "investment_assets" in tables
    assert "holdings" in tables
    assert "investment_operations" in tables


def test_assets_crud(client):
    r = client.post("/api/investments/assets", json={
        "name": "Apple Inc.", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    })
    assert r.status_code == 201
    asset = r.json()
    assert asset["name"] == "Apple Inc."
    asset_id = asset["id"]

    r = client.get("/api/investments/assets")
    assert r.status_code == 200
    assert any(a["id"] == asset_id for a in r.json())

    r = client.patch(f"/api/investments/assets/{asset_id}", json={"sector": "Technology"})
    assert r.status_code == 200
    assert r.json()["sector"] == "Technology"

    r = client.delete(f"/api/investments/assets/{asset_id}")
    assert r.status_code == 204

    r = client.get("/api/investments/assets")
    assert all(a["id"] != asset_id for a in r.json())


def test_asset_not_found_returns_404(client):
    r = client.patch("/api/investments/assets/nonexistent", json={"sector": "X"})
    assert r.status_code == 404


def _setup_account_and_asset(client):
    account = client.post("/api/accounts", json={
        "name": "Trade Republic", "type": "broker", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Telefónica", "ticker": "TEF.MC", "asset_type": "stock",
        "currency": "EUR", "price_source": "yfinance",
    }).json()
    return account["id"], asset["id"]


def test_holdings_crud_and_enrichment(client):
    account_id, asset_id = _setup_account_and_asset(client)

    r = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "100", "average_price": "3.95",
    })
    assert r.status_code == 201
    h = r.json()
    assert h["cost_basis"] == "395.0000"
    assert h["return_absolute"] is None
    assert h["asset"]["ticker"] == "TEF.MC"
    holding_id = h["id"]

    r = client.get("/api/investments/holdings")
    assert any(x["id"] == holding_id for x in r.json())

    r = client.patch(f"/api/investments/holdings/{holding_id}", json={"current_price": "4.21"})
    assert r.status_code == 200
    h = r.json()
    assert h["market_value"] == "421.00"
    assert h["return_absolute"] == "26.00"
    assert abs(h["return_percent"] - 6.58) < 0.1

    r = client.delete(f"/api/investments/holdings/{holding_id}")
    assert r.status_code == 204


def test_holdings_savings_account_accrued_interest(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    r = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "5000", "average_price": "1",
        "interest_rate": "0.04", "inception_date": "2025-01-01",
        "market_value": "5000",
    })
    assert r.status_code == 201
    h = r.json()
    assert h["accrued_interest"] is not None
    assert float(h["accrued_interest"]) > 0
