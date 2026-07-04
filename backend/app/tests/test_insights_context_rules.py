from app.modules.insights.rules.data_quality_rules import data_quality_insights
from app.modules.insights.rules.macro_rules import macro_context_insights
from app.modules.insights.rules.market_rules import market_context_insights


def test_market_no_data_returns_empty_or_partial(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = market_context_insights(db, "2026-06")
        assert isinstance(result, list)
    finally:
        db.close()


def test_macro_no_data_returns_list(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = macro_context_insights(db, "2026-06")
        assert isinstance(result, list)
    finally:
        db.close()


def test_data_quality_no_transactions(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = data_quality_insights(db, "2026-06")
        assert isinstance(result, list)
    finally:
        db.close()


def test_data_quality_uncategorized_transactions(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank", "currency": "EUR", "current_balance": "1000"})
    assert acc.status_code == 201
    account_id = acc.json()["id"]
    tx = client.post("/api/transactions", json={
        "account_id": account_id,
        "date": "2026-06-01",
        "description": "Compra",
        "amount": "-50.00",
        "type": "expense",
    })
    assert tx.status_code == 201
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = data_quality_insights(db, "2026-06")
        types = [i.type.value for i in result]
        assert "data_quality" in types
    finally:
        db.close()
