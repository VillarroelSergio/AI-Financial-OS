"""Orchestrator — calls all rules, scores, filters and returns insights."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.modules.insights import repository
from app.modules.insights.constants import DEFAULT_LIMIT
from app.modules.insights.rules.cashflow_rules import cashflow_alert_insight
from app.modules.insights.rules.data_quality_rules import data_quality_insights
from app.modules.insights.rules.goal_rules import goal_progress_insights
from app.modules.insights.rules.investment_rules import (
    fund_stale_valuation_insight,
    investment_allocation_insight,
)
from app.modules.insights.rules.macro_rules import macro_context_insights
from app.modules.insights.rules.market_rules import market_context_insights
from app.modules.insights.rules.net_worth_rules import net_worth_change_insight
from app.modules.insights.rules.spending_rules import (
    monthly_comparison_insights,
    savings_rate_insight,
    spending_anomaly_insights,
)
from app.modules.insights.schemas import (
    AnomaliesOut,
    DataStatus,
    InsightOut,
    InsightSourceOut,
    InsightsSummaryCountOut,
    InsightsSummaryOut,
    MonthlyReviewOut,
)
from app.modules.insights.scoring import sort_and_limit


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
    all_ins: list[InsightOut] = []
    for rule_fn in [
        lambda: spending_anomaly_insights(db, period),
        lambda: monthly_comparison_insights(db, period),
        lambda: savings_rate_insight(db, period),
        lambda: cashflow_alert_insight(db, period),
        lambda: net_worth_change_insight(db, period),
        lambda: investment_allocation_insight(db, period),
        lambda: fund_stale_valuation_insight(db, period),
        lambda: goal_progress_insights(db, period),
        lambda: market_context_insights(db, period),
        lambda: macro_context_insights(db, period),
        lambda: data_quality_insights(db, period),
    ]:
        try:
            all_ins.extend(rule_fn())
        except Exception:
            pass
    return all_ins


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
    income = sum(float(t.amount) for t in txs if t.type == "income")
    expense = abs(sum(float(t.amount) for t in txs if t.type == "expense"))
    savings = income - expense
    savings_rate = round(savings / income * 100, 2) if income > 0 else 0.0

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
            summary = f"Has ahorrado {savings:.0f} €, con una tasa de ahorro del {savings_rate:.1f}%."
        elif savings_rate >= 0:
            headline = "Este mes cierras con ahorro positivo."
            summary = f"Has ahorrado {savings:.0f} € con una tasa del {savings_rate:.1f}%."
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
