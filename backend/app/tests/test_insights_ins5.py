"""INS-5 (Lote 1): cada regla dispara/no-dispara y lleva su dedupe_key propio.

Se prueban las reglas de forma directa sembrando la BD temporal del fixture `client`.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.core import database as db_module
from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.household_bill import HouseholdBill
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.modules.insights.rules.budget_rules import budget_alert_insights
from app.modules.insights.rules.planning_rules import (
    household_bill_anomaly_insights,
    recurring_creep_insight,
    snapshot_pending_insight,
    upcoming_cashflow_insight,
)
from app.modules.insights.schemas import InsightClass
from app.modules.insights.service import _classify

_PERIOD = datetime.now(timezone.utc).strftime("%Y-%m")


def _session():
    return db_module.SessionLocal()


# ---- budget_alert ----

def test_budget_alert_fires_over_threshold(client):
    db = _session()
    try:
        db.add(Category(id="cat_salud", name="Salud", type="expense"))
        db.add(Budget(category_id="cat_salud", amount=Decimal("100.00"), period="monthly",
                      alert_threshold_pct=80, active=True))
        db.add(Transaction(account_id="a1", category_id="cat_salud", date=f"{_PERIOD}-15",
                           description="Farmacia", amount=Decimal("90.00"), type="expense"))
        db.commit()
        out = budget_alert_insights(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key.startswith("budget_alert:")
    assert out[0].primary_metric.value == 90.0


def test_budget_alert_silent_under_threshold(client):
    db = _session()
    try:
        db.add(Category(id="cat_ocio", name="Ocio", type="expense"))
        db.add(Budget(category_id="cat_ocio", amount=Decimal("100.00"), period="monthly",
                      alert_threshold_pct=80, active=True))
        db.add(Transaction(account_id="a1", category_id="cat_ocio", date=f"{_PERIOD}-15",
                           description="Cine", amount=Decimal("50.00"), type="expense"))
        db.commit()
        assert budget_alert_insights(db, _PERIOD) == []
    finally:
        db.close()


# ---- upcoming_cashflow ----

def test_upcoming_cashflow_fires_when_charges_exceed_liquidity(client):
    db = _session()
    try:
        db.add(Account(id="acc_liq", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("10.00"), is_active=True, is_liability=False))
        db.add(RecurringTransaction(name="Alquiler", amount=Decimal("500.00"), currency="EUR",
                                    type="expense", frequency="monthly",
                                    next_date=date.today() + timedelta(days=5), active=True))
        db.commit()
        out = upcoming_cashflow_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key == f"upcoming_cashflow:{_PERIOD}"


def test_upcoming_cashflow_silent_with_enough_liquidity(client):
    db = _session()
    try:
        db.add(Account(id="acc_liq", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("5000.00"), is_active=True, is_liability=False))
        db.add(RecurringTransaction(name="Alquiler", amount=Decimal("500.00"), currency="EUR",
                                    type="expense", frequency="monthly",
                                    next_date=date.today() + timedelta(days=5), active=True))
        db.commit()
        assert upcoming_cashflow_insight(db, _PERIOD) == []
    finally:
        db.close()


# ---- recurring_creep ----

def test_recurring_creep_fires_on_recent_additions(client):
    db = _session()
    try:
        old = RecurringTransaction(name="Base", amount=Decimal("1000.00"), currency="EUR",
                                   type="expense", frequency="monthly",
                                   next_date=date.today(), active=True)
        old.created_at = datetime.now(timezone.utc) - timedelta(days=200)
        new = RecurringTransaction(name="Nueva suscripción", amount=Decimal("300.00"), currency="EUR",
                                   type="expense", frequency="monthly",
                                   next_date=date.today(), active=True)
        new.created_at = datetime.now(timezone.utc)
        db.add_all([old, new])
        db.commit()
        out = recurring_creep_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1  # 300/1000 = 30% ≥ 15%
    assert out[0].dedupe_key == f"recurring_creep:{_PERIOD}"


def test_recurring_creep_silent_without_recent_additions(client):
    db = _session()
    try:
        old = RecurringTransaction(name="Base", amount=Decimal("1000.00"), currency="EUR",
                                   type="expense", frequency="monthly",
                                   next_date=date.today(), active=True)
        old.created_at = datetime.now(timezone.utc) - timedelta(days=200)
        db.add(old)
        db.commit()
        assert recurring_creep_insight(db, _PERIOD) == []
    finally:
        db.close()


# ---- household_bill_anomaly ----

def test_household_bill_anomaly_fires_on_jump(client):
    db = _session()
    try:
        db.add(HouseholdBill(provider="Iberdrola", service_type="electricidad",
                             period_start=date(2026, 5, 1), period_end=date(2026, 5, 31),
                             amount=Decimal("100.00")))
        db.add(HouseholdBill(provider="Iberdrola", service_type="electricidad",
                             period_start=date(2026, 6, 1), period_end=date(2026, 6, 30),
                             amount=Decimal("130.00")))  # +30% ≥ 20% → anomalía
        db.commit()
        out = household_bill_anomaly_insights(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key == "household_bill_anomaly:electricidad:Iberdrola"


def test_household_bill_anomaly_silent_when_stable(client):
    db = _session()
    try:
        db.add(HouseholdBill(provider="Iberdrola", service_type="electricidad",
                             period_start=date(2026, 5, 1), period_end=date(2026, 5, 31),
                             amount=Decimal("100.00")))
        db.add(HouseholdBill(provider="Iberdrola", service_type="electricidad",
                             period_start=date(2026, 6, 1), period_end=date(2026, 6, 30),
                             amount=Decimal("102.00")))  # +2% < 20%
        db.commit()
        assert household_bill_anomaly_insights(db, _PERIOD) == []
    finally:
        db.close()


# ---- snapshot_pending (clase data_quality) ----

def test_snapshot_pending_fires_and_classifies_as_data_quality(client):
    db = _session()
    try:
        db.add(Account(id="acc1", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("1000.00"), is_active=True, is_liability=False))
        db.commit()
        out = snapshot_pending_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key.startswith("snapshot_pending:")
    assert _classify(out[0]).insight_class == InsightClass.data_quality


def test_snapshot_pending_silent_without_accounts(client):
    db = _session()
    try:
        assert snapshot_pending_insight(db, _PERIOD) == []
    finally:
        db.close()
