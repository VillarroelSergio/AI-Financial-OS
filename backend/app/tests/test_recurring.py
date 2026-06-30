from __future__ import annotations
from datetime import date
import pytest
from fastapi.testclient import TestClient


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
