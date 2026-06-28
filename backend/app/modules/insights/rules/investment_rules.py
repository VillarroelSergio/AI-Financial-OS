from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.investment import Holding, InvestmentAsset
from app.modules.insights.constants import HIGH_CONCENTRATION_THRESHOLD
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority


def investment_allocation_insight(db: Session, period: str) -> list[InsightOut]:
    holdings = db.query(Holding).all()
    now_iso = datetime.now(timezone.utc).isoformat()

    if not holdings:
        return [InsightOut(
            id=f"insight_{period}_investment_empty",
            type=InsightType.investment_allocation,
            severity=InsightSeverity.info,
            title="Sin posiciones de inversión registradas",
            summary="No hay posiciones de inversión para analizar.",
            period=period,
            impact_area="inversiones",
            confidence=compute_confidence("empty"),
            priority=compute_priority("info", "empty", 30.0),
            data_status=DataStatus.empty,
            sources=[InsightSourceOut(type="investments", label="Inversiones", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver inversiones", target="/investments", params={})],
            created_at=now_iso,
        )]

    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    insights: list[InsightOut] = []

    missing_price = [h for h in holdings if h.current_price is None]
    if missing_price:
        insights.append(InsightOut(
            id=f"insight_{period}_investment_missing_prices",
            type=InsightType.investment_allocation,
            severity=InsightSeverity.info,
            title="Posiciones sin precio actualizado",
            summary=f"{len(missing_price)} posición(es) no tienen precio actualizado. Puedes actualizarlos manualmente.",
            period=period,
            impact_area="inversiones",
            confidence=compute_confidence("partial"),
            priority=compute_priority("info", "partial", 45.0),
            data_status=DataStatus.partial,
            primary_metric=InsightMetricOut(label="Sin precio", value=float(len(missing_price)), unit="posiciones"),
            sources=[InsightSourceOut(type="investments", label="Inversiones", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver inversiones", target="/investments", params={})],
            created_at=now_iso,
        ))

    values: list[tuple[str, Decimal]] = []
    for h in holdings:
        mv = h.market_value or (h.quantity * (h.current_price or h.average_price))
        asset = assets.get(h.asset_id)
        name = asset.name if asset else "Activo desconocido"
        values.append((name, mv if mv > 0 else Decimal("0")))

    total = sum(v for _, v in values)
    if total > 0:
        for name, val in values:
            pct = val / total * 100
            if pct > HIGH_CONCENTRATION_THRESHOLD:
                insights.append(InsightOut(
                    id=f"insight_{period}_investment_concentration_{name[:20]}",
                    type=InsightType.investment_allocation,
                    severity=InsightSeverity.info,
                    title="Concentración elevada en un activo",
                    summary=f"{name} representa el {float(pct):.0f}% de tu cartera. Puedes revisar la distribución antes de tomar nuevas decisiones.",
                    period=period,
                    impact_area="inversiones",
                    confidence=compute_confidence("complete"),
                    priority=compute_priority("info", "complete", 50.0),
                    data_status=DataStatus.complete,
                    primary_metric=InsightMetricOut(label="Concentración", value=round(float(pct), 1), unit="%"),
                    sources=[InsightSourceOut(type="investments", label="Inversiones", period=period, updated_at=now_iso)],
                    actions=[InsightActionOut(label="Ver inversiones", target="/investments", params={})],
                    created_at=now_iso,
                ))

    return insights
