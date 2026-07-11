"""Servicios deterministas de patrimonio (INS-4): balance, readiness, snapshots.

Sin IA. El balance reutiliza la conversión a EUR del dashboard, no la duplica.
"""
from __future__ import annotations

import calendar
import json
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.investment import Holding, InvestmentAsset
from app.models.net_worth_snapshot import NetWorthSnapshot
from app.models.transaction import Transaction
from app.modules.dashboard.routes import _to_eur
from app.modules.net_worth.schemas import (
    BalanceLineOut,
    BalanceSheetOut,
    ReadinessItemOut,
    ReadinessOut,
    SnapshotOut,
)

_ASSET_CLASS_LABEL = {
    "liquidez": "Liquidez",
    "remuneradas": "Cuentas remuneradas",
    "inversion_cash": "Efectivo de inversión",
    "cartera": "Cartera de mercado",
    "fondos": "Fondos",
    "otros": "Otros activos",
}


def _month_start(month: str) -> date:
    y, m = (int(p) for p in month.split("-"))
    return date(y, m, 1)


def _month_end(month: str) -> date:
    y, m = (int(p) for p in month.split("-"))
    return date(y, m, calendar.monthrange(y, m)[1])


def _prev_month(month: str) -> str:
    y, m = (int(p) for p in month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _account_class(acc: Account) -> str:
    if acc.type in ("cash", "bank"):
        return "liquidez"
    if acc.type == "savings":
        return "remuneradas"
    if acc.type in ("broker", "investment"):
        return "inversion_cash"
    return "otros"


def build_balance_sheet(db: Session, month: str) -> BalanceSheetOut:
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
    rates: dict[str, float | None] = {}

    assets: dict[str, Decimal] = {}
    liabilities: dict[str, Decimal] = {}
    for a in accounts:
        eur = _to_eur(a.current_balance or Decimal("0"), a.currency, rates)
        if a.is_liability:
            # el pasivo se muestra en positivo; un saldo negativo es la deuda
            liabilities[a.id] = (liabilities.get(a.id, Decimal("0")) + abs(eur))
        else:
            cls = _account_class(a)
            assets[cls] = assets.get(cls, Decimal("0")) + eur

    # Cartera de mercado (market_value ya en EUR). Fondos separados del resto.
    fund_ids = {
        aid for (aid,) in db.query(InvestmentAsset.id).filter(InvestmentAsset.asset_type == "fund").all()
    }
    portfolio_cost = Decimal("0")
    for h in db.query(Holding).all():
        mv = h.market_value
        if mv is None:
            continue
        cls = "fondos" if h.asset_id in fund_ids else "cartera"
        assets[cls] = assets.get(cls, Decimal("0")) + mv
        portfolio_cost += (h.quantity or Decimal("0")) * (h.average_price or Decimal("0"))

    liab_names = {a.id: a.name for a in accounts if a.is_liability}
    asset_lines = [
        BalanceLineOut(key=k, label=_ASSET_CLASS_LABEL.get(k, k), amount=str(v))
        for k, v in assets.items()
        if v != 0
    ]
    liab_lines = [
        BalanceLineOut(key=aid, label=liab_names.get(aid, "Pasivo"), amount=str(v))
        for aid, v in liabilities.items()
        if v != 0
    ]

    total_assets = sum((v for v in assets.values()), Decimal("0"))
    total_liabilities = sum((v for v in liabilities.values()), Decimal("0"))
    net_worth = total_assets - total_liabilities
    portfolio_mv = assets.get("cartera", Decimal("0")) + assets.get("fondos", Decimal("0"))

    prev = (
        db.query(NetWorthSnapshot)
        .filter(NetWorthSnapshot.month == _prev_month(month))
        .one_or_none()
    )
    change = str(net_worth - prev.net_worth) if prev else None

    return BalanceSheetOut(
        month=month,
        assets=asset_lines,
        liabilities=liab_lines,
        total_assets=str(total_assets),
        total_liabilities=str(total_liabilities),
        net_worth=str(net_worth),
        portfolio_cost=str(portfolio_cost),
        portfolio_gain=str(portfolio_mv - portfolio_cost),
        net_worth_change=change,
    )


def _naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def evaluate_readiness(db: Session, month: str) -> ReadinessOut:
    start = _month_start(month)
    start_dt = datetime(start.year, start.month, start.day)
    items: list[ReadinessItemOut] = []

    # 1. Movimientos del mes
    has_tx = (
        db.query(Transaction.id)
        .filter(Transaction.date.like(f"{month}%"))
        .first()
        is not None
    )
    items.append(ReadinessItemOut(
        key="movimientos", label="Movimientos del mes",
        status="ok" if has_tx else "missing",
        detail="" if has_tx else "No hay transacciones registradas este mes.",
        cta_route="/imports",
    ))

    # 2. Saldos de cuentas frescos (updated_at dentro del mes)
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
    stale_accts = [a for a in accounts if (_naive(a.updated_at) or start_dt) < start_dt]
    items.append(ReadinessItemOut(
        key="saldos", label="Saldos de cuentas",
        status="stale" if stale_accts else "ok",
        detail=f"{len(stale_accts)} cuenta(s) sin actualizar este mes." if stale_accts else "",
        cta_route="/accounts",
    ))

    # 3. Valoración de fondos (holdings manuales sin revalorar en el mes)
    fund_ids = {
        aid for (aid,) in db.query(InvestmentAsset.id).filter(InvestmentAsset.asset_type == "fund").all()
    }
    fund_holdings = [h for h in db.query(Holding).all() if h.asset_id in fund_ids]
    stale_funds = [h for h in fund_holdings if (_naive(h.updated_at) or start_dt) < start_dt]
    items.append(ReadinessItemOut(
        key="fondos", label="Valoración de fondos",
        status="stale" if stale_funds else "ok",
        detail=f"{len(stale_funds)} fondo(s) sin valorar este mes." if stale_funds else "",
        cta_route="/investments",
    ))

    # 4. Precios de posiciones cotizadas (sin market_value = sin precio)
    no_price = db.query(Holding.id).filter(Holding.market_value.is_(None)).count()
    items.append(ReadinessItemOut(
        key="precios", label="Precios de posiciones cotizadas",
        status="stale" if no_price else "ok",
        detail=f"{no_price} posición(es) sin precio." if no_price else "",
        cta_route="/investments",
    ))

    ready = all(i.status == "ok" for i in items)
    existing = db.query(NetWorthSnapshot).filter(NetWorthSnapshot.month == month).one_or_none()
    return ReadinessOut(
        month=month,
        items=items,
        ready=ready,
        snapshot_exists=existing is not None,
        snapshot_state=existing.data_state if existing else None,
    )


def _to_out(s: NetWorthSnapshot) -> SnapshotOut:
    missing = json.loads(s.missing_items_json) if s.missing_items_json else []
    return SnapshotOut(
        id=s.id,
        month=s.month,
        snapshot_date=s.snapshot_date.isoformat(),
        total_assets=str(s.total_assets),
        total_liabilities=str(s.total_liabilities),
        net_worth=str(s.net_worth),
        data_state=s.data_state,
        missing_items=missing,
        currency=s.currency,
        created_at=s.created_at.isoformat() if s.created_at else "",
    )


def list_snapshots(db: Session, date_from: str | None, date_to: str | None) -> list[SnapshotOut]:
    q = db.query(NetWorthSnapshot)
    if date_from:
        q = q.filter(NetWorthSnapshot.month >= date_from)
    if date_to:
        q = q.filter(NetWorthSnapshot.month <= date_to)
    return [_to_out(s) for s in q.order_by(NetWorthSnapshot.month).all()]


def create_snapshot(db: Session, month: str, force_partial: bool) -> SnapshotOut:
    """Idempotente por mes (DELETE+INSERT). Solo vía acción explícita del usuario."""
    readiness = evaluate_readiness(db, month)
    missing = [i.label for i in readiness.items if i.status != "ok"]
    if missing and not force_partial:
        raise ValueError("readiness_incomplete")

    sheet = build_balance_sheet(db, month)
    breakdown = {
        "assets": [line.model_dump() for line in sheet.assets],
        "liabilities": [line.model_dump() for line in sheet.liabilities],
    }
    db.query(NetWorthSnapshot).filter(NetWorthSnapshot.month == month).delete()
    snap = NetWorthSnapshot(
        month=month,
        snapshot_date=_month_end(month),
        total_assets=Decimal(sheet.total_assets),
        total_liabilities=Decimal(sheet.total_liabilities),
        net_worth=Decimal(sheet.net_worth),
        breakdown_json=json.dumps(breakdown),
        data_state="partial" if missing else "complete",
        missing_items_json=json.dumps(missing) if missing else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return _to_out(snap)
