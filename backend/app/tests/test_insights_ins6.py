"""INS-6 (Lote 2): tendencias y patrimonio. Cada regla dispara/no-dispara con series
sintéticas de meses completos y lleva su dedupe_key propio.

Se prueban las reglas de forma directa sembrando la BD temporal del fixture `client`.
"""
from datetime import datetime, timezone
from decimal import Decimal

from app.core import database as db_module
from app.models.account import Account
from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.modules.insights.rules.trend_rules import (
    category_trend_insights,
    emergency_fund_coverage_insight,
    real_return_insight,
    savings_rate_trend_insight,
)
from app.modules.insights.schemas import InsightClass
from app.modules.insights.service import _classify

_PERIOD = "2026-07"


def _session():
    return db_module.SessionLocal()


def _prev_months(period, n):
    y, m = int(period[:4]), int(period[5:7])
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        out.append(f"{y}-{m:02d}")
    return out  # reciente→antiguo


def _income(db, month, amount):
    db.add(Transaction(account_id="a1", date=f"{month}-05", description="Nómina",
                       amount=Decimal(str(amount)), type="income"))


def _expense(db, month, amount, cat="c1"):
    db.add(Transaction(account_id="a1", category_id=cat, date=f"{month}-10", description="Gasto",
                       amount=Decimal(str(amount)), type="expense"))


# ---- savings_rate_trend ----

def test_savings_rate_trend_fires_on_sustained_improvement(client):
    db = _session()
    try:
        months = _prev_months(_PERIOD, 6)  # reciente→antiguo
        # tasa de ahorro creciente: los recientes ahorran más
        rates = [0.40, 0.35, 0.30, 0.10, 0.05, 0.0]  # alineado reciente→antiguo
        for m, r in zip(months, rates):
            _income(db, m, 1000)
            _expense(db, m, 1000 * (1 - r))
        db.commit()
        out = savings_rate_trend_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key == f"savings_rate_trend:{_PERIOD}"
    assert _classify(out[0]).insight_class == InsightClass.context


def test_savings_rate_trend_silent_when_flat(client):
    db = _session()
    try:
        for m in _prev_months(_PERIOD, 6):
            _income(db, m, 1000)
            _expense(db, m, 800)  # tasa constante 20%
        db.commit()
        assert savings_rate_trend_insight(db, _PERIOD) == []
    finally:
        db.close()


# ---- category_trend ----

def test_category_trend_fires_on_monotonic_growth(client):
    db = _session()
    try:
        db.add(Category(id="c1", name="Ocio", type="expense"))
        months = list(reversed(_prev_months(_PERIOD, 3)))  # antiguo→reciente
        for m, amt in zip(months, [100, 150, 220]):
            _expense(db, m, amt)
        db.commit()
        out = category_trend_insights(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key == "category_trend:c1"


def test_category_trend_silent_when_not_monotonic(client):
    db = _session()
    try:
        db.add(Category(id="c1", name="Ocio", type="expense"))
        months = list(reversed(_prev_months(_PERIOD, 3)))
        for m, amt in zip(months, [200, 150, 220]):  # baja en el medio
            _expense(db, m, amt)
        db.commit()
        assert category_trend_insights(db, _PERIOD) == []
    finally:
        db.close()


# ---- emergency_fund_coverage ----

def test_emergency_fund_fires_below_threshold(client):
    db = _session()
    try:
        db.add(Account(id="acc_liq", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("1000.00"), is_active=True, is_liability=False))
        for m in _prev_months(_PERIOD, 3):
            _expense(db, m, 1000)  # gasto medio 1000 → colchón = 1 mes < 3
        db.commit()
        out = emergency_fund_coverage_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    assert out[0].dedupe_key == f"emergency_fund_coverage:{_PERIOD}"


def test_emergency_fund_crosses_goal(client):
    db = _session()
    try:
        db.add(Account(id="acc_liq", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("1000.00"), is_active=True, is_liability=False))
        db.add(Goal(name="Fondo de emergencia", type="emergency_fund",
                    target_amount=Decimal("6000.00"), status="active"))
        for m in _prev_months(_PERIOD, 3):
            _expense(db, m, 1000)
        db.commit()
        out = emergency_fund_coverage_insight(db, _PERIOD)
    finally:
        db.close()
    assert len(out) == 1
    # cruce con objetivo: aparece la métrica secundaria del objetivo
    assert any(mtr.label == "Objetivo" for mtr in out[0].secondary_metrics)


def test_emergency_fund_silent_when_covered(client):
    db = _session()
    try:
        db.add(Account(id="acc_liq", name="Banco", type="bank", currency="EUR",
                       current_balance=Decimal("6000.00"), is_active=True, is_liability=False))
        for m in _prev_months(_PERIOD, 3):
            _expense(db, m, 1000)  # colchón = 6 meses ≥ 3
        db.commit()
        assert emergency_fund_coverage_insight(db, _PERIOD) == []
    finally:
        db.close()


# ---- real_return ----

def test_real_return_silent_without_savings_config(client):
    db = _session()
    try:
        # sin SavingsAccountConfig la regla no puede calcular tipo nominal
        assert real_return_insight(db, _PERIOD) == []
    finally:
        db.close()
