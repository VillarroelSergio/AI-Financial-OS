from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.account import Account
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


def net_worth_change_insight(db: Session, period: str) -> list[InsightOut]:
    """Show current net worth. Month-over-month change not available without balance history snapshots."""
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
    now_iso = datetime.now(timezone.utc).isoformat()

    if not accounts:
        return []

    net_worth = sum(float(a.current_balance) for a in accounts)

    return [InsightOut(
        id=f"insight_{period}_net_worth",
        type=InsightType.net_worth_change,
        severity=InsightSeverity.info,
        title="Patrimonio neto actual",
        summary=f"Tu patrimonio neto consolidado es de {net_worth:.0f} €.",
        detail="El cambio mes a mes requiere histórico de saldos. Mantén las cuentas actualizadas para ver la evolución.",
        period=period,
        impact_area="patrimonio",
        confidence=compute_confidence("partial"),
        priority=compute_priority("info", "partial", 45.0),
        data_status=DataStatus.partial,
        primary_metric=InsightMetricOut(label="Patrimonio neto", value=round(net_worth, 2), unit="EUR"),
        secondary_metrics=[
            InsightMetricOut(label="Cuentas activas", value=float(len(accounts)), unit=""),
        ],
        sources=[InsightSourceOut(type="accounts", label="Cuentas", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver cuentas", target="/accounts", params={})],
        created_at=now_iso,
    )]
