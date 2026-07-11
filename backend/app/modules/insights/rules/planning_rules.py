"""INS-5 (Lote 1): planificación — vencimientos próximos, encarecimiento de recurrentes,
anomalías de facturas del hogar y recordatorio de cierre de mes.

Reglas deterministas que reutilizan servicios existentes (calendar recurrente, resumen de
facturas, readiness de patrimonio). No duplican su cálculo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.recurring_transaction import RecurringTransaction
from app.modules.dashboard.routes import _to_eur
from app.modules.household_bills.routes import household_bill_summary
from app.modules.insights.constants import (
    RECURRING_CREEP_LOOKBACK_DAYS,
    RECURRING_CREEP_PCT_THRESHOLD,
    UPCOMING_CASHFLOW_DAYS,
)
from app.modules.insights.schemas import (
    DataStatus,
    InsightActionOut,
    InsightMetricOut,
    InsightOut,
    InsightSeverity,
    InsightSourceOut,
    InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority
from app.modules.net_worth.routes import get_snapshot_readiness
from app.modules.recurring.routes import get_calendar

_LIQUID_TYPES = ("cash", "bank", "savings")
_MONTHLY_FACTOR = {"monthly": Decimal("1"), "weekly": Decimal("52") / Decimal("12"),
                   "yearly": Decimal("1") / Decimal("12")}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _prev_month(month: str) -> str:
    y, m = (int(p) for p in month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _liquidity_eur(db: Session) -> Decimal:
    rates: dict[str, float | None] = {}
    accts = (
        db.query(Account)
        .filter(Account.is_active == True, Account.is_liability == False)  # noqa: E712
        .filter(Account.type.in_(_LIQUID_TYPES))
        .all()
    )
    return sum((_to_eur(a.current_balance or Decimal("0"), a.currency, rates) for a in accts), Decimal("0"))


def upcoming_cashflow_insight(db: Session, period: str) -> list[InsightOut]:
    """Los cargos recurrentes de los próximos 15 días superan la liquidez disponible."""
    events = get_calendar(days=UPCOMING_CASHFLOW_DAYS, db=db)
    upcoming_expense = sum(
        (Decimal(str(e.amount)) for e in events if e.type == "expense"), Decimal("0")
    )
    if upcoming_expense <= 0:
        return []
    liquidity = _liquidity_eur(db)
    if upcoming_expense <= liquidity:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    deficit = upcoming_expense - liquidity
    return [InsightOut(
        id=f"insight_{period}_upcoming_cashflow",
        type=InsightType.upcoming_cashflow,
        severity=InsightSeverity.critical,
        title="Vencimientos próximos por encima de tu liquidez",
        summary=(
            f"En los próximos {UPCOMING_CASHFLOW_DAYS} días vencen {float(upcoming_expense):.0f} € "
            f"en cargos recurrentes y tu liquidez disponible es {float(liquidity):.0f} € "
            f"(faltan {float(deficit):.0f} €)."
        ),
        period=period,
        impact_area="spending",
        dedupe_key=f"upcoming_cashflow:{period}",
        confidence=compute_confidence("complete"),
        priority=compute_priority("critical", "complete", 92.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Déficit previsto", value=float(deficit), unit="EUR"),
        secondary_metrics=[
            InsightMetricOut(label="Vencimientos", value=float(upcoming_expense), unit="EUR"),
            InsightMetricOut(label="Liquidez", value=float(liquidity), unit="EUR"),
        ],
        sources=[InsightSourceOut(type="recurring", label="Recurrentes", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver calendario", target="/recurring", params={})],
        created_at=now_iso,
    )]


def recurring_creep_insight(db: Session, period: str) -> list[InsightOut]:
    """El gasto recurrente comprometido ha crecido ≥ umbral por altas de los últimos 90 días.

    ponytail: sin histórico del recurrente, "crecimiento vs hace 3 meses" se aproxima con las
    altas (created_at) de la ventana; upgrade a serie mensual si se guarda histórico.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RECURRING_CREEP_LOOKBACK_DAYS)
    rts = (
        db.query(RecurringTransaction)
        .filter(RecurringTransaction.active == True, RecurringTransaction.type == "expense")  # noqa: E712
        .all()
    )

    def monthly(rt: RecurringTransaction) -> Decimal:
        return abs(rt.amount or Decimal("0")) * _MONTHLY_FACTOR.get(rt.frequency, Decimal("1"))

    total = sum((monthly(rt) for rt in rts), Decimal("0"))
    added = sum((monthly(rt) for rt in rts if rt.created_at and _aware(rt.created_at) >= cutoff), Decimal("0"))
    base = total - added
    if base <= 0 or added <= 0:
        return []
    pct = (added / base) * Decimal("100")
    if pct < RECURRING_CREEP_PCT_THRESHOLD:
        return []

    now_iso = now.isoformat()
    return [InsightOut(
        id=f"insight_{period}_recurring_creep",
        type=InsightType.recurring_creep,
        severity=InsightSeverity.warning,
        title="Tus gastos recurrentes han subido",
        summary=(
            f"El gasto recurrente comprometido ha crecido un {float(pct):.0f}% en los últimos "
            f"3 meses: {float(added):.0f} €/mes en nuevas altas sobre una base de {float(base):.0f} €/mes."
        ),
        period=period,
        impact_area="spending",
        dedupe_key=f"recurring_creep:{period}",
        confidence=compute_confidence("complete"),
        priority=compute_priority("warning", "complete", 70.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Crecimiento", value=float(pct), unit="%", precision=0),
        secondary_metrics=[
            InsightMetricOut(label="Nuevas altas", value=float(added), unit="EUR"),
            InsightMetricOut(label="Base mensual", value=float(base), unit="EUR"),
        ],
        sources=[InsightSourceOut(type="recurring", label="Recurrentes", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver recurrentes", target="/recurring", params={})],
        created_at=now_iso,
    )]


def household_bill_anomaly_insights(db: Session, period: str) -> list[InsightOut]:
    """Expone como insight las subidas anómalas que household_bills ya detecta (anomaly=True)."""
    summary = household_bill_summary(db)
    now_iso = datetime.now(timezone.utc).isoformat()
    out: list[InsightOut] = []
    for it in summary.items:
        if not it.anomaly or it.change_pct is None:
            continue
        label = f"{it.service_type} · {it.provider}"
        out.append(InsightOut(
            id=f"insight_{period}_bill_{it.service_type}_{it.provider}",
            type=InsightType.household_bill_anomaly,
            severity=InsightSeverity.warning,
            title=f"Factura de {it.service_type} más alta de lo habitual",
            summary=(
                f"La última factura de {label} ({it.last_amount:.0f} €) subió un {it.change_pct:.0f}% "
                f"respecto a la anterior ({(it.previous_amount or 0):.0f} €)."
            ),
            period=period,
            impact_area="spending",
            dedupe_key=f"household_bill_anomaly:{it.service_type}:{it.provider}",
            confidence=compute_confidence("complete"),
            priority=compute_priority("warning", "complete", 68.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Subida", value=it.change_pct, unit="%", precision=0),
            secondary_metrics=[
                InsightMetricOut(label="Última", value=it.last_amount, unit="EUR"),
                InsightMetricOut(label="Anterior", value=it.previous_amount or 0.0, unit="EUR"),
            ],
            sources=[InsightSourceOut(type="household_bills", label="Facturas del hogar",
                                      period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver facturas", target="/household-bills", params={})],
            created_at=now_iso,
        ))
    return out


def snapshot_pending_insight(db: Session, period: str) -> list[InsightOut]:
    """Cierre del mes anterior no realizado, o realizado como parcial (con faltantes)."""
    prev = _prev_month(period)
    # Sin ninguna cuenta el concepto de patrimonio no aplica: no molestamos con el recordatorio.
    if db.query(Account.id).first() is None:
        return []
    readiness = get_snapshot_readiness(month=prev, db=db)
    if readiness.snapshot_exists and readiness.snapshot_state != "partial":
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    missing = [i.label for i in readiness.items if i.status != "ok"]
    if not readiness.snapshot_exists:
        title = f"Cierre de {prev} pendiente"
        summary = f"Aún no has cerrado el mes {prev}. Crea el snapshot de patrimonio para seguir su evolución."
    else:
        title = f"Cierre de {prev} incompleto"
        summary = f"El cierre de {prev} se guardó como parcial. Completa lo pendiente y reciérralo."
    detail = ("Pendiente: " + ", ".join(missing)) if missing else ""
    return [InsightOut(
        id=f"insight_{period}_snapshot_pending",
        type=InsightType.snapshot_pending,
        severity=InsightSeverity.info,
        title=title,
        summary=summary,
        detail=detail,
        period=period,
        impact_area="net_worth",
        dedupe_key=f"snapshot_pending:{prev}",
        confidence=compute_confidence("partial"),
        priority=compute_priority("info", "partial", 55.0),
        data_status=DataStatus.partial,
        sources=[InsightSourceOut(type="net_worth", label="Patrimonio", period=prev, updated_at=now_iso)],
        actions=[InsightActionOut(label="Cerrar mes", target="/overview", params={"month": prev})],
        created_at=now_iso,
    )]
