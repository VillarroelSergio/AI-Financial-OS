"""INS-5: alertas de presupuesto. Reutiliza el cálculo existente de /api/budgets/comparison."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.budgets.routes import budget_comparison
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


def budget_alert_insights(db: Session, period: str) -> list[InsightOut]:
    """Un insight por presupuesto en aviso (consumo ≥ umbral) o superado (≥ 100%)."""
    items = budget_comparison(month=period, db=db)  # ya ordena por consumo desc
    now_iso = datetime.now(timezone.utc).isoformat()
    out: list[InsightOut] = []

    for it in items:
        if not it.alert:  # alert = consumo ≥ alert_threshold_pct del propio presupuesto
            continue
        over = it.over_budget
        severity = InsightSeverity.critical if over else InsightSeverity.warning
        if over:
            title = f"Presupuesto de {it.category_name} superado"
            summary = (
                f"Has gastado el {it.consumption_pct:.0f}% del presupuesto de {it.category_name}, "
                f"superándolo en {abs(it.remaining):.0f} €."
            )
        else:
            title = f"Presupuesto de {it.category_name} en aviso"
            summary = (
                f"Llevas el {it.consumption_pct:.0f}% del presupuesto de {it.category_name}; "
                f"te quedan {it.remaining:.0f} € para el resto del mes."
            )
        out.append(InsightOut(
            id=f"insight_{period}_budget_{it.budget_id}",
            type=InsightType.budget_alert,
            severity=severity,
            title=title,
            summary=summary,
            period=period,
            impact_area="spending",
            dedupe_key=f"budget_alert:{it.budget_id}:{period}",
            confidence=compute_confidence("complete"),
            priority=compute_priority(severity.value, "complete", 90.0 if over else 75.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Consumo", value=it.consumption_pct, unit="%", precision=0),
            secondary_metrics=[
                InsightMetricOut(label="Gastado", value=it.actual_amount, unit="EUR"),
                InsightMetricOut(label="Presupuesto", value=it.budget_amount, unit="EUR"),
            ],
            sources=[InsightSourceOut(type="budgets", label="Presupuestos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label=f"Ver gastos de {it.category_name}",
                                      target="/transactions", params={"category_id": it.category_id})],
            created_at=now_iso,
        ))
    return out
