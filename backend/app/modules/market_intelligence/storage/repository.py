"""Repository DuckDB para el Market Intelligence Layer."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.duckdb import get_duckdb
from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.ingestion.models import (
    BondYield,
    Commodity,
    CurrencyRate,
    HistoricalPrice,
    MacroIndicator,
    MarketQuote,
    NewsItem,
)
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import QualityResult
from app.modules.market_intelligence.storage.migrations import run_migrations

logger = logging.getLogger("market_intelligence.repository")

_migrations_run = False
_catalog = CatalogLoader()

# Tipos de registro admisibles por categoría de catálogo. Evita que un fallback
# genérico (p. ej. FRED devolviendo Fed Funds) persista macro bajo un bono o commodity.
_ALLOWED_MODELS_BY_CATEGORY: dict[str, set[str]] = {
    "macro": {"MacroIndicator"},
    "bonds": {"BondYield", "YieldCurvePoint"},
    "commodities": {"Commodity", "MarketQuote", "HistoricalPrice"},
    "indices": {"MarketQuote", "HistoricalPrice"},
    "crypto": {"MarketQuote", "HistoricalPrice"},
    "forex": {"CurrencyRate"},
    "news": {"NewsItem"},
}


def _expected_maturity(catalog_item_id: str) -> str | None:
    """us_2y → '2Y', spain_10y → '10Y'. None si el id no codifica maturity."""
    match = re.search(r"_(\d+)y$", catalog_item_id)
    return f"{match.group(1)}Y" if match else None


def _record_matches_catalog(catalog_item_id: str, record) -> bool:
    item = _catalog.get_by_id(catalog_item_id)
    if item is None or not item.category:
        return True  # item desconocido: no bloquear
    allowed = _ALLOWED_MODELS_BY_CATEGORY.get(item.category)
    if allowed is None:
        return True
    if type(record).__name__ not in allowed:
        return False
    # Los adapters de bonos devuelven la curva completa: solo la maturity del item
    if item.category == "bonds":
        expected = _expected_maturity(catalog_item_id)
        maturity = getattr(record, "maturity", None)
        if expected and maturity and maturity.upper() != expected:
            return False
    return True


def _conn():
    global _migrations_run
    c = get_duckdb()
    if not _migrations_run:
        run_migrations(c)
        _migrations_run = True
    return c


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


def _checksum(payload: str) -> str:
    return hashlib.md5(payload.encode()).hexdigest()


# ── Persist fetch result ──────────────────────────────────────────────────────

def persist_fetch_result(
    result: CatalogFetchResult,
    quality: QualityResult,
    run_id: str,
) -> None:
    """Persiste raw record + normalized record + log de salud."""
    conn = _conn()
    now = _now()
    catalog_item_id = result.catalog_id
    provider_id = result.provider_used

    # Raw record — idempotente por checksum
    raw_payload = json.dumps(result.adapter_result.raw_sample or {})
    checksum = _checksum(raw_payload)
    existing = conn.execute(
        "SELECT id FROM mi_raw_records WHERE catalog_item_id = ? AND checksum = ? LIMIT 1",
        [catalog_item_id, checksum],
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO mi_raw_records (id, catalog_item_id, provider_id, raw_payload_json,
                source_url, retrieved_at, ingestion_run_id, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [_uid(), catalog_item_id, provider_id, raw_payload,
             result.adapter_result.metadata.base_url, now, run_id, checksum],
        )

    # Normalized records por tipo de modelo
    for record in result.adapter_result.records:
        if not _record_matches_catalog(catalog_item_id, record):
            logger.debug(
                "Descartado %s para '%s': tipo incompatible con la categoría del catálogo",
                type(record).__name__, catalog_item_id,
            )
            continue
        _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now)

    # Health log
    log_provider_health(
        provider_id=provider_id,
        catalog_item_id=catalog_item_id,
        status="success",
        latency_ms=int(result.adapter_result.latency_ms),
    )


def _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now):
    model_type = type(record).__name__
    observed_at = getattr(record, "retrieved_at", now)

    # Idempotency: skip if same record already exists
    existing = conn.execute(
        "SELECT id FROM mi_normalized_records WHERE catalog_item_id = ? AND provider_id = ? AND model_type = ? AND observed_at = ? LIMIT 1",
        [catalog_item_id, provider_id, model_type, observed_at],
    ).fetchone()
    if existing:
        return

    def _first_not_none(*vals):
        for v in vals:
            if v is not None:
                return v
        return None

    value_numeric = _first_not_none(
        getattr(record, "value", None),
        getattr(record, "rate", None),
        getattr(record, "price", None),
        getattr(record, "yield_value", None),
    )
    conn.execute(
        """
        INSERT INTO mi_normalized_records
            (id, catalog_item_id, provider_id, model_type, observed_at, value_numeric,
             unit, period, frequency, source_url, retrieved_at, confidence_score, quality_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            _uid(), catalog_item_id, provider_id, model_type,
            observed_at,
            value_numeric,
            getattr(record, "unit", ""),
            getattr(record, "period", ""),
            getattr(record, "frequency", ""),
            getattr(record, "source", ""),
            now,
            getattr(record, "confidence_score", 1.0),
            quality.final_score,
            now,
        ],
    )

    # Tablas especializadas
    if isinstance(record, MacroIndicator):
        _upsert_macro(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, CurrencyRate):
        _upsert_currency(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, BondYield):
        _upsert_bond(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, MarketQuote):
        _upsert_quote(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, HistoricalPrice):
        _upsert_historical(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, Commodity):
        _upsert_commodity(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, NewsItem):
        _insert_news(conn, provider_id, record)


def _upsert_macro(conn, catalog_item_id, provider_id, record: MacroIndicator, quality):
    # DuckDB does not support INSERT OR REPLACE; use DELETE + INSERT
    conn.execute(
        "DELETE FROM mi_macro_observations WHERE catalog_item_id = ? AND period = ?",
        [catalog_item_id, record.period],
    )
    conn.execute(
        """
        INSERT INTO mi_macro_observations
            (id, catalog_item_id, indicator_id, country, period, frequency,
             value, unit, provider_id, quality_score, source_url, retrieved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.indicator_id, record.country,
         record.period, record.frequency, record.value, record.unit,
         provider_id, quality.final_score, record.source, record.retrieved_at],
    )


def _upsert_currency(conn, catalog_item_id, provider_id, record: CurrencyRate, quality):
    conn.execute(
        "DELETE FROM mi_currency_rates WHERE catalog_item_id = ? AND date = ?",
        [catalog_item_id, record.date],
    )
    conn.execute(
        """
        INSERT INTO mi_currency_rates
            (id, catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.base_currency, record.quote_currency,
         record.rate, record.date, provider_id, quality.final_score],
    )


def _upsert_bond(conn, catalog_item_id, provider_id, record: BondYield, quality):
    conn.execute(
        "DELETE FROM mi_bond_yields WHERE catalog_item_id = ? AND date = ? AND maturity = ?",
        [catalog_item_id, record.date, record.maturity],
    )
    conn.execute(
        """
        INSERT INTO mi_bond_yields
            (id, catalog_item_id, country, maturity, yield_value, date, currency,
             issuer, instrument_type, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.country, record.maturity, record.yield_value,
         record.date, record.currency, record.issuer, record.instrument_type,
         provider_id, quality.final_score],
    )


def _upsert_quote(conn, catalog_item_id, provider_id, record: MarketQuote, quality):
    conn.execute(
        "DELETE FROM mi_market_quotes WHERE catalog_item_id = ?",
        [catalog_item_id],
    )
    conn.execute(
        """
        INSERT INTO mi_market_quotes
            (id, catalog_item_id, symbol, asset_type, price, change_pct, currency,
             market_status, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.asset_type, record.price,
         record.change_pct, record.currency, record.market_status,
         record.retrieved_at, provider_id, quality.final_score],
    )


def _upsert_historical(conn, catalog_item_id, provider_id, record: HistoricalPrice, quality):
    conn.execute(
        "DELETE FROM mi_historical_prices WHERE catalog_item_id = ? AND symbol = ? AND date = ?",
        [catalog_item_id, record.symbol, record.date],
    )
    conn.execute(
        """INSERT INTO mi_historical_prices
            (id, catalog_item_id, symbol, date, open, high, low, close, volume, currency, provider_id, quality_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [_uid(), catalog_item_id, record.symbol, record.date,
         record.open, record.high, record.low, record.close, record.volume,
         getattr(record, 'currency', 'USD'), provider_id, quality.final_score],
    )


def _upsert_commodity(conn, catalog_item_id, provider_id, record: Commodity, quality):
    conn.execute(
        "DELETE FROM mi_commodities WHERE catalog_item_id = ?",
        [catalog_item_id],
    )
    conn.execute(
        """
        INSERT INTO mi_commodities
            (id, catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.name, record.price,
         record.unit, record.currency, record.retrieved_at, provider_id, quality.final_score],
    )


def _insert_news(conn, provider_id, record: NewsItem):
    conn.execute(
        """
        INSERT INTO mi_news_items (id, title, published_at, source_name, url, category, related_asset, provider_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), record.title, record.published_at, record.source_name,
         record.url, record.category, record.related_asset, provider_id],
    )


def log_provider_health(
    provider_id: str,
    catalog_item_id: str,
    status: str,
    latency_ms: int = 0,
    error_message: str | None = None,
) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_provider_health_logs (id, provider_id, catalog_item_id, status, latency_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [_uid(), provider_id, catalog_item_id, status, latency_ms, error_message],
    )


# ── Read functions ────────────────────────────────────────────────────────────

def get_latest_macro(catalog_item_id: str) -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM mi_macro_observations
        WHERE catalog_item_id = ?
        ORDER BY retrieved_at DESC
        LIMIT 1
        """,
        [catalog_item_id],
    ).fetchone()
    if row is None:
        return None
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit",
            "provider_id", "quality_score", "retrieved_at"]
    return dict(zip(cols, row))


def purge_mismatched_macro_observations() -> int:
    """Elimina observaciones macro estampadas bajo items que no son macro.

    Limpia la contaminación histórica del fallback FRED (Fed Funds persistido
    bajo us_2y/us_5y/us_10y/us_30y/wti...). Idempotente; se ejecuta al arrancar la ingesta.
    """
    non_macro_ids = [i.id for i in _catalog.load_all() if i.category and i.category != "macro"]
    if not non_macro_ids:
        return 0
    conn = _conn()
    placeholders = ", ".join("?" for _ in non_macro_ids)
    count = conn.execute(
        f"SELECT COUNT(*) FROM mi_macro_observations WHERE catalog_item_id IN ({placeholders})",
        non_macro_ids,
    ).fetchone()[0]
    if count:
        conn.execute(
            f"DELETE FROM mi_macro_observations WHERE catalog_item_id IN ({placeholders})",
            non_macro_ids,
        )
        logger.warning("Purgadas %d observaciones macro contaminadas (items no-macro)", count)

    # Bonos: elimina filas cuya maturity no coincide con la codificada en el id
    # (los adapters de curva persistían las 8 maturities bajo cada item).
    bond_purged = 0
    for item in _catalog.get_by_category("bonds"):
        expected = _expected_maturity(item.id)
        if not expected:
            continue
        mismatched = conn.execute(
            "SELECT COUNT(*) FROM mi_bond_yields WHERE catalog_item_id = ? AND upper(maturity) != ?",
            [item.id, expected],
        ).fetchone()[0]
        if mismatched:
            conn.execute(
                "DELETE FROM mi_bond_yields WHERE catalog_item_id = ? AND upper(maturity) != ?",
                [item.id, expected],
            )
            bond_purged += mismatched
    if bond_purged:
        logger.warning("Purgadas %d filas de bonos con maturity incorrecta", bond_purged)
    return int(count) + int(bond_purged)


def get_latest_macro_all() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM mi_macro_observations
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY retrieved_at DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit",
            "provider_id", "quality_score", "retrieved_at"]
    return [dict(zip(cols, r)) for r in rows]


def get_macro_history(max_points: int = 13) -> dict[str, list[tuple[str, float]]]:
    """Serie (period, value) por indicador macro, ordenada por periodo ascendente.

    Devuelve como máximo `max_points` puntos por indicador (suficiente para
    sparkline de 12 meses + delta vs periodo anterior).
    """
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, period, value
        FROM mi_macro_observations
        WHERE value IS NOT NULL AND period IS NOT NULL AND period != ''
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id, period ORDER BY retrieved_at DESC) = 1
        ORDER BY catalog_item_id, period
    """).fetchall()
    history: dict[str, list[tuple[str, float]]] = {}
    for catalog_item_id, period, value in rows:
        history.setdefault(str(catalog_item_id), []).append((str(period), float(value)))
    return {cid: points[-max_points:] for cid, points in history.items()}


def get_latest_quotes() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, symbol, asset_type, price, change_pct, currency, observed_at, provider_id, quality_score
        FROM mi_market_quotes
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY observed_at DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct",
            "currency", "observed_at", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_forex() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score
        FROM mi_currency_rates
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "base_currency", "quote_currency", "rate", "date",
            "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_bonds() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, country, maturity, yield_value, date, provider_id, quality_score
        FROM mi_bond_yields
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "country", "maturity", "yield_value", "date",
            "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_news(limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, title, published_at, source_name, url, category, related_asset, provider_id
        FROM mi_news_items
        ORDER BY published_at DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    cols = ["id", "title", "published_at", "source_name", "url", "category", "related_asset", "provider_id"]
    return [dict(zip(cols, r)) for r in rows]


def save_ai_datasheet(scope: str, datasheet_json: str, quality_score: float) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_ai_datasheets (id, snapshot_date, scope, datasheet_json, quality_score)
        VALUES (?, current_date, ?, ?, ?)
        """,
        [_uid(), scope, datasheet_json, quality_score],
    )


def get_latest_ai_datasheet(scope: str = "daily") -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT scope, datasheet_json, quality_score, generated_at
        FROM mi_ai_datasheets
        WHERE scope = ?
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        [scope],
    ).fetchone()
    if row is None:
        return None
    return {"scope": row[0], "datasheet_json": row[1], "quality_score": row[2], "generated_at": row[3]}
