from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority


def cashflow_alert_insight(db: Session, period: str) -> list[InsightOut]:
    txs = db.query(Transaction).filter(Transaction.date.like(f"{period}%")).all()
    income = sum((t.amount for t in txs if t.type == "income"), Decimal("0"))
    expense = abs(sum((t.amount for t in txs if t.type == "expense"), Decimal("0")))
    now_iso = datetime.now(timezone.utc).isoformat()

    if income == 0 and expense == 0:
        return []

    if income == 0:
        return [InsightOut(
            id=f"insight_{period}_cashflow_no_income",
            type=InsightType.cashflow_alert,
            severity=InsightSeverity.warning,
            title="Sin ingresos registrados",
            summary="No hay ingresos registrados este mes. Revisa si faltan importaciones.",
            period=period,
            impact_area="spending",
            confidence=compute_confidence("insufficient"),
            priority=compute_priority("warning", "insufficient", 60.0),
            data_status=DataStatus.insufficient,
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Importar datos", target="/imports", params={})],
            created_at=now_iso,
        )]

    if expense > income:
        deficit = expense - income
        return [InsightOut(
            id=f"insight_{period}_cashflow_deficit",
            type=InsightType.cashflow_alert,
            severity=InsightSeverity.warning,
            title="Gastos superiores a ingresos",
            summary=f"Este mes tus gastos superan tus ingresos registrados en {float(deficit):.0f} €. Puedes revisar si faltan ingresos por importar.",
            period=period,
            impact_area="spending",
            confidence=compute_confidence("complete"),
            priority=compute_priority("warning", "complete", 75.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Déficit", value=float(deficit), unit="EUR"),
            secondary_metrics=[
                InsightMetricOut(label="Ingresos", value=float(income), unit="EUR"),
                InsightMetricOut(label="Gastos", value=float(expense), unit="EUR"),
            ],
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Importar datos", target="/imports", params={})],
            created_at=now_iso,
        )]

    return []
