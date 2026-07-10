"""Regresiones INS-4 (Balance General + cierre asistido): invariante, readiness, snapshots."""
from datetime import datetime, timezone
from decimal import Decimal

from app.core import database as db_module
from app.models.transaction import Transaction


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _add_tx_this_month(account_id: str) -> None:
    db = db_module.SessionLocal()
    try:
        db.add(Transaction(
            account_id=account_id, date=f"{_month()}-15", description="Compra",
            amount=Decimal("-20.00"), type="expense",
        ))
        db.commit()
    finally:
        db.close()


# ---- DoD: activos − pasivos = patrimonio ----

def test_balance_sheet_invariant(client):
    client.post("/api/accounts", json={"name": "Banco", "type": "bank",
                                       "currency": "EUR", "current_balance": "10000.00"})
    client.post("/api/accounts", json={"name": "Hipoteca", "type": "mortgage",
                                       "currency": "EUR", "current_balance": "-80000.00",
                                       "is_liability": True})
    sheet = client.get("/api/net-worth/balance-sheet").json()
    assert Decimal(sheet["total_assets"]) - Decimal(sheet["total_liabilities"]) == Decimal(sheet["net_worth"])
    assert Decimal(sheet["total_liabilities"]) == Decimal("80000.00")


# ---- DoD: checklist derivada ----

def test_readiness_missing_when_no_data(client):
    r = client.get("/api/net-worth/snapshot-readiness").json()
    assert r["ready"] is False
    movimientos = next(i for i in r["items"] if i["key"] == "movimientos")
    assert movimientos["status"] == "missing"


def test_readiness_ready_with_fresh_data(client):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank",
                                             "currency": "EUR", "current_balance": "500.00"}).json()
    _add_tx_this_month(acc["id"])
    r = client.get("/api/net-worth/snapshot-readiness").json()
    assert r["ready"] is True
    assert all(i["status"] == "ok" for i in r["items"])


# ---- DoD: ningún snapshot sin acción; parcial registra faltantes ----

def test_snapshot_blocked_until_ready_or_partial(client):
    month = _month()
    # sin datos → no ready → cierre completo rechazado
    blocked = client.post("/api/net-worth/snapshots", json={"month": month, "force_partial": False})
    assert blocked.status_code == 409
    assert client.get("/api/net-worth/snapshots").json() == []

    # cierre parcial siempre disponible y registra faltantes
    partial = client.post("/api/net-worth/snapshots", json={"month": month, "force_partial": True})
    assert partial.status_code == 201
    body = partial.json()
    assert body["data_state"] == "partial"
    assert body["missing_items"]  # al menos 'Movimientos del mes'
    assert len(client.get("/api/net-worth/snapshots").json()) == 1


def test_snapshot_complete_when_ready(client):
    month = _month()
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank",
                                             "currency": "EUR", "current_balance": "500.00"}).json()
    _add_tx_this_month(acc["id"])
    done = client.post("/api/net-worth/snapshots", json={"month": month, "force_partial": False})
    assert done.status_code == 201
    assert done.json()["data_state"] == "complete"
    # idempotente por mes: recerrar reemplaza, no duplica
    client.post("/api/net-worth/snapshots", json={"month": month, "force_partial": False})
    assert len(client.get("/api/net-worth/snapshots").json()) == 1
