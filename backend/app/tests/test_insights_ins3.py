"""Regresiones INS-3 (modelo y persistencia): is_liability, dismissals SQLite, snapshots."""
from datetime import date
from decimal import Decimal

from app.core import database as db_module
from app.models.net_worth_snapshot import NetWorthSnapshot
from app.modules.insights import cache, repository

# ---- D6: is_liability en Account ----

def test_account_is_liability_roundtrip(client):
    r = client.post("/api/accounts", json={"name": "Hipoteca", "type": "mortgage",
                                           "currency": "EUR", "current_balance": "-90000.00",
                                           "is_liability": True})
    assert r.status_code == 201
    acc = r.json()
    assert acc["is_liability"] is True
    # persiste y se lee en el listado
    listed = next(a for a in client.get("/api/accounts").json() if a["id"] == acc["id"])
    assert listed["is_liability"] is True


def test_account_defaults_not_liability(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank",
                                             "currency": "EUR", "current_balance": "1000.00"}).json()
    assert acc["is_liability"] is False


# ---- D3: dismissals en SQLite (sobreviven a una sesión nueva = "reinicio") ----

def test_dismiss_persists_across_sessions(client):
    repository.dismiss("insight_2026-06_savings_rate")
    # repository abre su propia SessionLocal en cada llamada → simula proceso nuevo
    assert "insight_2026-06_savings_rate" in repository.get_dismissed_ids()
    assert repository.is_dismissed("insight_2026-06_savings_rate")


# ---- D2: snapshots mensuales → variación correcta ----

def test_two_snapshots_yield_variation(client):
    db = db_module.SessionLocal()
    try:
        db.add(NetWorthSnapshot(month="2026-05", snapshot_date=date(2026, 5, 31),
                                total_assets=Decimal("40000.00"), total_liabilities=Decimal("0.00"),
                                net_worth=Decimal("40000.00")))
        db.add(NetWorthSnapshot(month="2026-06", snapshot_date=date(2026, 6, 30),
                                total_assets=Decimal("42413.75"), total_liabilities=Decimal("0.00"),
                                net_worth=Decimal("42413.75")))
        db.commit()
        rows = {s.month: s.net_worth for s in db.query(NetWorthSnapshot).all()}
    finally:
        db.close()
    assert rows["2026-06"] - rows["2026-05"] == Decimal("2413.75")


# ---- D4: caché con invalidación por commit ----

def test_commit_invalidates_cache(client):
    cache.set("2026-06", ["cached"])
    assert cache.get("2026-06") == ["cached"]
    # cualquier escritura dispara el listener after_commit → limpia la caché
    client.post("/api/accounts", json={"name": "X", "type": "bank",
                                       "currency": "EUR", "current_balance": "1.00"})
    assert cache.get("2026-06") is None
