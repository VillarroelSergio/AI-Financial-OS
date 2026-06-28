def _seed_spending(client):
    account = client.post("/api/accounts", json={"name": "BBVA", "type": "bank", "currency": "EUR"}).json()
    casa = client.post("/api/categories", json={"name": "Casa", "type": "expense"}).json()
    comida = client.post("/api/categories", json={"name": "Comida", "type": "expense"}).json()
    salary = client.post("/api/categories", json={"name": "Nomina", "type": "income"}).json()
    client.post("/api/transactions", json={
        "account_id": account["id"], "category_id": casa["id"], "date": "2026-06-12",
        "description": "Alquiler", "amount": "-456.00", "currency": "EUR", "type": "expense",
    })
    client.post("/api/transactions", json={
        "account_id": account["id"], "category_id": casa["id"], "date": "2026-06-15",
        "description": "Comunidad", "amount": "-44.00", "currency": "EUR", "type": "expense",
    })
    client.post("/api/transactions", json={
        "account_id": account["id"], "category_id": comida["id"], "date": "2026-06-16",
        "description": "Supermercado", "amount": "-500.00", "currency": "EUR", "type": "expense",
    })
    client.post("/api/transactions", json={
        "account_id": account["id"], "category_id": casa["id"], "date": "2026-07-01",
        "description": "Alquiler julio", "amount": "-600.00", "currency": "EUR", "type": "expense",
    })
    client.post("/api/transactions", json={
        "account_id": account["id"], "category_id": salary["id"], "date": "2026-06-01",
        "description": "Nomina", "amount": "2000.00", "currency": "EUR", "type": "income",
    })
    return casa


def test_expense_category_detail_month(client):
    casa = _seed_spending(client)
    r = client.get(f"/api/dashboard/spending/category-detail?category_id={casa['id']}&month=2026-06")
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "Casa"
    assert data["period"] == "2026-06"
    assert data["transaction_count"] == 2
    assert data["total"] == "500.00"
    assert [tx["description"] for tx in data["transactions"]] == ["Comunidad", "Alquiler"]


def test_expense_category_detail_year(client):
    casa = _seed_spending(client)
    r = client.get(f"/api/dashboard/spending/category-detail?category_id={casa['id']}&year=2026")
    assert r.status_code == 200
    data = r.json()
    assert data["period_type"] == "year"
    assert data["transaction_count"] == 3
    assert data["total"] == "1100.00"


def test_expense_category_detail_percentage(client):
    casa = _seed_spending(client)
    r = client.get(f"/api/dashboard/spending/category-detail?category_id={casa['id']}&month=2026-06")
    assert r.status_code == 200
    assert r.json()["percentage"] == 50.0


def test_expense_category_detail_empty(client):
    casa = _seed_spending(client)
    r = client.get(f"/api/dashboard/spending/category-detail?category_id={casa['id']}&month=2025-01")
    assert r.status_code == 200
    data = r.json()
    assert data["transaction_count"] == 0
    assert data["transactions"] == []
