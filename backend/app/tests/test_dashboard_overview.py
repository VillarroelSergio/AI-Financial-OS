from datetime import datetime, timezone
from decimal import Decimal


def test_spending_monthly_series(client):
    acc = client.post("/api/accounts", json={"name": "BBVA", "type": "bank"}).json()
    current = datetime.now(timezone.utc).strftime("%Y-%m")
    client.post("/api/transactions", json={
        "account_id": acc["id"], "date": f"{current}-05",
        "description": "Nomina", "amount": "2000.00", "type": "income",
    })
    client.post("/api/transactions", json={
        "account_id": acc["id"], "date": f"{current}-10",
        "description": "Compra", "amount": "-500.00", "type": "expense",
    })
    series = client.get("/api/dashboard/spending/monthly?months=3").json()
    assert len(series) == 3
    last = series[-1]
    assert last["month"] == current
    assert Decimal(last["income"]) == Decimal("2000.00")
    assert Decimal(last["expense"]) == Decimal("500.00")
    assert Decimal(last["savings"]) == Decimal("1500.00")


def test_overview_converts_fx_and_includes_portfolio(client, monkeypatch):
    monkeypatch.setattr(
        "app.modules.investments.price_coverage_audit.fetch_fx_rate",
        lambda currency: (2.0, "EURUSD=X", None),
    )
    client.post("/api/accounts", json={"name": "BBVA", "type": "bank", "current_balance": "4000"})
    client.post(
        "/api/accounts",
        json={"name": "TR Ahorro", "type": "savings", "currency": "USD", "current_balance": "8000"},
    )
    broker = client.post(
        "/api/accounts", json={"name": "Trade Republic", "type": "broker"}
    ).json()

    from app.core import database as db_module
    from app.models.investment import Holding, InvestmentAsset

    session = db_module.SessionLocal()
    asset = InvestmentAsset(name="S&P 500 ETF", asset_type="etf")
    session.add(asset)
    session.flush()
    session.add(
        Holding(
            account_id=broker["id"],
            asset_id=asset.id,
            quantity=Decimal("10"),
            average_price=Decimal("100"),
            market_value=Decimal("1500.00"),
        )
    )
    session.commit()
    session.close()

    overview = client.get("/api/dashboard/overview").json()
    # 8000 USD a rate 2.0 → 4000 EUR
    assert overview["liquidity"] == "8000.00"
    assert overview["investments"] == "1500.00"
    assert overview["net_worth"] == "9500.00"
