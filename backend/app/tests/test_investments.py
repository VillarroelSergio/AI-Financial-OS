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


def test_price_refresh_updates_holdings(client, monkeypatch):
    import app.modules.investments.price_service as ps

    prices = {"AAPL": 192.5, "EURUSD=X": 1.08}

    class MockFastInfo:
        def __init__(self, ticker):
            self.last_price = prices.get(ticker)

    class MockTicker:
        def __init__(self, ticker):
            self.fast_info = MockFastInfo(ticker)

    monkeypatch.setattr(ps.yf, "Ticker", MockTicker)

    account = client.post("/api/accounts", json={
        "name": "TR", "type": "broker", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Apple", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "10", "average_price": "140.00",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1
    assert data["failed"] == []

    holdings = client.get("/api/investments/holdings").json()
    h = next(x for x in holdings if x["id"] == holding["id"])
    assert float(h["current_price"]) == 192.5
    expected_mv = round(10 * 192.5 / 1.08, 2)
    assert abs(float(h["market_value"]) - expected_mv) < 0.05


def test_price_refresh_marks_manual_assets(client, monkeypatch):
    import app.modules.investments.price_service as ps

    class MockFastInfo:
        last_price = 576.19

    class MockTicker:
        def __init__(self, ticker):
            self.fast_info = MockFastInfo()

    monkeypatch.setattr(ps.yf, "Ticker", MockTicker)

    account = client.post("/api/accounts", json={
        "name": "Finizens", "type": "investment", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Vanguard US 500", "asset_type": "fund",
        "currency": "EUR", "price_source": "manual",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "4.59", "average_price": "420.00",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert holding["id"] in data["needs_manual_nav"]
    assert data["manual_required"][0]["holding_id"] == holding["id"]
    assert data["manual_required"][0]["reason"] == "missing_price_provider"


def test_refresh_prices_skips_savings_accounts(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "5000", "average_price": "1", "market_value": "5000",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert holding["id"] not in data["needs_manual_nav"]
    assert data["manual_required"] == []
    assert data["skipped"][0]["holding_id"] == holding["id"]
    assert data["skipped"][0]["reason"] == "cash_uses_account_balance"


def test_refresh_prices_does_not_request_nav_for_cash(client):
    account = client.post("/api/accounts", json={
        "name": "Efectivo", "type": "cash", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Efectivo cartera", "asset_type": "cash",
        "currency": "EUR", "price_source": "manual",
    }).json()
    client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "1000", "average_price": "1", "market_value": "1000",
    })

    data = client.post("/api/investments/prices/refresh").json()
    assert data["needs_manual_nav"] == []
    assert data["manual_required"] == []
    assert len(data["skipped"]) == 1


def test_no_duplicate_cash_holdings_in_refresh_modal(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    for _ in range(2):
        client.post("/api/investments/holdings", json={
            "account_id": account["id"], "asset_id": asset["id"],
            "quantity": "1000", "average_price": "1", "market_value": "1000",
        })

    data = client.post("/api/investments/prices/refresh").json()
    assert data["manual_required"] == []
    assert data["needs_manual_nav"] == []
