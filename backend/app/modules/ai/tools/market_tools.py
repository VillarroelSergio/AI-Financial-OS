"""Controlled market and macro intelligence tools for the AI assistant."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.market_intelligence.api import service as mi_service
from app.modules.market_intelligence.api.impact import compute_personal_impact


async def _get_macro_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = mi_service.get_macro_snapshot()
        regions: dict[str, Any] = {
            "spain": {"region": "spain", "indicators": [point.model_dump() for point in snapshot.spain]},
            "eurozone": {"region": "eurozone", "indicators": [point.model_dump() for point in snapshot.eurozone]},
            "usa": {"region": "usa", "indicators": [point.model_dump() for point in snapshot.usa]},
        }
        return {
            "regions": regions,
            "observed_at": snapshot.generated_at,
            "warnings": snapshot.warnings,
            "quality_score": 0.9,
            "sources": [{"type": "macro_indicators", "provider": "market_intelligence"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_personal_impact(db: Session, **_: Any) -> dict[str, Any]:
    try:
        impact_obj = compute_personal_impact(db=db)
        items = [item.model_dump() for item in impact_obj.comparatives]
        return {
            "impacts": items,
            "observed_at": impact_obj.generated_at,
            "warnings": impact_obj.warnings,
            "quality_score": 0.85,
            "sources": [{"type": "personal_impact", "provider": "market_intelligence"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_financial_signals(db: Session, **_: Any) -> dict[str, Any]:
    """Aggregated financial signals derived from economic data."""
    try:
        snapshot = mi_service.get_macro_snapshot()
        indicators = [
            *[point.model_dump() | {"region": "spain", "indicator": point.indicator_id} for point in snapshot.spain],
            *[point.model_dump() | {"region": "eurozone", "indicator": point.indicator_id} for point in snapshot.eurozone],
            *[point.model_dump() | {"region": "usa", "indicator": point.indicator_id} for point in snapshot.usa],
        ]
        signals = []
        for row in indicators:
            value = row.get("value")
            indicator = row.get("indicator", "")
            region = row.get("region", "")
            if value is None:
                continue
            signal_type = "neutral"
            if indicator == "inflation":
                if value > 4.0:
                    signal_type = "warning"
                elif value < 1.0:
                    signal_type = "caution"
                else:
                    signal_type = "normal"
            elif indicator == "unemployment":
                if value > 10.0:
                    signal_type = "warning"
                elif value < 5.0:
                    signal_type = "positive"
            signals.append({
                "indicator": indicator,
                "region": region,
                "value": value,
                "signal": signal_type,
                "period": row.get("period", ""),
                "source": row.get("source", ""),
            })
        return {
            "signals": signals,
            "count": len(signals),
            "quality_score": 0.85,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "sources": [{"type": "financial_signals", "provider": "local_analysis"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


# ── Registration ──────────────────────────────────────────────────────────────

tool_registry.register(ToolDefinition(
    name="get_macro_snapshot",
    description="Returns current macroeconomic indicators for ES, EA and US: inflation, unemployment, GDP, interest rates.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_macro_snapshot,
    source_type="economic_data",
))

tool_registry.register(ToolDefinition(
    name="get_personal_impact_summary",
    description="Returns how current macro indicators personally impact the user's finances.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_personal_impact,
    source_type="economic_data",
))

tool_registry.register(ToolDefinition(
    name="get_financial_signals",
    description="Returns categorized financial signals (normal/warning/caution/positive) derived from macro indicators.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_financial_signals,
    source_type="economic_data",
))
