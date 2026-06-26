"""Market Intelligence API service — lee desde DuckDB, nunca llama providers."""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut, BondSnapshotOut, BondYieldOut, ForexRateOut, ForexSnapshotOut,
    MacroDataPoint, MacroSnapshotOut, MarketSnapshotOut, NewsItemOut, NewsSnapshotOut,
    QuoteOut,
)
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.api")

_SPAIN_CATALOG_IDS = {"ipc_general", "ipc_subyacente", "pib_spain", "desempleo_spain", "euribor_12m", "euribor_3m"}
_EUROZONE_CATALOG_IDS = {"tipo_bce", "ipc_eurozona", "pib_eurozona", "desempleo_eurozona"}
_USA_CATALOG_IDS = {"ipc_usa", "gdp_usa", "desempleo_usa", "fed_funds_rate"}
_INDEX_CATALOG_IDS = {"sp500", "nasdaq100", "ibex35", "eurostoxx50", "dax", "nikkei225"}
_CRYPTO_CATALOG_IDS = {"btc", "eth", "sol", "xrp"}


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
        cid = r.get("catalog_item_id", "")
        if cid in _SPAIN_CATALOG_IDS:
            spain.append(point)
        elif cid in _EUROZONE_CATALOG_IDS:
            eurozone.append(point)
        elif cid in _USA_CATALOG_IDS:
            usa.append(point)
    return MacroSnapshotOut(spain=spain, eurozone=eurozone, usa=usa, generated_at=_now(), warnings=_warn(rows))


def get_market_snapshot() -> MarketSnapshotOut:
    quotes = repository.get_latest_quotes()
    indices = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
               for q in quotes if q.get("catalog_item_id") in _INDEX_CATALOG_IDS]
    crypto = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
              for q in quotes if q.get("catalog_item_id") in _CRYPTO_CATALOG_IDS]
    return MarketSnapshotOut(indices=indices, crypto=crypto, commodities=[], generated_at=_now(), warnings=_warn(quotes))


def get_forex_snapshot() -> ForexSnapshotOut:
    rows = repository.get_latest_forex()
    rates = []
    for r in rows:
        rates.append(ForexRateOut(
            catalog_item_id=r["catalog_item_id"],
            base_currency=r.get("base_currency"),
            quote_currency=r.get("quote_currency"),
            rate=r.get("rate"),
            date=str(r.get("date", "")),
            provider_id=r.get("provider_id"),
            quality_score=r.get("quality_score", 1.0),
        ))
    return ForexSnapshotOut(rates=rates, generated_at=_now(), warnings=_warn(rows))


def get_bond_snapshot() -> BondSnapshotOut:
    rows = repository.get_latest_bonds()
    yields = []
    for r in rows:
        yields.append(BondYieldOut(
            catalog_item_id=r["catalog_item_id"],
            country=r.get("country"),
            maturity=r.get("maturity"),
            yield_value=r.get("yield_value"),
            date=str(r.get("date", "")),
            provider_id=r.get("provider_id"),
            quality_score=r.get("quality_score", 1.0),
        ))
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
    """Genera el AI Datasheet. La IA local SOLO llama a esta función."""
    try:
        from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
        return generate_ai_datasheet(scope=scope)
    except ImportError:
        return AiDatasheetOut(generated_at=_now(), scope=scope)
