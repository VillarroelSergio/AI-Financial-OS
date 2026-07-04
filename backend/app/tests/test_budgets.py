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
