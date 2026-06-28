from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.insights.constants import MARKET_DAILY_CHANGE_THRESHOLD
from app.modules.insights.schemas import (
    DataStatus, InsightActionOut, InsightMetricOut, InsightOut,
    InsightSeverity, InsightSourceOut, InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority

WATCHED_SYMBOLS = {"^IBEX", "^STOXX50E", "^GSPC", "^IXIC", "MSCIWORLD"}


def market_context_insights(db: Session, period: str) -> list[InsightOut]:
    try:
        from app.modules.market_intelligence.storage.repository import get_latest_quotes
        quotes = get_latest_quotes()
    except Exception:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    insights: list[InsightOut] = []

    relevant = [q for q in quotes if q.get("symbol") in WATCHED_SYMBOLS or q.get("catalog_item_id", "").upper() in WATCHED_SYMBOLS]
    if not relevant:
        return []

    big_movers = [q for q in relevant if abs(q.get("change_pct") or 0) >= float(MARKET_DAILY_CHANGE_THRESHOLD)]
    if not big_movers:
        return []

    for q in big_movers[:3]:
        symbol = q.get("symbol", "Índice")
        change = q.get("change_pct", 0)
        direction = "baja" if change < 0 else "sube"
        insights.append(InsightOut(
            id=f"insight_{period}_market_{symbol}",
            type=InsightType.market_context,
            severity=InsightSeverity.info,
            title=f"Movimiento relevante en {symbol}",
            summary=f"{symbol} {direction} un {abs(change):.1f}% hoy. Si tu cartera está expuesta a este mercado, parte de la variación puede venir del contexto general.",
            period=period,
            impact_area="mercado",
            confidence=compute_confidence("complete"),
            priority=compute_priority("info", "complete", 50.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Variación", value=round(change, 2), unit="%"),
            sources=[InsightSourceOut(type="market_quotes", label="Mercados", period=period, updated_at=q.get("observed_at"))],
            actions=[InsightActionOut(label="Ver mercados", target="/markets", params={})],
            created_at=now_iso,
        ))

    return insights
