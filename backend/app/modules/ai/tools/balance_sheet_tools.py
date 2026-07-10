"""AI tool: get_balance_sheet — read-only wrapper over the deterministic net_worth balance sheet (INS-8)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.net_worth import service as net_worth_service


async def _get_balance_sheet(
    db: Session,
    month: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    if month and (len(month) != 7 or "-" not in month):
        return {"error": "month must be YYYY-MM", "status": "error"}
    result = net_worth_service.build_balance_sheet(
        db, month or datetime.now(timezone.utc).strftime("%Y-%m")
    )
    # ponytail: balance sheet is computed deterministically upstream; we only serialize it.
    return {
        **result.model_dump(mode="json"),
        "sources": [{"type": "net_worth_engine", "provider": "local_deterministic"}],
        "quality_score": 1.0,
    }


tool_registry.register(ToolDefinition(
    name="get_balance_sheet",
    description=(
        "Returns the deterministic balance sheet (assets, liabilities, net worth) for a given month. "
        "Use this when the user asks about their patrimonio, net worth, balance, assets or liabilities. "
        "Values are computed from real local data — EXPLAIN and CONTEXTUALIZE them, but do NOT recalculate, "
        "modify or invent figures; always cite the same amounts returned here."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "Month in YYYY-MM format. Defaults to current month.",
            },
        },
    },
    handler=_get_balance_sheet,
))
