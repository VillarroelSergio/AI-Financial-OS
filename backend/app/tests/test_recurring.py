from __future__ import annotations
from datetime import date


def test_create_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix",
        "amount": "15.99",
        "type": "expense",
        "frequency": "monthly",
        "day_of_month": 8,
        "next_date": "2026-07-08",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Netflix"


def test_list_recurring(client):
    client.post("/api/recurring", json={
        "name": "Salario", "amount": "2500", "type": "income",
        "frequency": "monthly", "day_of_month": 1, "next_date": "2026-07-01",
    })
    resp = client.get("/api/recurring")
    assert len(resp.json()) == 1


def test_update_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": "2026-07-08",
    })
    rid = resp.json()["id"]
    resp2 = client.put(f"/api/recurring/{rid}", json={"amount": "17.99"})
    assert float(resp2.json()["amount"]) == 17.99


def test_delete_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": "2026-07-08",
    })
    rid = resp.json()["id"]
    assert client.delete(f"/api/recurring/{rid}").status_code == 204


def test_detect_recurring_candidates_requires_confirmation(client):
    for payload in [
        {"account_id": "acc-main", "date": "2026-01-05", "description": "Netflix", "amount": "-15.99", "currency": "EUR", "type": "expense"},
        {"account_id": "acc-main", "date": "2026-02-05", "description": "Netflix", "amount": "-15.99", "currency": "EUR", "type": "expense"},
        {"account_id": "acc-main", "date": "2026-03-05", "description": "Netflix", "amount": "-16.49", "currency": "EUR", "type": "expense"},
    ]:
        assert client.post("/api/transactions", json=payload).status_code == 201

    resp = client.get("/api/recurring/candidates")
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["name"] == "Netflix"
    assert candidate["frequency"] == "monthly"
    assert candidate["type"] == "expense"
    assert candidate["transaction_count"] == 3
    assert len(candidate["transaction_ids"]) == 3
    assert candidate["confidence"] >= 0.7


def test_calendar_returns_events(client):
    client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": str(date.today()),
    })
    resp = client.get("/api/recurring/calendar?days=60")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["name"] == "Netflix"
