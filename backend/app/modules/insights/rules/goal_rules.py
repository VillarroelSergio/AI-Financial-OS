from __future__ import annotations
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.goal import Goal
from app.modules.insights.constants import GOAL_LAG_THRESHOLD_PERCENTAGE_POINTS
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority


def goal_progress_insights(db: Session, period: str) -> list[InsightOut]:
    goals = db.query(Goal).filter(Goal.status == "active").all()
    if not goals:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    today = date.today()
    insights: list[InsightOut] = []

    for g in goals:
        target = float(g.target_amount)
        current = float(g.current_amount or Decimal("0"))
        if target <= 0:
            continue

        actual_progress = current / target * 100
        data_status = DataStatus.complete

        if actual_progress >= 100:
            insights.append(InsightOut(
                id=f"insight_{period}_goal_{g.id}_completed",
                type=InsightType.goal_progress,
                severity=InsightSeverity.positive,
                title=f"Objetivo completado: {g.name}",
                summary=f"Has alcanzado el objetivo '{g.name}'. ¡Enhorabuena!",
                period=period,
                impact_area="objetivos",
                confidence=compute_confidence("complete"),
                priority=compute_priority("positive", "complete", 70.0),
                data_status=data_status,
                primary_metric=InsightMetricOut(label="Progreso", value=round(actual_progress, 1), unit="%"),
                sources=[InsightSourceOut(type="goals", label="Objetivos", period=period, updated_at=now_iso)],
                actions=[InsightActionOut(label="Ver objetivos", target="/goals", params={})],
                created_at=now_iso,
            ))
            continue

        if g.target_date:
            created = g.created_at.date() if hasattr(g.created_at, 'date') else today
            total_days = (g.target_date - created).days
            elapsed_days = (today - created).days
            if total_days > 0:
                expected_progress = min(100.0, elapsed_days / total_days * 100)
                lag = expected_progress - actual_progress
                if lag > float(GOAL_LAG_THRESHOLD_PERCENTAGE_POINTS):
                    insights.append(InsightOut(
                        id=f"insight_{period}_goal_{g.id}_behind",
                        type=InsightType.goal_progress,
                        severity=InsightSeverity.warning,
                        title=f"Objetivo '{g.name}' por debajo del ritmo previsto",
                        summary=f"Tu objetivo '{g.name}' está un {lag:.0f}% por debajo del ritmo esperado para la fecha objetivo.",
                        detail=f"Progreso actual: {actual_progress:.1f}%. Progreso esperado: {expected_progress:.1f}%.",
                        period=period,
                        impact_area="objetivos",
                        confidence=compute_confidence("complete"),
                        priority=compute_priority("warning", "complete", 60.0),
                        data_status=data_status,
                        primary_metric=InsightMetricOut(label="Progreso actual", value=round(actual_progress, 1), unit="%"),
                        secondary_metrics=[InsightMetricOut(label="Progreso esperado", value=round(expected_progress, 1), unit="%")],
                        sources=[InsightSourceOut(type="goals", label="Objetivos", period=period, updated_at=now_iso)],
                        actions=[InsightActionOut(label="Ver objetivos", target="/goals", params={})],
                        created_at=now_iso,
                    ))
                    continue

        insights.append(InsightOut(
            id=f"insight_{period}_goal_{g.id}_progress",
            type=InsightType.goal_progress,
            severity=InsightSeverity.info,
            title=f"Progreso en objetivo: {g.name}",
            summary=f"Llevas un {actual_progress:.1f}% del objetivo '{g.name}'.",
            period=period,
            impact_area="objetivos",
            confidence=compute_confidence("complete"),
            priority=compute_priority("info", "complete", 45.0),
            data_status=data_status,
            primary_metric=InsightMetricOut(label="Progreso", value=round(actual_progress, 1), unit="%"),
            secondary_metrics=[InsightMetricOut(label="Cantidad actual", value=current, unit="EUR"), InsightMetricOut(label="Objetivo", value=target, unit="EUR")],
            sources=[InsightSourceOut(type="goals", label="Objetivos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver objetivos", target="/goals", params={})],
            created_at=now_iso,
        ))

    return insights
