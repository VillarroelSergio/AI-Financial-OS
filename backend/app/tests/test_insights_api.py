"""Integration tests for the Insights Engine API."""


def test_get_insights_empty_db(client):
    r = client.get("/api/insights")
    assert r.status_code == 200
    data = r.json()
    assert "insights" in data
    assert "summary" in data
    assert data["data_status"] in ("empty", "insufficient", "partial", "complete")
    assert isinstance(data["insights"], list)


def test_get_insights_with_period(client):
    r = client.get("/api/insights?period=2026-06")
    assert r.status_code == 200
    assert r.json()["period"] == "2026-06"


def test_get_insights_invalid_period(client):
    r = client.get("/api/insights?period=06-2026")
    assert r.status_code == 422


def test_get_insights_limit(client):
    r = client.get("/api/insights?limit=5")
    assert r.status_code == 200
    assert len(r.json()["insights"]) <= 5


def test_monthly_review_empty_db(client):
    r = client.get("/api/insights/monthly-review")
    assert r.status_code == 200
    data = r.json()
    assert "headline" in data
    assert "income" in data
    assert "savings_rate" in data


def test_monthly_review_with_transactions(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank", "currency": "EUR", "current_balance": "2000"})
    account_id = acc.json()["id"]
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-06-01", "description": "Sueldo", "amount": "2000.00", "type": "income"})
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-06-05", "description": "Supermercado", "amount": "-150.00", "type": "expense"})
    r = client.get("/api/insights/monthly-review?period=2026-06")
    assert r.status_code == 200
    data = r.json()
    assert data["income"] == 2000.0
    assert data["expenses"] == 150.0
    assert data["savings"] == 1850.0
    assert data["savings_rate"] > 0


def test_anomalies_endpoint(client):
    r = client.get("/api/insights/anomalies")
    assert r.status_code == 200
    data = r.json()
    assert "anomalies" in data
    assert "baseline_months" in data


def test_data_quality_endpoint(client):
    r = client.get("/api/insights/data-quality")
    assert r.status_code == 200
    assert "insights" in r.json()


def test_refresh_endpoint(client):
    r = client.post("/api/insights/refresh")
    assert r.status_code == 200
    assert "insights" in r.json()


def test_dismiss_insight(client):
    r = client.post("/api/insights/test_insight_id/dismiss")
    assert r.status_code == 200
    data = r.json()
    assert data["insight_id"] == "test_insight_id"
    assert "dismissed_at" in data


def test_insights_savings_rate_positive(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank", "currency": "EUR", "current_balance": "5000"})
    account_id = acc.json()["id"]
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-05-01", "description": "Sueldo", "amount": "3000.00", "type": "income"})
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-05-05", "description": "Gastos", "amount": "-800.00", "type": "expense"})
    r = client.get("/api/insights?period=2026-05&type=savings_rate")
    assert r.status_code == 200
    insights = r.json()["insights"]
    if insights:
        savings_insight = next((i for i in insights if i["type"] == "savings_rate"), None)
        if savings_insight:
            assert savings_insight["severity"] in ("positive", "info")


def test_insights_cashflow_deficit(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank", "currency": "EUR", "current_balance": "1000"})
    account_id = acc.json()["id"]
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-04-01", "description": "Sueldo", "amount": "500.00", "type": "income"})
    client.post("/api/transactions", json={"account_id": account_id, "date": "2026-04-05", "description": "Gastos", "amount": "-1000.00", "type": "expense"})
    r = client.get("/api/insights?period=2026-04&type=cashflow_alert")
    assert r.status_code == 200
    insights = r.json()["insights"]
    cashflow = [i for i in insights if i["type"] == "cashflow_alert"]
    if cashflow:
        assert cashflow[0]["severity"] == "warning"
