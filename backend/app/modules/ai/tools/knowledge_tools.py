"""Financial knowledge layer tools - AI datasheet and market regime."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.envelope import as_dict, fail, ok, source
from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.financial_knowledge import service as knowledge_service


async def _get_market_regime(db: Session, **_: Any) -> dict[str, Any]:
    try:
        regime = knowledge_service.get_regime()
        if regime is None:
            return fail("get_market_regime", "market regime not available")
        data = as_dict(regime)
        sources = [source(
            source_type="market_regime",
            provider="financial_knowledge",
            source_id=data.get("id"),
            observed_at=data.get("computed_at"),
            quality_score=data.get("confidence_score"),
            model_type=data.get("regime_type"),
        )]
        return ok("get_market_regime", data, sources=sources, quality_score=data.get("confidence_score"))
    except Exception as exc:
        return fail("get_market_regime", "market regime not available", str(exc))


async def _get_ai_datasheet(db: Session, **_: Any) -> dict[str, Any]:
    try:
        datasheet = knowledge_service.get_ai_datasheet()
        if datasheet is None:
            return fail("get_ai_datasheet", "AI datasheet not available")
        data = as_dict(datasheet)
        sources = [
            source(
                source_type="ai_datasheet",
                provider="financial_knowledge",
                observed_at=data.get("generated_at"),
                quality_score=data.get("quality_score"),
                model_type="daily",
            )
        ]
        for source_id in data.get("sources", []):
            sources.append(source(source_type="knowledge_source", provider="financial_knowledge", source_id=str(source_id)))
        return ok(
            "get_ai_datasheet",
            data,
            sources=sources,
            quality_score=data.get("quality_score"),
            warnings=data.get("warnings", []),
        )
    except Exception as exc:
        return fail("get_ai_datasheet", "AI datasheet not available", str(exc))


tool_registry.register(ToolDefinition(
    name="get_market_regime",
    description="Returns the computed market regime from the Financial Knowledge layer.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_market_regime,
    source_type="financial_knowledge",
))

tool_registry.register(ToolDefinition(
    name="get_ai_datasheet",
    description="Returns a comprehensive context datasheet combining market regime, macro insights, signals, impacts and sources.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_ai_datasheet,
    source_type="financial_knowledge",
))
