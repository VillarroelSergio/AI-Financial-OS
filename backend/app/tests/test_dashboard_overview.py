import asyncio
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


def test_investment_account_derives_total_from_cash_and_positions_once(client):
    broker = client.post("/api/accounts", json={
        "name": "Trade Republic",
        "type": "broker",
        "currency": "EUR",
        "current_balance": "100.00",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "ETF Global",
        "ticker": "ETF",
        "asset_type": "etf",
        "currency": "EUR",
        "price_source": "manual",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": broker["id"],
        "asset_id": asset["id"],
        "quantity": "10",
        "average_price": "100.00",
        "current_price": "150.00",
    })
    assert holding.status_code == 201

    account = next(
        item for item in client.get("/api/accounts").json()
        if item["id"] == broker["id"]
    )
    assert account["cash_balance_eur"] == "100.00"
    assert account["portfolio_value_eur"] == "1500.00"
    assert account["total_value_eur"] == "1600.00"
    assert account["position_count"] == 1

    overview = client.get("/api/dashboard/overview").json()
    assert overview["investments"] == "1600.00"
    assert overview["net_worth"] == "1600.00"

    from app.core.database import SessionLocal
    from app.modules.ai.tools.personal_finance_tools import _get_net_worth

    db = SessionLocal()
    try:
        ai_result = asyncio.run(_get_net_worth(db))
    finally:
        db.close()
    assert ai_result["net_worth"] == 1600.00
    assert ai_result["by_type"]["broker"] == 1600.00


def test_overview_uses_savings_holding_when_container_balance_is_zero(client):
    account = client.post("/api/accounts", json={
        "name": "Cuenta remunerada existente",
        "type": "savings",
        "currency": "EUR",
        "current_balance": "0.00",
    }).json()
    created = client.post("/api/investments/savings", json={
        "account_id": account["id"],
        "opened_at": "2026-01-01",
        "balance": "19000.00",
        "rate_source": "fixed",
        "fixed_rate": "2.00",
    })
    assert created.status_code == 201

    overview = client.get("/api/dashboard/overview").json()
    assert overview["liquidity"] == "19000.00"
    assert overview["investments"] == "19000.00"
    assert overview["net_worth"] == "19000.00"


def test_overview_counts_new_savings_account_only_once(client):
    created = client.post("/api/investments/savings", json={
        "new_account_name": "Cuenta remunerada nueva",
        "opened_at": "2026-01-01",
        "balance": "19000.00",
        "rate_source": "fixed",
        "fixed_rate": "2.00",
    })
    assert created.status_code == 201

    overview = client.get("/api/dashboard/overview").json()
    assert overview["liquidity"] == "19000.00"
    assert overview["investments"] == "19000.00"
    assert overview["net_worth"] == "19000.00"
