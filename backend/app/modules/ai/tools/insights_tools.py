"""AI tool: get_insights_summary — wraps deterministic InsightsEngine."""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.insights import service as insights_service


async def _get_insights_summary(
    db: Session,
    period: str | None = None,
    limit: int = 5,
    type: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    if period and (len(period) != 7 or "-" not in period):
        return {"error": "period must be YYYY-MM", "status": "error"}
    limit = max(1, min(limit, 10))
    result = insights_service.get_insights(
        db=db,
        period=period,
        type_filter=type,
        limit=limit,
    )
    return {
        "period": result.period,
        "generated_at": result.generated_at,
        "data_status": result.data_status.value,
        "insights": [
            {
                "id": i.id,
                "type": i.type.value,
                "severity": i.severity.value,
                "title": i.title,
                "summary": i.summary,
                "impact_area": i.impact_area,
                "priority": i.priority,
                "primary_metric": i.primary_metric.model_dump() if i.primary_metric else None,
                "sources": [s.model_dump() for s in i.sources],
                "actions": [a.model_dump() for a in i.actions],
            }
            for i in result.insights
        ],
        "summary": result.summary.model_dump(),
        "sources": [{"type": "insights_engine", "provider": "local_deterministic"}],
        "quality_score": 1.0,
    }


tool_registry.register(ToolDefinition(
    name="get_insights_summary",
    description=(
        "Returns prioritized financial insights for a given month. "
        "Use this when the user asks about alerts, warnings, monthly review, "
        "things to review, financial recommendations, or insights. "
        "Insights are computed deterministically from real local data — do NOT invent or modify them."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "description": "Month in YYYY-MM format. Defaults to current month.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of insights to return (1-10). Default 5.",
                "default": 5,
            },
            "type": {
                "type": "string",
                "description": "Optional filter: spending_anomaly | monthly_comparison | savings_rate | cashflow_alert | net_worth_change | investment_allocation | goal_progress | market_context | macro_context | data_quality",
            },
        },
    },
    handler=_get_insights_summary,
))
