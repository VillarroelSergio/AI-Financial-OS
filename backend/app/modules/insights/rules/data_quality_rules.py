from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.investment import Holding
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority


def data_quality_insights(db: Session, period: str) -> list[InsightOut]:
    now_iso = datetime.now(timezone.utc).isoformat()
    insights: list[InsightOut] = []

    all_txs = db.query(Transaction).count()
    if all_txs == 0:
        return [InsightOut(
            id=f"insight_{period}_dq_no_transactions",
            type=InsightType.data_quality,
            severity=InsightSeverity.info,
            title="Sin movimientos importados",
            summary="No hay movimientos registrados. Importa un CSV para empezar a generar insights.",
            period=period,
            impact_area="calidad",
            confidence=compute_confidence("empty"),
            priority=compute_priority("info", "empty", 60.0),
            data_status=DataStatus.empty,
            sources=[InsightSourceOut(type="transactions", label="Movimientos", updated_at=now_iso)],
            actions=[InsightActionOut(label="Importar datos", target="/imports", params={})],
            created_at=now_iso,
        )]

    period_txs = db.query(Transaction).filter(Transaction.date.like(f"{period}%")).all()
    uncategorized = [t for t in period_txs if t.type == "expense" and t.category_id is None]
    if uncategorized:
        insights.append(InsightOut(
            id=f"insight_{period}_dq_uncategorized",
            type=InsightType.data_quality,
            severity=InsightSeverity.info,
            title="Hay movimientos sin categoría",
            summary=f"{len(uncategorized)} movimiento(s) de gasto no tienen categoría asignada. Clasificarlos mejorará los análisis.",
            period=period,
            impact_area="calidad",
            confidence=compute_confidence("partial"),
            priority=compute_priority("info", "partial", 65.0),
            data_status=DataStatus.partial,
            primary_metric=InsightMetricOut(label="Sin categoría", value=float(len(uncategorized)), unit="movimientos"),
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver movimientos", target="/transactions", params={"period": period})],
            created_at=now_iso,
        ))

    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
    if not accounts:
        insights.append(InsightOut(
            id=f"insight_{period}_dq_no_accounts",
            type=InsightType.data_quality,
            severity=InsightSeverity.info,
            title="Sin cuentas configuradas",
            summary="No hay cuentas activas. Configura tus cuentas para calcular el patrimonio correctamente.",
            period=period,
            impact_area="calidad",
            confidence=compute_confidence("empty"),
            priority=compute_priority("info", "empty", 55.0),
            data_status=DataStatus.empty,
            sources=[InsightSourceOut(type="accounts", label="Cuentas", updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver cuentas", target="/accounts", params={})],
            created_at=now_iso,
        ))

    holdings_no_price = db.query(Holding).filter(Holding.current_price == None).count()  # noqa: E711
    if holdings_no_price > 0:
        insights.append(InsightOut(
            id=f"insight_{period}_dq_holdings_no_price",
            type=InsightType.data_quality,
            severity=InsightSeverity.info,
            title="Posiciones sin precio actualizado",
            summary=f"{holdings_no_price} posición(es) no tienen precio actualizado. El valor de cartera puede no ser preciso.",
            period=period,
            impact_area="calidad",
            confidence=compute_confidence("partial"),
            priority=compute_priority("info", "partial", 50.0),
            data_status=DataStatus.partial,
            primary_metric=InsightMetricOut(label="Sin precio", value=float(holdings_no_price), unit="posiciones"),
            sources=[InsightSourceOut(type="investments", label="Inversiones", updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver inversiones", target="/investments", params={})],
            created_at=now_iso,
        ))

    incomplete_goals = db.query(Goal).filter(Goal.status == "active", Goal.target_date == None).count()  # noqa: E711
    if incomplete_goals > 0:
        insights.append(InsightOut(
            id=f"insight_{period}_dq_goals_no_date",
            type=InsightType.data_quality,
            severity=InsightSeverity.info,
            title="Objetivos sin fecha límite",
            summary=f"{incomplete_goals} objetivo(s) no tienen fecha objetivo. Añadirla mejorará el seguimiento del ritmo de ahorro.",
            period=period,
            impact_area="calidad",
            confidence=compute_confidence("partial"),
            priority=compute_priority("info", "partial", 40.0),
            data_status=DataStatus.partial,
            sources=[InsightSourceOut(type="goals", label="Objetivos", updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver objetivos", target="/goals", params={})],
            created_at=now_iso,
        ))

    return insights
