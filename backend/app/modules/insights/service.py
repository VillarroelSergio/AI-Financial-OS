"""Orchestrator — calls all rules, scores, filters and returns insights."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.modules.insights import cache, repository
from app.modules.insights.constants import DEFAULT_LIMIT
from app.modules.insights.formatting import fmt_eur, fmt_pct, savings_rate_dec
from app.modules.insights.rules.budget_rules import budget_alert_insights
from app.modules.insights.rules.cashflow_rules import cashflow_alert_insight
from app.modules.insights.rules.data_quality_rules import data_quality_insights
from app.modules.insights.rules.goal_rules import goal_progress_insights
from app.modules.insights.rules.investment_rules import (
    fund_stale_valuation_insight,
    investment_allocation_insight,
)
from app.modules.insights.rules.macro_rules import macro_context_insights
from app.modules.insights.rules.market_rules import market_context_insights
from app.modules.insights.rules.net_worth_rules import (
    net_worth_change_insight,
    wealth_concentration_insight,
)
from app.modules.insights.rules.planning_rules import (
    household_bill_anomaly_insights,
    recurring_creep_insight,
    snapshot_pending_insight,
    upcoming_cashflow_insight,
)
from app.modules.insights.rules.spending_rules import (
    monthly_comparison_insights,
    savings_rate_insight,
    spending_anomaly_insights,
)
from app.modules.insights.rules.trend_rules import (
    category_trend_insights,
    emergency_fund_coverage_insight,
    real_return_insight,
    savings_rate_trend_insight,
)
from app.modules.insights.schemas import (
    AnomaliesOut,
    DataStatus,
    InsightClass,
    InsightOut,
    InsightSourceOut,
    InsightsSummaryCountOut,
    InsightsSummaryOut,
    MonthlyReviewOut,
)
from app.modules.insights.scoring import sort_and_limit

# Taxonomía única (INS-2): la clase se deriva del tipo en un solo punto, no en cada regla.
_CONTEXT_TYPES = {"savings_rate", "market_context", "macro_context", "wealth_concentration",
                  "real_return", "savings_rate_trend"}
# snapshot_pending es un aviso de dato incompleto (INS-5), no una señal accionable.
_DATA_QUALITY_TYPES = {"data_quality", "snapshot_pending"}


def _classify(insight: InsightOut) -> InsightOut:
    if insight.type.value in _DATA_QUALITY_TYPES:
        insight.insight_class = InsightClass.data_quality
    elif insight.type.value in _CONTEXT_TYPES:
        insight.insight_class = InsightClass.context
    else:
        insight.insight_class = InsightClass.signal
    return insight


def _dedupe(insights: list[InsightOut]) -> list[InsightOut]:
    """Conserva una instancia por `dedupe_key` (o `id`), la de mayor prioridad. (INS-B3)."""
    best: dict[str, InsightOut] = {}
    for i in insights:
        key = i.dedupe_key or i.id
        if key not in best or i.priority > best[key].priority:
            best[key] = i
    return list(best.values())


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _determine_data_status(insights: list[InsightOut], db: Session, period: str) -> DataStatus:
    tx_count = db.query(Transaction).filter(Transaction.date.like(f"{period}%")).count()
    if tx_count == 0:
        return DataStatus.empty
    partial = any(i.data_status in (DataStatus.partial, DataStatus.insufficient) for i in insights)
    return DataStatus.partial if partial else DataStatus.complete


def _make_summary(insights: list[InsightOut]) -> InsightsSummaryCountOut:
    return InsightsSummaryCountOut(
        total=len(insights),
        positive=sum(1 for i in insights if i.severity.value == "positive"),
        info=sum(1 for i in insights if i.severity.value == "info"),
        warning=sum(1 for i in insights if i.severity.value == "warning"),
        critical=sum(1 for i in insights if i.severity.value == "critical"),
        partial=sum(1 for i in insights if i.data_status.value == "partial"),
        insufficient=sum(1 for i in insights if i.data_status.value == "insufficient"),
    )


def _all_insights(db: Session, period: str) -> list[InsightOut]:
    cached = cache.get(period)
    if cached is not None:
        return cached  # type: ignore[return-value]
    all_ins: list[InsightOut] = []
    for rule_fn in [
        lambda: spending_anomaly_insights(db, period),
        lambda: monthly_comparison_insights(db, period),
        lambda: savings_rate_insight(db, period),
        lambda: cashflow_alert_insight(db, period),
        lambda: net_worth_change_insight(db, period),
        lambda: wealth_concentration_insight(db, period),
        lambda: investment_allocation_insight(db, period),
        lambda: fund_stale_valuation_insight(db, period),
        lambda: goal_progress_insights(db, period),
        lambda: market_context_insights(db, period),
        lambda: macro_context_insights(db, period),
        lambda: data_quality_insights(db, period),
        # INS-5 (Lote 1: planificación)
        lambda: budget_alert_insights(db, period),
        lambda: upcoming_cashflow_insight(db, period),
        lambda: recurring_creep_insight(db, period),
        lambda: household_bill_anomaly_insights(db, period),
        lambda: snapshot_pending_insight(db, period),
        # INS-6 (Lote 2: tendencias y patrimonio)
        lambda: savings_rate_trend_insight(db, period),
        lambda: category_trend_insights(db, period),
        lambda: emergency_fund_coverage_insight(db, period),
        lambda: real_return_insight(db, period),
    ]:
        try:
            all_ins.extend(rule_fn())
        except Exception:
            pass
    return cache.set(period, _dedupe([_classify(i) for i in all_ins]))


def get_insights(
    db: Session,
    period: str | None = None,
    type_filter: str | None = None,
    severity_filter: str | None = None,
    impact_area: str | None = None,
    limit: int = DEFAULT_LIMIT,
    include_dismissed: bool = False,
) -> InsightsSummaryOut:
    p = period or _current_period()
    insights = _all_insights(db, p)

    dismissed = repository.get_dismissed_ids()
    if not include_dismissed:
        insights = [i for i in insights if i.id not in dismissed]

    if type_filter:
        insights = [i for i in insights if i.type.value == type_filter]
    if severity_filter:
        insights = [i for i in insights if i.severity.value == severity_filter]
    if impact_area:
        insights = [i for i in insights if i.impact_area == impact_area]

    sorted_insights = sort_and_limit(insights, limit)
    data_status = _determine_data_status(insights, db, p)
    # Sin transacciones en el periodo, los insights de contexto (macro/mercado/calidad)
    # contradicen al cuerpo "sin datos": badge y lista deben derivar del mismo estado.
    if data_status == DataStatus.empty:
        sorted_insights = []

    return InsightsSummaryOut(
        period=p,
        generated_at=datetime.now(timezone.utc).isoformat(),
        data_status=data_status,
        insights=sorted_insights,
        summary=_make_summary(sorted_insights),
    )


def get_monthly_review(db: Session, period: str | None = None) -> MonthlyReviewOut:
    p = period or _current_period()

    txs = db.query(Transaction).filter(Transaction.date.like(f"{p}%")).all()
    income = sum((t.amount for t in txs if t.type == "income"), Decimal("0"))
    expense = abs(sum((t.amount for t in txs if t.type == "expense"), Decimal("0")))
    savings = income - expense
    # Misma definición y redondeo que la regla savings_rate (INS-B1): una sola cifra.
    savings_rate = savings_rate_dec(income, expense)

    if income == 0 and expense == 0:
        data_status = DataStatus.empty
        headline = "Aún no hay datos para este mes."
        summary = "Importa movimientos para generar un resumen mensual."
    elif income == 0:
        data_status = DataStatus.insufficient
        headline = "Datos de ingresos incompletos."
        summary = "No hay ingresos registrados este mes. Revisa si faltan importaciones."
    else:
        data_status = DataStatus.complete
        if savings_rate >= 20:
            headline = "Este mes mantienes una situación financiera sólida."
            summary = f"Has ahorrado {fmt_eur(savings)}, con una tasa de ahorro del {fmt_pct(savings_rate)}."
        elif savings_rate >= 0:
            headline = "Este mes cierras con ahorro positivo."
            summary = f"Has ahorrado {fmt_eur(savings)} con una tasa del {fmt_pct(savings_rate)}."
        else:
            headline = "Este mes los gastos superan los ingresos registrados."
            summary = "Puedes revisar si faltan ingresos por importar o si hubo gastos extraordinarios."

    all_ins = _all_insights(db, p)
    positives = [i for i in all_ins if i.severity.value == "positive"]
    warnings = [i for i in all_ins if i.severity.value in ("warning", "critical")]
    sources = [InsightSourceOut(type="transactions", label="Movimientos", period=p,
                                updated_at=datetime.now(timezone.utc).isoformat())]

    return MonthlyReviewOut(
        period=p,
        headline=headline,
        summary=summary,
        income=round(income, 2),
        expenses=round(expense, 2),
        savings=round(savings, 2),
        savings_rate=savings_rate,
        net_worth_change=None,
        top_positive=sort_and_limit(positives, 2),
        top_warnings=sort_and_limit(warnings, 2),
        top_changes=[],
        data_status=data_status,
        sources=sources,
    )


def get_anomalies(db: Session, period: str | None = None, baseline_months: int = 3) -> AnomaliesOut:
    p = period or _current_period()
    anomalies = spending_anomaly_insights(db, p)
    tx_count = db.query(Transaction).filter(Transaction.date.like(f"{p}%")).count()
    status = DataStatus.empty if tx_count == 0 else DataStatus.complete
    return AnomaliesOut(period=p, baseline_months=baseline_months, data_status=status, anomalies=anomalies)


def get_data_quality(db: Session, period: str | None = None) -> InsightsSummaryOut:
    p = period or _current_period()
    dq = data_quality_insights(db, p)
    tx_count = db.query(Transaction).filter(Transaction.date.like(f"{p}%")).count()
    status = DataStatus.empty if tx_count == 0 else DataStatus.partial
    return InsightsSummaryOut(
        period=p,
        generated_at=datetime.now(timezone.utc).isoformat(),
        data_status=status,
        insights=dq,
        summary=_make_summary(dq),
    )
