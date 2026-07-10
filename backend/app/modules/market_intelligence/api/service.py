"""Market Intelligence API service — lee desde SQLite (ECO-3b), nunca llama providers."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut,
    BondSnapshotOut,
    BondYieldOut,
    EconomyOverviewOut,
    ForexRateOut,
    ForexSnapshotOut,
    MacroDataPoint,
    MacroSnapshotOut,
    MarketSnapshotOut,
    NewsItemOut,
    NewsSnapshotOut,
    QuoteOut,
    RegionBlockOut,
    ThemedGroupOut,
)
from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.api")

def _storage_warnings() -> list[str]:
    # ECO-3b: SQLite WAL no cae a memoria (no hay mono-escritor). Sin aviso de almacenamiento.
    return []

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
    try:
        macro_history = repository.get_macro_history()
    except Exception:
        macro_history = {}
    spain, eurozone, usa = [], [], []
    for r in rows:
        catalog_id = str(r.get("catalog_item_id", ""))
        region = _region_for(catalog_id)
        payload = {k: v for k, v in r.items() if k in MacroDataPoint.model_fields}
        payload["retrieved_at"] = str(r.get("retrieved_at", "")) if r.get("retrieved_at") else None
        payload["data_status"] = _status_for(r)
        cat_item = _catalog.get_by_id(catalog_id)
        payload["display_name"] = cat_item.name if cat_item else None
        payload["description"] = cat_item.description if cat_item else None
        payload["subcategory"] = cat_item.subcategory if cat_item else None
        payload["frequency"] = cat_item.frequency if cat_item else None
        payload["priority"] = cat_item.priority if cat_item else None
        # La unidad del catálogo manda sobre la que reporte el adapter
        if cat_item and cat_item.unit:
            payload["unit"] = cat_item.unit
        points = macro_history.get(catalog_id, [])
        payload["history"] = [{"period": p, "value": v} for p, v in points]
        if len(points) >= 2 and r.get("value") is not None:
            payload["previous_value"] = points[-2][1]
            payload["delta"] = round(float(r["value"]) - points[-2][1], 4)
        point = MacroDataPoint(**payload)
        if region == "spain":
            spain.append(point)
        elif region == "eurozone":
            eurozone.append(point)
        elif region == "usa":
            usa.append(point)
    # ECO-1: la detección de "valores repetidos" en lectura era un parche del bug de
    # clonación (P1), ya cortado en origen con allowlists honestas en los adapters.
    warnings = _storage_warnings() + _warn(rows)
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
    warnings = _storage_warnings() + _warn(quotes)
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


# ── ECO-6: overview agregado ──────────────────────────────────────────────────
# Agrupación temática y "snapshot global" vivían en EconomyPage.tsx; se resuelven aquí
# para que la UI reciba datos ya agrupados (DoD: lógica temática fuera del frontend).
# Propuesta §3: temas que responden preguntas del usuario (no listas de series).
# policy_rate ya no cae en "Otros" (fix §1). El agrupado vive aquí, en backend (ECO-6).
_THEME_BY_SUBCATEGORY: dict[str, str] = {
    "inflation": "Precios y consumo",
    "consumption": "Precios y consumo",
    "sentiment": "Precios y consumo",
    "housing": "Vivienda",
    "interest_rates": "Ahorro y tipos",
    "policy_rate": "Ahorro y tipos",
    "monetary": "Ahorro y tipos",
    "employment": "Empleo y salarios",
    "energy": "Energía",
    "gdp": "Actividad y cuentas públicas",
    "industrial": "Actividad y cuentas públicas",
    "fiscal": "Actividad y cuentas públicas",
    "pmi": "Actividad y cuentas públicas",
}
_THEME_ORDER = [
    "Precios y consumo", "Vivienda", "Ahorro y tipos", "Empleo y salarios",
    "Energía", "Actividad y cuentas públicas", "Otros",
]
_GLOBAL_PICK = ["ipc_general", "euribor_12m", "tipo_bce", "fed_funds_rate"]


def _group_by_theme(points: list[MacroDataPoint]) -> RegionBlockOut:
    groups: dict[str, list[MacroDataPoint]] = {}
    for p in points:
        theme = _THEME_BY_SUBCATEGORY.get(p.subcategory or "", "Otros")
        groups.setdefault(theme, []).append(p)
    themes = [ThemedGroupOut(theme=t, indicators=groups[t]) for t in _THEME_ORDER if t in groups]
    return RegionBlockOut(themes=themes)


def get_economy_overview(db) -> EconomyOverviewOut:
    """ECO-6: colapsa los 5 requests de EconomyPage en uno; agrupa por tema en backend."""
    from app.modules.market_intelligence.api.impact import compute_personal_impact
    from app.modules.market_intelligence.api.personal_economy import compute_personal_economy

    macro = get_macro_snapshot()
    all_points = [*macro.spain, *macro.eurozone, *macro.usa]
    by_id = {p.catalog_item_id: p for p in all_points}
    picked = [by_id[i] for i in _GLOBAL_PICK if i in by_id]
    rest = [p for p in all_points if p.catalog_item_id not in _GLOBAL_PICK]
    global_indicators = (picked + rest)[:4]

    return EconomyOverviewOut(
        status=macro.status,
        generated_at=macro.generated_at,
        warnings=macro.warnings,
        global_indicators=global_indicators,
        regions={
            "ES": _group_by_theme(macro.spain),
            "EA": _group_by_theme(macro.eurozone),
            "US": _group_by_theme(macro.usa),
        },
        impact=compute_personal_impact(db),
        bonds=get_bond_snapshot(),
        forex=get_forex_snapshot(),
        personal_economy=compute_personal_economy(db),
    )


def get_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    try:
        from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
        return generate_ai_datasheet(scope=scope)
    except ImportError:
        return AiDatasheetOut(generated_at=_now(), scope=scope)
