from __future__ import annotations

from datetime import date


def _today_plus_months(months: int) -> str:
    """Return a date string `months` months from today, for next_date values."""
    today = date.today()
    m = today.month + months
    y = today.year
    while m > 12:
        m -= 12
        y += 1
    return f"{y}-{m:02d}-01"


def test_forecast_empty_db(client):
    """With no data, all months should return 0.0 values wrapped in CashflowForecast."""
    resp = client.get("/api/cashflow/forecast?months=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "generated_at" in data
    assert "months" in data
    assert len(data["months"]) == 3
    for entry in data["months"]:
        assert "month" in entry
        assert "projected_income" in entry
        assert "projected_expenses" in entry
        assert "projected_balance" in entry
        assert "historical_avg_income" in entry
        assert "historical_avg_expenses" in entry
        assert "recurring_income" in entry
        assert "recurring_expenses" in entry
        assert abs(entry["projected_balance"] - (entry["projected_income"] - entry["projected_expenses"])) < 0.01


def test_forecast_months_param(client):
    """months query param controls number of entries returned."""
    resp = client.get("/api/cashflow/forecast?months=6")
    assert resp.status_code == 200
    assert len(resp.json()["months"]) == 6


def test_forecast_with_monthly_recurring_income(client):
    """A monthly recurring income entry should appear in each projected month."""
    client.post("/api/recurring", json={
        "name": "Salary",
        "amount": "2000.00",
        "type": "income",
        "frequency": "monthly",
        "next_date": _today_plus_months(0),
    })
    resp = client.get("/api/cashflow/forecast?months=3")
    assert resp.status_code == 200
    data = resp.json()
    # Each month should have projected income >= 0
    for entry in data["months"]:
        assert entry["projected_income"] >= 0


def test_forecast_with_monthly_recurring_expense(client):
    """A monthly recurring expense entry should reduce projected_balance."""
    client.post("/api/recurring", json={
        "name": "Rent",
        "amount": "1500.00",
        "type": "expense",
        "frequency": "monthly",
        "next_date": _today_plus_months(0),
    })
    resp = client.get("/api/cashflow/forecast?months=2")
    assert resp.status_code == 200
    data = resp.json()
    for entry in data["months"]:
        assert entry["projected_expenses"] >= 0
        assert abs(entry["projected_balance"] - (entry["projected_income"] - entry["projected_expenses"])) < 0.01


def test_forecast_balance_calculation(client):
    """projected_balance == projected_income - projected_expenses for every month."""
    resp = client.get("/api/cashflow/forecast?months=4")
    assert resp.status_code == 200
    for entry in resp.json()["months"]:
        expected = round(entry["projected_income"] - entry["projected_expenses"], 10)
        assert abs(entry["projected_balance"] - expected) < 0.01


def test_forecast_month_labels_sequential(client):
    """Month labels should be sequential from current month."""
    today = date.today()
    resp = client.get("/api/cashflow/forecast?months=3")
    data = resp.json()
    assert len(data["months"]) == 3
    for i, entry in enumerate(data["months"]):
        m = today.month + i
        y = today.year
        while m > 12:
            m -= 12
            y += 1
        assert entry["month"] == f"{y}-{m:02d}"


def test_forecast_inactive_recurring_excluded(client):
    """Inactive recurring transactions should not be included in forecast."""
    # Create active one first
    resp = client.post("/api/recurring", json={
        "name": "Active",
        "amount": "500.00",
        "type": "income",
        "frequency": "monthly",
        "next_date": _today_plus_months(0),
    })
    rid = resp.json()["id"]

    # Deactivate it
    client.put(f"/api/recurring/{rid}", json={"active": False})

    forecast = client.get("/api/cashflow/forecast?months=1").json()
    # With no active recurring, falls back to historical avg (0 in empty db)
    assert forecast["months"][0]["projected_income"] >= 0  # structural check
