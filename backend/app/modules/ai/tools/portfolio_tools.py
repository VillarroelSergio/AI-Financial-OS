"""Controlled portfolio/investment tools for the AI assistant."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.investment import Holding, InvestmentAsset
from app.modules.ai.tools.registry import ToolDefinition, tool_registry


async def _get_portfolio_summary(db: Session, **_: Any) -> dict[str, Any]:
    holdings = db.query(Holding).all()
    if not holdings:
        return {
            "status": "not_available",
            "message": "No holdings found",
            "total_value": 0.0,
            "quality_score": 1.0,
        }
    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    total = sum(float(h.market_value or h.quantity * h.average_price) for h in holdings)
    items = []
    for h in holdings:
        asset = assets.get(h.asset_id)
        mv = float(h.market_value or h.quantity * h.average_price)
        items.append({
            "name": asset.name if asset else h.asset_id,
            "ticker": asset.ticker if asset else None,
            "asset_type": asset.asset_type if asset else "unknown",
            "currency": h.current_price_currency or "EUR",
            "market_value": round(mv, 2),
            "weight": round(mv / total, 4) if total > 0 else 0.0,
        })
    items.sort(key=lambda x: x["market_value"], reverse=True)
    return {
        "total_value": round(total, 2),
        "currency": "EUR",
        "holdings_count": len(holdings),
        "holdings": items,
        "quality_score": 1.0,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sources": [{"type": "portfolio", "provider": "local_db"}],
    }


async def _get_asset_allocation(db: Session, **_: Any) -> dict[str, Any]:
    holdings = db.query(Holding).all()
    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    total = sum(float(h.market_value or h.quantity * h.average_price) for h in holdings)
    by_type: dict[str, float] = {}
    for h in holdings:
        asset = assets.get(h.asset_id)
        atype = asset.asset_type if asset else "unknown"
        mv = float(h.market_value or h.quantity * h.average_price)
        by_type[atype] = by_type.get(atype, 0.0) + mv
    allocation = [
        {"type": k, "value": round(v, 2), "weight": round(v / total, 4) if total > 0 else 0.0}
        for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True)
    ]
    return {
        "allocation": allocation,
        "total_value": round(total, 2),
        "currency": "EUR",
        "quality_score": 1.0,
        "sources": [{"type": "portfolio", "provider": "local_db"}],
    }


async def _get_currency_exposure(db: Session, **_: Any) -> dict[str, Any]:
    holdings = db.query(Holding).all()
    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    total = sum(float(h.market_value or h.quantity * h.average_price) for h in holdings)
    by_currency: dict[str, float] = {}
    for h in holdings:
        currency = h.current_price_currency or "EUR"
        mv = float(h.market_value or h.quantity * h.average_price)
        by_currency[currency] = by_currency.get(currency, 0.0) + mv
    exposure = [
        {"currency": k, "value": round(v, 2), "weight": round(v / total, 4) if total > 0 else 0.0}
        for k, v in sorted(by_currency.items(), key=lambda x: x[1], reverse=True)
    ]
    return {
        "currency_exposure": exposure,
        "total_value": round(total, 2),
        "quality_score": 1.0,
        "sources": [{"type": "portfolio", "provider": "local_db"}],
    }


async def _get_sector_exposure(db: Session, **_: Any) -> dict[str, Any]:
    holdings = db.query(Holding).all()
    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    total = sum(float(h.market_value or h.quantity * h.average_price) for h in holdings)
    by_sector: dict[str, float] = {}
    for h in holdings:
        asset = assets.get(h.asset_id)
        sector = (asset.sector if asset else None) or "Diversified/Other"
        mv = float(h.market_value or h.quantity * h.average_price)
        by_sector[sector] = by_sector.get(sector, 0.0) + mv
    exposure = [
        {"sector": k, "value": round(v, 2), "weight": round(v / total, 4) if total > 0 else 0.0}
        for k, v in sorted(by_sector.items(), key=lambda x: x[1], reverse=True)
    ]
    return {
        "sector_exposure": exposure,
        "total_value": round(total, 2),
        "quality_score": 1.0,
        "sources": [{"type": "portfolio", "provider": "local_db"}],
    }


# ── Registration ──────────────────────────────────────────────────────────────

tool_registry.register(ToolDefinition(
    name="get_portfolio_summary",
    description="Returns a summary of the investment portfolio: total value, holdings list and weights.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_portfolio_summary,
))

tool_registry.register(ToolDefinition(
    name="get_asset_allocation",
    description="Returns portfolio allocation by asset type (ETF, stock, bond, savings account, etc.).",
    input_schema={"type": "object", "properties": {}},
    handler=_get_asset_allocation,
))

tool_registry.register(ToolDefinition(
    name="get_currency_exposure",
    description="Returns portfolio exposure by currency (EUR, USD, GBP, etc.).",
    input_schema={"type": "object", "properties": {}},
    handler=_get_currency_exposure,
))

tool_registry.register(ToolDefinition(
    name="get_sector_exposure",
    description="Returns portfolio exposure by economic sector.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_sector_exposure,
))
