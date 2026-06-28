"""Controlled market and macro intelligence tools for the AI assistant."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.ai.tools.envelope import as_dict, fail, ok, source
from app.modules.ai.tools.registry import ToolDefinition, tool_registry
from app.modules.financial_knowledge import service as knowledge_service
from app.modules.market_intelligence.api import service as market_service


def _sources_from_items(items: list[dict[str, Any]], source_type: str, observed_key: str = "period") -> list[dict[str, Any]]:
    sources = []
    for item in items:
        sources.append(source(
            source_type=source_type,
            provider=item.get("provider_id") or item.get("source_provider"),
            catalog_item_id=item.get("catalog_item_id"),
            observed_at=str(item.get(observed_key)) if item.get(observed_key) is not None else None,
            quality_score=item.get("quality_score"),
        ))
    return sources


async def _get_macro_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = as_dict(market_service.get_macro_snapshot())
        items = snapshot.get("spain", []) + snapshot.get("eurozone", []) + snapshot.get("usa", [])
        return ok(
            "get_macro_snapshot",
            snapshot,
            sources=_sources_from_items(items, "market_indicator"),
            warnings=snapshot.get("warnings", []),
        )
    except Exception as exc:
        return fail("get_macro_snapshot", "macro snapshot not available", str(exc))


async def _get_market_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = as_dict(market_service.get_market_snapshot())
        items = snapshot.get("indices", []) + snapshot.get("crypto", []) + snapshot.get("commodities", [])
        return ok(
            "get_market_snapshot",
            snapshot,
            sources=_sources_from_items(items, "market_quote", observed_key="catalog_item_id"),
            warnings=snapshot.get("warnings", []),
        )
    except Exception as exc:
        return fail("get_market_snapshot", "market snapshot not available", str(exc))


async def _get_forex_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = as_dict(market_service.get_forex_snapshot())
        return ok(
            "get_forex_snapshot",
            snapshot,
            sources=_sources_from_items(snapshot.get("rates", []), "forex_rate", observed_key="date"),
            warnings=snapshot.get("warnings", []),
        )
    except Exception as exc:
        return fail("get_forex_snapshot", "forex snapshot not available", str(exc))


async def _get_bond_snapshot(db: Session, **_: Any) -> dict[str, Any]:
    try:
        snapshot = as_dict(market_service.get_bond_snapshot())
        return ok(
            "get_bond_snapshot",
            snapshot,
            sources=_sources_from_items(snapshot.get("yields", []), "bond_yield", observed_key="date"),
            warnings=snapshot.get("warnings", []),
        )
    except Exception as exc:
        return fail("get_bond_snapshot", "bond snapshot not available", str(exc))


async def _get_provider_quality(db: Session, **_: Any) -> dict[str, Any]:
    try:
        macro = as_dict(market_service.get_macro_snapshot())
        market = as_dict(market_service.get_market_snapshot())
        forex = as_dict(market_service.get_forex_snapshot())
        bonds = as_dict(market_service.get_bond_snapshot())
        items = (
            macro.get("spain", []) + macro.get("eurozone", []) + macro.get("usa", [])
            + market.get("indices", []) + market.get("crypto", [])
            + forex.get("rates", []) + bonds.get("yields", [])
        )
        by_provider: dict[str, dict[str, Any]] = {}
        for item in items:
            provider = item.get("provider_id") or "unknown"
            bucket = by_provider.setdefault(provider, {"provider": provider, "items": 0, "quality_total": 0.0})
            bucket["items"] += 1
            bucket["quality_total"] += float(item.get("quality_score", 1.0))
        providers = [
            {"provider": row["provider"], "items": row["items"], "quality_score": round(row["quality_total"] / row["items"], 3)}
            for row in by_provider.values()
            if row["items"] > 0
        ]
        sources = [
            source(source_type="provider_quality", provider=p["provider"], quality_score=p["quality_score"])
            for p in providers
        ]
        return ok("get_provider_quality", {"providers": providers}, sources=sources)
    except Exception as exc:
        return fail("get_provider_quality", "provider quality not available", str(exc))


async def _get_personal_impact(db: Session, **_: Any) -> dict[str, Any]:
    try:
        impacts = [as_dict(item) for item in knowledge_service.get_personal_impacts()]
        if not impacts:
            return ok(
                "get_personal_impact_summary",
                {"impacts": []},
                quality_score=0,
                warnings=["No personal impact data available in Financial Knowledge."],
            )
        sources = [
            source(
                source_type="personal_impact",
                provider="financial_knowledge",
                source_id=item.get("id"),
                observed_at=item.get("computed_at"),
                quality_score=item.get("confidence_score"),
                model_type=item.get("impact_type"),
            )
            for item in impacts
        ]
        return ok("get_personal_impact_summary", {"impacts": impacts}, sources=sources)
    except Exception as exc:
        return fail("get_personal_impact_summary", "personal impact summary not available", str(exc))


async def _get_financial_signals(db: Session, **_: Any) -> dict[str, Any]:
    try:
        signals = [as_dict(item) for item in knowledge_service.get_signals()]
        if not signals:
            return ok(
                "get_financial_signals",
                {"signals": [], "count": 0},
                quality_score=0,
                warnings=["No financial signals available in Financial Knowledge."],
            )
        sources = [
            source(
                source_type="financial_signal",
                provider="financial_knowledge",
                source_id=item.get("id"),
                observed_at=item.get("computed_at"),
                quality_score=item.get("quality_score"),
                model_type=item.get("signal_type"),
            )
            for item in signals
        ]
        return ok("get_financial_signals", {"signals": signals, "count": len(signals)}, sources=sources)
    except Exception as exc:
        return fail("get_financial_signals", "financial signals not available", str(exc))


tool_registry.register(ToolDefinition(
    name="get_market_snapshot",
    description="Returns current market quotes for tracked indices, crypto and commodities from Market Intelligence.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_market_snapshot,
    source_type="market_intelligence",
))

tool_registry.register(ToolDefinition(
    name="get_macro_snapshot",
    description="Returns current macroeconomic indicators for ES, EA and US: inflation, unemployment, GDP, interest rates.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_macro_snapshot,
    source_type="market_intelligence",
))

tool_registry.register(ToolDefinition(
    name="get_forex_snapshot",
    description="Returns current tracked FX rates from Market Intelligence.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_forex_snapshot,
    source_type="market_intelligence",
))

tool_registry.register(ToolDefinition(
    name="get_bond_snapshot",
    description="Returns current tracked sovereign bond yields from Market Intelligence.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_bond_snapshot,
    source_type="market_intelligence",
))

tool_registry.register(ToolDefinition(
    name="get_provider_quality",
    description="Returns provider-level data quality from the latest Market Intelligence snapshots.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_provider_quality,
    source_type="market_intelligence",
))

tool_registry.register(ToolDefinition(
    name="get_personal_impact_summary",
    description="Returns how current macro indicators personally impact the user's finances.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_personal_impact,
    source_type="financial_knowledge",
))

tool_registry.register(ToolDefinition(
    name="get_financial_signals",
    description="Returns categorized financial signals derived from the Financial Knowledge layer.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_financial_signals,
    source_type="financial_knowledge",
))
