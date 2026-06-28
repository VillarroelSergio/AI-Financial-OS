"""Repository DuckDB para el Market Intelligence Layer."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from app.core.duckdb import get_duckdb
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


def _table_count(conn, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
    except Exception:
        return 0


def _has_catalog_item(conn, table: str, catalog_item_id: str) -> bool:
    try:
        row = conn.execute(
            f"SELECT 1 FROM {table} WHERE catalog_item_id = ? LIMIT 1",
            [catalog_item_id],
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _has_valid_symbol_item(conn, table: str, catalog_item_id: str) -> bool:
    try:
        rows = conn.execute(
            f"SELECT catalog_item_id, symbol FROM {table} WHERE catalog_item_id = ?",
            [catalog_item_id],
        ).fetchall()
        return any(_valid_quote_row({"catalog_item_id": row[0], "symbol": row[1]}) for row in rows)
    except Exception:
        return False


_EXPECTED_SYMBOLS = {
    "sp500": {"^GSPC", "^SPX", "SPX", "GSPC"},
    "nasdaq": {"^IXIC", "^NDX", "IXIC", "NDX"},
    "nasdaq100": {"^NDX", "NDX"},
    "ibex35": {"^IBEX", "IBEX"},
    "eurostoxx50": {"^STOXX50E", "STOXX50E", "SX5E"},
    "dax": {"^GDAXI", "GDAXI", "DAX"},
    "nikkei225": {"^N225", "N225"},
    "bitcoin": {"BTC", "BTC-USD"},
    "ethereum": {"ETH", "ETH-USD"},
    "solana": {"SOL", "SOL-USD"},
    "xrp": {"XRP", "XRP-USD"},
    "gold": {"XAU", "GC=F", "GOLD"},
    "brent": {"BZ", "BZ=F", "BRENT"},
    "wti": {"CL", "CL=F", "WTI"},
}

_FX_PAIRS = {
    "eur_usd": ("EUR", "USD"),
    "eur_gbp": ("EUR", "GBP"),
    "eur_jpy": ("EUR", "JPY"),
    "eur_chf": ("EUR", "CHF"),
    "eur_cad": ("EUR", "CAD"),
    "eur_aud": ("EUR", "AUD"),
    "usd_jpy": ("USD", "JPY"),
    "gbp_usd": ("GBP", "USD"),
}

_BOND_MATCH = {
    "us_2y": ("US", "2Y"),
    "us_5y": ("US", "5Y"),
    "us_10y": ("US", "10Y"),
    "us_30y": ("US", "30Y"),
    "germany_10y": ("DE", "10Y"),
    "spain_10y": ("ES", "10Y"),
}


def _symbol(value: str | None) -> str:
    return (value or "").upper().strip()


def _record_matches_catalog(catalog_item_id: str, record: object) -> bool:
    if isinstance(record, MarketQuote | HistoricalPrice | Commodity):
        expected = _EXPECTED_SYMBOLS.get(catalog_item_id)
        if expected is None:
            return True
        symbol = _symbol(getattr(record, "symbol", None))
        name = _symbol(getattr(record, "name", None))
        return symbol in expected or any(token in name for token in expected)

    if isinstance(record, CurrencyRate):
        expected_pair = _FX_PAIRS.get(catalog_item_id)
        if expected_pair is None:
            return True
        return (record.base_currency, record.quote_currency) == expected_pair

    if isinstance(record, BondYield):
        expected_bond = _BOND_MATCH.get(catalog_item_id)
        if expected_bond is None:
            return True
        country, maturity = expected_bond
        return record.country == country and record.maturity == maturity

    return True


def _valid_quote_row(row: dict) -> bool:
    expected = _EXPECTED_SYMBOLS.get(row.get("catalog_item_id", ""))
    if expected is None:
        return True
    return _symbol(row.get("symbol")) in expected


def ensure_baseline_market_data() -> bool:
    """Seed minimal dashboard data when ingestion has not produced any rows yet."""
    conn = _conn()

    now = _now()
    today = date.today()
    period = today.strftime("%Y-%m")
    provider = "baseline_seed"
    quality = 0.45
    inserted = False

    macro_rows = [
        ("ipc_general", "inflation", "ES", period, 3.2, "%"),
        ("ipc_subyacente", "inflation_core", "ES", period, 2.9, "%"),
        ("tipo_bce", "policy_rate", "EA", period, 4.0, "%"),
        ("euribor_12m", "euribor", "ES", today.isoformat(), 3.7, "%"),
        ("inflation_eurozone", "hicp", "EA", period, 2.6, "%"),
        ("desempleo_spain", "unemployment", "ES", period, 11.8, "%"),
        ("confianza_consumidor_spain", "consumer_confidence", "ES", period, 86.0, "index"),
    ]
    for catalog_item_id, indicator_id, country, obs_period, value, unit in macro_rows:
        if not _has_catalog_item(conn, "mi_macro_observations", catalog_item_id):
            conn.execute(
                """
                INSERT INTO mi_macro_observations
                    (id, catalog_item_id, indicator_id, country, period, frequency,
                     value, unit, provider_id, quality_score, source_url, retrieved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_uid(), catalog_item_id, indicator_id, country, obs_period, "monthly",
                 value, unit, provider, quality, "internal://baseline-market-data", now],
            )
            inserted = True

    quote_rows = [
        ("sp500", "^GSPC", "index", 5450.0, 0.0, "USD"),
        ("nasdaq", "^IXIC", "index", 17800.0, 0.0, "USD"),
        ("ibex35", "^IBEX", "index", 11200.0, 0.0, "EUR"),
        ("eurostoxx50", "^STOXX50E", "index", 4950.0, 0.0, "EUR"),
        ("bitcoin", "BTC", "crypto", 62000.0, 0.0, "USD"),
        ("ethereum", "ETH", "crypto", 3400.0, 0.0, "USD"),
    ]
    for catalog_item_id, symbol, asset_type, price, change_pct, currency in quote_rows:
        if not _has_valid_symbol_item(conn, "mi_market_quotes", catalog_item_id):
            conn.execute(
                """
                INSERT INTO mi_market_quotes
                    (id, catalog_item_id, symbol, asset_type, price, change_pct, currency,
                     market_status, observed_at, provider_id, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_uid(), catalog_item_id, symbol, asset_type, price, change_pct, currency,
                 "baseline", now, provider, quality],
            )
            inserted = True

    fx_rows = [
        ("eur_usd", "EUR", "USD", 1.08),
        ("eur_gbp", "EUR", "GBP", 0.85),
        ("eur_jpy", "EUR", "JPY", 170.0),
    ]
    for catalog_item_id, base, quote, rate in fx_rows:
        if not _has_catalog_item(conn, "mi_currency_rates", catalog_item_id):
            conn.execute(
                """
                INSERT INTO mi_currency_rates
                    (id, catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_uid(), catalog_item_id, base, quote, rate, today, provider, quality],
            )
            inserted = True

    bond_rows = [
        ("us_2y", "US", "2Y", 4.7, "USD", "US Treasury"),
        ("us_5y", "US", "5Y", 4.3, "USD", "US Treasury"),
        ("us_10y", "US", "10Y", 4.2, "USD", "US Treasury"),
        ("us_30y", "US", "30Y", 4.4, "USD", "US Treasury"),
        ("germany_10y", "DE", "10Y", 2.5, "EUR", "Bund"),
        ("spain_10y", "ES", "10Y", 3.2, "EUR", "Tesoro"),
    ]
    for catalog_item_id, country, maturity, value, currency, issuer in bond_rows:
        if not _has_catalog_item(conn, "mi_bond_yields", catalog_item_id):
            conn.execute(
                """
                INSERT INTO mi_bond_yields
                    (id, catalog_item_id, country, maturity, yield_value, date, currency,
                     issuer, instrument_type, provider_id, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_uid(), catalog_item_id, country, maturity, value, today, currency,
                 issuer, "government_bond", provider, quality],
            )
            inserted = True

    commodity_rows = [
        ("gold", "XAU", "Oro", 2320.0, "USD/oz", "USD"),
        ("brent", "BZ", "Brent Crude Oil", 84.0, "USD/bbl", "USD"),
        ("wti", "CL", "WTI Crude Oil", 80.0, "USD/bbl", "USD"),
    ]
    for catalog_item_id, symbol, name, price, unit, currency in commodity_rows:
        if not _has_valid_symbol_item(conn, "mi_commodities", catalog_item_id):
            conn.execute(
                """
                INSERT INTO mi_commodities
                    (id, catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_uid(), catalog_item_id, symbol, name, price, unit, currency, now, provider, quality],
            )
            inserted = True

    return inserted


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
    matching_records = [record for record in result.adapter_result.records if _record_matches_catalog(catalog_item_id, record)]
    if result.adapter_result.records and not matching_records:
        logger.info("No matching records for catalog_item_id=%s provider=%s", catalog_item_id, provider_id)

    for record in matching_records:
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

    value_numeric = (
        getattr(record, "value", None)
        or getattr(record, "rate", None)
        or getattr(record, "price", None)
        or getattr(record, "yield_value", None)
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


def get_latest_quotes() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, symbol, asset_type, price, change_pct, currency, observed_at, provider_id, quality_score
        FROM mi_market_quotes
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY observed_at DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct",
            "currency", "observed_at", "provider_id", "quality_score"]
    return [row for row in (dict(zip(cols, r)) for r in rows) if _valid_quote_row(row)]


def get_latest_historical_as_quotes() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        WITH ranked AS (
            SELECT catalog_item_id, symbol, close, date, currency, provider_id, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) AS rn
            FROM mi_historical_prices
        )
        SELECT catalog_item_id, symbol, 'index' AS asset_type, close AS price,
               NULL AS change_pct, currency, date AS observed_at, provider_id, quality_score
        FROM ranked
        WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct",
            "currency", "observed_at", "provider_id", "quality_score"]
    return [row for row in (dict(zip(cols, r)) for r in rows) if _valid_quote_row(row)]


def get_latest_commodities() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, symbol, 'commodity' AS asset_type, price, NULL AS change_pct,
               currency, observed_at, provider_id, quality_score
        FROM mi_commodities
        QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY observed_at DESC) = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct",
            "currency", "observed_at", "provider_id", "quality_score"]
    return [row for row in (dict(zip(cols, r)) for r in rows) if _valid_quote_row(row)]


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
