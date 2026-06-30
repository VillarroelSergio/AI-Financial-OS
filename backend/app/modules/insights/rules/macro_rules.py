from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority

INFLATION_WARNING_THRESHOLD = 3.0
HIGH_RATE_THRESHOLD = 3.0
INFLATION_IDS = {"esp_cpi_yoy", "ea_cpi_yoy", "usa_cpi_yoy", "esp_cpi", "ea_cpi"}
RATE_IDS = {"ecb_rate", "fed_rate", "euribor_12m", "euribor_3m"}


def macro_context_insights(db: Session, period: str) -> list[InsightOut]:
    try:
        from app.modules.market_intelligence.storage.repository import get_latest_macro_all
        macro_data = get_latest_macro_all()
    except Exception:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    insights: list[InsightOut] = []

    for item in macro_data:
        cat_id = item.get("catalog_item_id", "")
        value = item.get("value")
        if value is None:
            continue
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            continue
        if cat_id in INFLATION_IDS and val_float >= INFLATION_WARNING_THRESHOLD:
            insights.append(InsightOut(
                id=f"insight_{period}_macro_inflation_{cat_id}",
                type=InsightType.macro_context,
                severity=InsightSeverity.info,
                title="La inflación puede afectar a tus objetivos",
                summary=f"La inflación ({cat_id.upper()}) está en {val_float:.1f}%. Puedes revisar si tus objetivos nominales mantienen poder adquisitivo real.",
                period=period,
                impact_area="macro",
                confidence=compute_confidence("complete"),
                priority=compute_priority("info", "complete", 50.0),
                data_status=DataStatus.complete,
                primary_metric=InsightMetricOut(label="Inflación", value=val_float, unit="%"),
                sources=[InsightSourceOut(type="macro", label="Datos macro", period=item.get("period"), updated_at=item.get("retrieved_at"))],
                actions=[InsightActionOut(label="Ver economía", target="/economy", params={})],
                created_at=now_iso,
            ))
            break

    for item in macro_data:
        cat_id = item.get("catalog_item_id", "")
        value = item.get("value")
        if value is None:
            continue
        if cat_id in RATE_IDS:
            try:
                val_float = float(value)
            except (ValueError, TypeError):
                continue
            if val_float >= HIGH_RATE_THRESHOLD:
                insights.append(InsightOut(
                    id=f"insight_{period}_macro_rates_{cat_id}",
                    type=InsightType.macro_context,
                    severity=InsightSeverity.info,
                    title="Tipos de interés elevados",
                    summary=f"{cat_id.upper()} está en {val_float:.2f}%. Puede ser relevante si tienes deuda variable o productos de renta fija.",
                    period=period,
                    impact_area="macro",
                    confidence=compute_confidence("complete"),
                    priority=compute_priority("info", "complete", 45.0),
                    data_status=DataStatus.complete,
                    primary_metric=InsightMetricOut(label="Tipo", value=val_float, unit="%"),
                    sources=[InsightSourceOut(type="macro", label="Datos macro", period=item.get("period"), updated_at=item.get("retrieved_at"))],
                    actions=[InsightActionOut(label="Ver economía", target="/economy", params={})],
                    created_at=now_iso,
                ))
                break

    return insights[:3]
