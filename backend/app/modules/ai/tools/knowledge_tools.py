"""Financial knowledge layer tools — AI Datasheet and market regime."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.market_intelligence.api import service as mi_service
from app.modules.market_intelligence.api.impact import compute_personal_impact


def _compute_market_regime(indicators: list[dict]) -> dict[str, Any]:
    """Heuristic regime from macro indicators."""
    inflation_vals = [r["value"] for r in indicators if r.get("indicator") == "inflation" and r.get("value") is not None]
    unemployment_vals = [r["value"] for r in indicators if r.get("indicator") == "unemployment" and r.get("value") is not None]
    gdp_vals = [r["value"] for r in indicators if r.get("indicator") == "gdp" and r.get("value") is not None]

    avg_inflation = sum(inflation_vals) / len(inflation_vals) if inflation_vals else None
    avg_unemployment = sum(unemployment_vals) / len(unemployment_vals) if unemployment_vals else None
    avg_gdp = sum(gdp_vals) / len(gdp_vals) if gdp_vals else None

    regime = "unknown"
    description = "Insufficient data to determine market regime."

    if avg_inflation is not None and avg_gdp is not None:
        if avg_inflation > 5.0 and avg_gdp < 1.0:
            regime = "stagflation"
            description = "High inflation combined with low growth. Challenging environment for fixed income and consumer spending."
        elif avg_inflation > 4.0:
            regime = "high_inflation"
            description = "Above-target inflation. Central banks likely tightening. Pressure on bonds and leveraged assets."
        elif avg_inflation < 1.5 and avg_gdp < 0.5:
            regime = "deflation_risk"
            description = "Low inflation with weak growth. Risk of deflation. Central banks likely easing."
        elif avg_gdp > 2.5 and avg_inflation < 3.0:
            regime = "goldilocks"
            description = "Strong growth with controlled inflation. Favorable for equities and risk assets."
        elif avg_gdp > 1.0:
            regime = "moderate_growth"
            description = "Moderate growth environment. Mixed signals — balanced portfolio approach recommended."
        else:
            regime = "slowdown"
            description = "Economic slowdown. Defensive positioning may be appropriate."

    return {
        "regime": regime,
        "description": description,
        "inputs": {
            "avg_inflation": round(avg_inflation, 2) if avg_inflation is not None else None,
            "avg_unemployment": round(avg_unemployment, 2) if avg_unemployment is not None else None,
            "avg_gdp": round(avg_gdp, 2) if avg_gdp is not None else None,
        },
    }


async def _get_market_regime(db: Session, **_: Any) -> dict[str, Any]:
    try:
        indicators = _latest_macro_points()
        regime_data = _compute_market_regime(indicators)
        return {
            **regime_data,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.75,
            "warnings": ["Regime is computed heuristically from macro data. Not investment advice."],
            "sources": [{"type": "market_regime", "provider": "local_analysis"}],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_ai_datasheet(db: Session, **_: Any) -> dict[str, Any]:
    """Comprehensive context datasheet for the AI assistant."""
    try:
        # Macro snapshot
        macro_result = await _get_macro_snapshot_simple()
        # Regime
        indicators = _latest_macro_points()
        regime = _compute_market_regime(indicators)
        # Personal impacts
        try:
            impact_obj = compute_personal_impact(db=db)
            impact_items = [item.model_dump() for item in impact_obj.comparatives]
        except Exception:
            impact_items = []

        return {
            "datasheet_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "market_regime": regime,
            "macro_insights": macro_result,
            "personal_impacts": impact_items,
            "quality_score": 0.85,
            "warnings": [
                "This datasheet is derived from publicly available macro data.",
                "Not investment advice. Data may be delayed.",
            ],
            "sources": [
                {"type": "macro_indicators", "provider": "FRED/Stooq"},
                {"type": "local_analysis", "provider": "internal"},
            ],
        }
    except Exception as exc:
        return {"status": "not_available", "error": str(exc), "quality_score": 0.0}


async def _get_macro_snapshot_simple() -> dict[str, Any]:
    try:
        indicators = _latest_macro_points()
        by_region: dict[str, list] = {}
        for row in indicators:
            region = row.get("region", "")
            if region not in by_region:
                by_region[region] = []
            by_region[region].append({
                "indicator": row.get("indicator"),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "period": row.get("period"),
            })
        return by_region
    except Exception:
        return {}


def _latest_macro_points() -> list[dict[str, Any]]:
    snapshot = mi_service.get_macro_snapshot()
    return [
        *[point.model_dump() | {"region": "spain", "indicator": point.indicator_id} for point in snapshot.spain],
        *[point.model_dump() | {"region": "eurozone", "indicator": point.indicator_id} for point in snapshot.eurozone],
        *[point.model_dump() | {"region": "usa", "indicator": point.indicator_id} for point in snapshot.usa],
    ]


# ── Registration ──────────────────────────────────────────────────────────────

tool_registry.register(ToolDefinition(
    name="get_market_regime",
    description="Returns the computed market regime (goldilocks, high_inflation, stagflation, slowdown, etc.) from macro data.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_market_regime,
    source_type="knowledge",
))

tool_registry.register(ToolDefinition(
    name="get_ai_datasheet",
    description="Returns a comprehensive context datasheet combining market regime, macro insights, and personal impacts. Use this before answering complex financial questions.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_ai_datasheet,
    source_type="knowledge",
))
