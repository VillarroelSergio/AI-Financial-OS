"""Controlled market and macro intelligence tools for the AI assistant."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.economic_data import service as econ_service
from app.modules.economic_data import repository as econ_repo


async def _get_macro_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = econ_service.get_snapshot()
        regions: dict[str, Any] = {}
        for region_name in ("spain", "eurozone", "us"):
            region = getattr(snapshot, region_name, None)
            if region:
                regions[region_name] = {
                    "region": region.region,
                    "indicators": [
                        {
                            "name": ind.name,
                            "indicator": ind.indicator,
                            "value": ind.value,
                            "unit": ind.unit,
                            "period": ind.period,
                            "change": ind.change,
                            "source": ind.source,
                            "is_stale": ind.is_stale,
                        }
                        for ind in (region.indicators or [])
                    ],
                }
        return {
            "regions": regions,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.9,
            "sources": [{"type": "macro_indicators", "provider": "FRED/Stooq"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_personal_impact(db: Session, **_: Any) -> dict[str, Any]:
    try:
        impact_obj = econ_service.get_personal_impact(db=db)
        items = []
        for cat, item in {
            "inflation_vs_savings": impact_obj.inflation_vs_savings,
            "rates_vs_liquidity": impact_obj.rates_vs_liquidity,
            "market_vs_portfolio": impact_obj.market_vs_portfolio,
            "purchasing_power": impact_obj.purchasing_power,
        }.items():
            items.append({
                "category": cat,
                "title": getattr(item, "title", ""),
                "impact_level": getattr(item, "impact_level", ""),
                "summary": getattr(item, "summary", ""),
                "recommendation": getattr(item, "recommendation", ""),
            })
        return {
            "impacts": items,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.85,
            "sources": [{"type": "personal_impact", "provider": "local_analysis"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_financial_signals(db: Session, **_: Any) -> dict[str, Any]:
    """Aggregated financial signals derived from economic data."""
    try:
        indicators = econ_repo.get_all_latest()
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
