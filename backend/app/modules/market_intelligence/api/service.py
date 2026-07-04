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


def _status_for(row: dict) -> str:
    if row.get("value") is None and row.get("price") is None and row.get("rate") is None and row.get("yield_value") is None:
        return "unavailable"
    if row.get("quality_score", 1.0) < 0.5:
        return "limited"
    return "ok"


def get_macro_snapshot() -> MacroSnapshotOut:
    rows = repository.get_latest_macro_all()
    spain, eurozone, usa = [], [], []
    seen_values: dict[tuple[str | None, float | None, str | None], set[str]] = {}
    for r in rows:
        region = _region_for(r.get("catalog_item_id", ""))
        key = (region, r.get("value"), r.get("period"))
        seen_values.setdefault(key, set()).add(str(r.get("catalog_item_id", "")))
        payload = {k: v for k, v in r.items() if k in MacroDataPoint.model_fields}
        payload["retrieved_at"] = str(r.get("retrieved_at", "")) if r.get("retrieved_at") else None
        payload["data_status"] = _status_for(r)
        cat_item = _catalog.get_by_id(r.get("catalog_item_id", ""))
        payload["display_name"] = cat_item.name if cat_item else None
        payload["description"] = cat_item.description if cat_item else None
        point = MacroDataPoint(**payload)
        if region == "spain":
            spain.append(point)
        elif region == "eurozone":
            eurozone.append(point)
        elif region == "usa":
            usa.append(point)
    warnings = _warn(rows)
    repeated = [
        ids for (region, value, period), ids in seen_values.items()
        if region and value is not None and period and len(ids) >= 3
    ]
    if repeated:
        warnings.append("Se han detectado indicadores macro con valores repetidos; revisa fuente y fecha antes de usarlos.")
        repeated_ids = {catalog_id for ids in repeated for catalog_id in ids}
        for point in [*spain, *eurozone, *usa]:
            if point.catalog_item_id in repeated_ids:
                point.data_status = "requires_review"
                point.quality_score = min(point.quality_score, 0.4)
        # Remove repeated/polluted indicators so the UI doesn't show misleading data
        spain = [p for p in spain if p.catalog_item_id not in repeated_ids]
        eurozone = [p for p in eurozone if p.catalog_item_id not in repeated_ids]
        usa = [p for p in usa if p.catalog_item_id not in repeated_ids]
    all_items = [*spain, *eurozone, *usa]
    status = "ok" if spain and eurozone and usa else "partial" if all_items else "empty"
    return MacroSnapshotOut(status=status, spain=spain, eurozone=eurozone, usa=usa, generated_at=_now(), warnings=warnings)


def get_market_snapshot() -> MarketSnapshotOut:
    quotes = repository.get_latest_quotes()
    def quote(q: dict) -> QuoteOut:
        payload = {k: v for k, v in q.items() if k in QuoteOut.model_fields}
        payload["observed_at"] = str(q.get("observed_at", "")) if q.get("observed_at") else None
        payload["data_status"] = _status_for(q)
        cat_item = _catalog.get_by_id(q.get("catalog_item_id", ""))
        payload["display_name"] = cat_item.name if cat_item else None
        payload["display_country"] = cat_item.country if cat_item else None
        return QuoteOut(**payload)

    indices = [quote(q) for q in quotes if str(q.get("catalog_item_id", "")).lower() in _INDEX_CATALOG_IDS]
    crypto = [quote(q) for q in quotes if str(q.get("catalog_item_id", "")).lower() in _CRYPTO_CATALOG_IDS]
    commodities = [quote(q) for q in quotes if str(q.get("catalog_item_id", "")).lower() in _COMMODITY_CATALOG_IDS]
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
        data_status=_status_for(r),
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
        data_status=_status_for(r),
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
