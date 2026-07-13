from __future__ import annotations


def _create_category(client, name: str = "Alimentación") -> str:
    resp = client.post("/api/categories", json={"name": name, "type": "expense"})
    return resp.json()["id"]


def test_create_budget(client):
    cat_id = _create_category(client)
    resp = client.post("/api/budgets", json={
        "category_id": cat_id,
        "period": "monthly",
        "amount": "500.00",
        "alert_threshold_pct": 80,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category_id"] == cat_id
    assert float(data["amount"]) == 500.0


def test_create_budget_rejects_unknown_category(client):
    resp = client.post("/api/budgets", json={"category_id": "cat-inexistente", "amount": "500.00"})
    assert resp.status_code == 422


def test_list_budgets(client):
    cat_id = _create_category(client)
    client.post("/api/budgets", json={"category_id": cat_id, "amount": "300.00"})
    resp = client.get("/api/budgets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_budget(client):
    cat_id = _create_category(client)
    resp = client.post("/api/budgets", json={"category_id": cat_id, "amount": "300.00"})
    bid = resp.json()["id"]
    resp2 = client.put(f"/api/budgets/{bid}", json={"amount": "450.00"})
    assert resp2.status_code == 200
    assert float(resp2.json()["amount"]) == 450.0


def test_delete_budget(client):
    cat_id = _create_category(client)
    resp = client.post("/api/budgets", json={"category_id": cat_id, "amount": "300.00"})
    bid = resp.json()["id"]
    assert client.delete(f"/api/budgets/{bid}").status_code == 204
    assert len(client.get("/api/budgets").json()) == 0


def test_comparison_returns_list(client):
    cat_id = _create_category(client)
    client.post("/api/budgets", json={"category_id": cat_id, "amount": "500.00"})
    resp = client.get("/api/budgets/comparison?month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["budget_amount"] == 500.0
    assert data[0]["actual_amount"] == 0.0
    assert data[0]["over_budget"] is False


def test_comparison_uses_positive_expense_magnitude(client):
    cat_id = _create_category(client, "Restaurante")
    budget = client.post("/api/budgets", json={"category_id": cat_id, "amount": "500.00"})
    assert budget.status_code == 201

    account = client.post("/api/accounts", json={
        "name": "Budget test account",
        "type": "bank",
        "current_balance": "1000.00",
        "currency": "EUR",
    })
    assert account.status_code == 201
    transaction = client.post("/api/transactions", json={
        "description": "Restaurant expense",
        "amount": "-42.30",
        "type": "expense",
        "category_id": cat_id,
        "account_id": account.json()["id"],
        "date": "2026-07-13",
    })
    assert transaction.status_code == 201

    response = client.get("/api/budgets/comparison?month=2026-07")
    assert response.status_code == 200
    item = response.json()[0]
    assert item["actual_amount"] == 42.3
    assert item["remaining"] == 457.7
    assert item["consumption_pct"] == 8.5
    assert item["over_budget"] is False
