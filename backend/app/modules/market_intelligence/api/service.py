"""Market Intelligence API service — lee desde DuckDB, nunca llama providers."""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut, BondSnapshotOut, BondYieldOut, ForexRateOut, ForexSnapshotOut,
    MacroDataPoint, MacroSnapshotOut, MarketSnapshotOut, NewsItemOut, NewsSnapshotOut,
    QuoteOut,
)
from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.api")

_catalog = CatalogLoader()
_INDEX_CATALOG_IDS = {
    "sp500", "nasdaq", "nasdaq100", "dow_jones", "russell_2000",
    "ibex35", "eurostoxx50", "dax", "cac40", "ftse100", "nikkei225",
}
_CRYPTO_CATALOG_IDS = {"bitcoin", "ethereum", "solana", "xrp", "btc", "eth", "sol"}
_COMMODITY_CATALOG_IDS = {"wti", "brent", "gold", "silver", "natural_gas", "copper", "uranium", "lithium", "xau", "cl", "bz"}


def _region_for(catalog_item_id: str) -> str | None:
    item = _catalog.get_by_id(catalog_item_id)
    if item is None:
        return None
    if item.country in ("ES",):
        return "spain"
    if item.region in ("Eurozone", "EU"):
        return "eurozone"
    if item.country in ("US",):
        return "usa"
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _warn(rows: list[dict], threshold: float = 0.5) -> list[str]:
    return [
        f"{r.get('catalog_item_id', '?')}: quality {r.get('quality_score', 0):.2f}"
        for r in rows
        if r.get("quality_score", 1.0) < threshold
    ]


def get_macro_snapshot() -> MacroSnapshotOut:
    rows = repository.get_latest_macro_all()
    spain, eurozone, usa = [], [], []
    for r in rows:
        point = MacroDataPoint(**{k: v for k, v in r.items() if k in MacroDataPoint.model_fields})
        region = _region_for(r.get("catalog_item_id", ""))
        if region == "spain":
            spain.append(point)
        elif region == "eurozone":
            eurozone.append(point)
        elif region == "usa":
            usa.append(point)
    return MacroSnapshotOut(spain=spain, eurozone=eurozone, usa=usa, generated_at=_now(), warnings=_warn(rows))


def get_market_snapshot() -> MarketSnapshotOut:
    quotes = repository.get_latest_quotes()
    indices = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
               for q in quotes if str(q.get("catalog_item_id", "")).lower() in _INDEX_CATALOG_IDS]
    crypto = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
              for q in quotes if str(q.get("catalog_item_id", "")).lower() in _CRYPTO_CATALOG_IDS]
    commodities = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
                   for q in quotes if str(q.get("catalog_item_id", "")).lower() in _COMMODITY_CATALOG_IDS]
    sections = [indices, crypto, commodities]
    all_items = [item for section in sections for item in section]
    quality = sum(item.quality_score for item in all_items) / len(all_items) if all_items else 0.0
    status = "ok" if indices and crypto and commodities else "partial" if all_items else "empty"
    warnings = _warn(quotes)
    if commodities and not indices and not crypto:
        warnings.append("Solo hay commodities disponibles.")
    return MarketSnapshotOut(
        status=status,
        indices=indices,
        crypto=crypto,
        commodities=commodities,
        generated_at=_now(),
        warnings=warnings,
        quality_score=round(quality, 2),
    )


def get_forex_snapshot() -> ForexSnapshotOut:
    rows = repository.get_latest_forex()
    rates = [ForexRateOut(
        catalog_item_id=r["catalog_item_id"],
        base_currency=r.get("base_currency"),
        quote_currency=r.get("quote_currency"),
        rate=r.get("rate"),
        date=str(r.get("date", "")),
        provider_id=r.get("provider_id"),
        quality_score=r.get("quality_score", 1.0),
    ) for r in rows]
    return ForexSnapshotOut(rates=rates, generated_at=_now(), warnings=_warn(rows))


def get_bond_snapshot() -> BondSnapshotOut:
    rows = repository.get_latest_bonds()
    yields = [BondYieldOut(
        catalog_item_id=r["catalog_item_id"],
        country=r.get("country"),
        maturity=r.get("maturity"),
        yield_value=r.get("yield_value"),
        date=str(r.get("date", "")),
        provider_id=r.get("provider_id"),
        quality_score=r.get("quality_score", 1.0),
    ) for r in rows]
    return BondSnapshotOut(yields=yields, generated_at=_now(), warnings=_warn(rows))


def get_news_snapshot(limit: int = 20) -> NewsSnapshotOut:
    rows = repository.get_latest_news(limit=limit)
    items = [NewsItemOut(
        id=r["id"], title=r.get("title"), published_at=str(r.get("published_at", "")),
        source_name=r.get("source_name"), url=r.get("url"),
        category=r.get("category"), provider_id=r.get("provider_id"),
    ) for r in rows]
    return NewsSnapshotOut(items=items, generated_at=_now())


def get_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    try:
        from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
        return generate_ai_datasheet(scope=scope)
    except ImportError:
        return AiDatasheetOut(generated_at=_now(), scope=scope)
