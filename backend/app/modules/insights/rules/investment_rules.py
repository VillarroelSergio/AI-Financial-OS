from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.investment import FundValuationSnapshot, Holding, InvestmentAsset

# Un fondo cuya última valoración manual supera este umbral se considera desactualizado.
FUND_STALE_DAYS = 90
from app.modules.insights.constants import HIGH_CONCENTRATION_THRESHOLD
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


def fund_stale_valuation_insight(db: Session, period: str) -> list[InsightOut]:
    """Fondos cuya última valoración manual está desactualizada (INV-3).

    Anima a usar 'Actualizar valor' para que los KPIs reflejen el valor real."""
    now_iso = datetime.now(timezone.utc).isoformat()
    today = date.today()
    funds = (
        db.query(Holding, InvestmentAsset)
        .join(InvestmentAsset, InvestmentAsset.id == Holding.asset_id)
        .filter(InvestmentAsset.asset_type == "fund")
        .all()
    )
    insights: list[InsightOut] = []
    for holding, asset in funds:
        latest = (
            db.query(FundValuationSnapshot)
            .filter(FundValuationSnapshot.holding_id == holding.id)
            .order_by(FundValuationSnapshot.as_of_date.desc())
            .first()
        )
        age_days = (today - latest.as_of_date).days if latest else None
        if latest is not None and age_days < FUND_STALE_DAYS:
            continue  # valoración reciente: nada que avisar

        if latest is None:
            summary = f"{asset.name} no tiene ninguna valoración registrada. Usa 'Actualizar valor' para reflejar su valor real."
            metric = InsightMetricOut(label="Sin valoración", value=0.0, unit="días")
        else:
            summary = f"La última valoración de {asset.name} tiene {age_days} días. Actualiza su valor para KPIs precisos."
            metric = InsightMetricOut(label="Antigüedad", value=float(age_days), unit="días")

        insights.append(InsightOut(
            id=f"insight_{period}_fund_stale_{holding.id[:8]}",
            type=InsightType.investment_allocation,
            severity=InsightSeverity.warning,
            title="Fondo con valoración desactualizada",
            summary=summary,
            period=period,
            impact_area="inversiones",
            confidence=compute_confidence("partial"),
            priority=compute_priority("warning", "partial", 55.0),
            data_status=DataStatus.partial,
            primary_metric=metric,
            sources=[InsightSourceOut(type="investments", label="Inversiones", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Actualizar valor", target="/investments", params={"holding_id": holding.id})],
            created_at=now_iso,
        ))
    return insights
