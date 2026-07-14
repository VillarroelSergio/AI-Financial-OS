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


# ── MKT-6: ficha de instrumento (histórico EOD) ───────────────────────────────
# Rangos por span de calendario (mes+) …
_RANGE_DAYS = {"1m": 30, "6m": 182, "1y": 365, "5y": 1825}
# … y rangos cortos por nº de cierres (datos EOD: días de bolsa, no de calendario).
# 1d = últimos 2 cierres (dibuja el movimiento del día); 5d ≈ una semana de bolsa.
_RANGE_TAIL = {"1d": 2, "5d": 6}
_RANGE_ORDER = ["1d", "5d", "1m", "6m", "1y", "5y"]
_MAX_POINTS = 400  # downsampling: mantiene el gráfico fluido en rangos largos


def _f(v) -> float | None:
    """Trata 0/None como ausente para OHLC (Stooq puebla reales; 0.0 = sin dato)."""
    return float(v) if v else None


def _downsample(rows: list[dict], max_points: int) -> list[dict]:
    if len(rows) <= max_points:
        return rows
    n = len(rows)
    # Índices equiespaciados; primero=0, último=n-1 (el último dato nunca se pierde).
    idx = sorted({round(i * (n - 1) / (max_points - 1)) for i in range(max_points)})
    return [rows[i] for i in idx]


def _compute_stats(all_rows: list[dict], selected: list[dict]) -> "HistoryStatsOut":
    from datetime import timedelta

    from app.modules.market_intelligence.api.schemas import HistoryStatsOut

    last = all_rows[-1]
    prev = all_rows[-2] if len(all_rows) >= 2 else None
    cutoff52 = last["date"] - timedelta(days=365)
    window = [r for r in all_rows if r["date"] >= cutoff52]
    lows = [r["low"] for r in window if _f(r.get("low")) is not None] or [r["close"] for r in window]
    highs = [r["high"] for r in window if _f(r.get("high")) is not None] or [r["close"] for r in window]
    first_close = selected[0]["close"] if selected else last["close"]
    change = ((last["close"] - first_close) / first_close * 100) if first_close else None
    return HistoryStatsOut(
        previous_close=_f(prev["close"]) if prev else None,
        open=_f(last.get("open")),
        day_low=_f(last.get("low")),
        day_high=_f(last.get("high")),
        week52_low=round(min(lows), 4) if lows else None,
        week52_high=round(max(highs), 4) if highs else None,
        range_change_pct=round(change, 2) if change is not None else None,
        volume=int(last["volume"]) if last.get("volume") else None,
    )


def get_instrument_history(indicator_code: str, range_key: str = "max"):
    """MKT-6: serie EOD + stats + rangos honestos derivados del span real (ECO-2)."""
    from datetime import timedelta

    from app.modules.market_intelligence.api.schemas import HistoryPointOut, InstrumentHistoryOut

    item = _catalog.get_by_id(indicator_code)
    name = item.name if item else None
    region = item.country if item else None
    rows = repository.read_historical(indicator_code)
    if not rows:
        return InstrumentHistoryOut(
            indicator_code=indicator_code, name=name, region=region,
            available_ranges=[], range=range_key, series=[],
        )

    first_date, last = rows[0]["date"], rows[-1]
    span = (last["date"] - first_date).days

    def _covers(r: str) -> bool:
        return len(rows) >= _RANGE_TAIL[r] if r in _RANGE_TAIL else span >= _RANGE_DAYS[r]

    available = [r for r in _RANGE_ORDER if _covers(r)] + ["max"]
    rk = range_key if range_key in available else "max"
    if rk == "max":
        selected = rows
    elif rk in _RANGE_TAIL:
        selected = rows[-_RANGE_TAIL[rk]:]
    else:
        cutoff = last["date"] - timedelta(days=_RANGE_DAYS[rk])
        selected = [r for r in rows if r["date"] >= cutoff] or rows

    stats = _compute_stats(rows, selected)
    series = _downsample(selected, _MAX_POINTS)
    return InstrumentHistoryOut(
        indicator_code=indicator_code, name=name, region=region,
        currency=last.get("currency"), provider_id=last.get("provider_id"),
        quality_score=round(float(last.get("quality_score") or 1.0), 2),
        last_updated=last["date"].isoformat(), granularity="eod",
        available_ranges=available, range=rk, stats=stats,
        series=[
            HistoryPointOut(
                date=r["date"].isoformat(), close=float(r["close"]),
                volume=int(r["volume"]) if r.get("volume") else None,
            )
            for r in series
        ],
    )


def get_sparklines(codes: list[str], points: int = 30) -> dict[str, list[float]]:
    """MKT-8: últimos N cierres por instrumento para mini-gráficas de fila. Solo lectura."""
    return repository.read_sparklines(codes, points=max(2, min(points, 60)))


def get_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    try:
        from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
        return generate_ai_datasheet(scope=scope)
    except ImportError:
        return AiDatasheetOut(generated_at=_now(), scope=scope)
