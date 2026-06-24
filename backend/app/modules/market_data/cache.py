"""DuckDB-backed cache for market data.

Tables:
  market_quotes_cache       — latest quote per symbol (upsert on fetch)
  market_candles_cache      — OHLCV history (append-only, deduplicated by symbol+timestamp)
  market_provider_logs      — structured fetch logs for debugging
  market_company_profiles   — company profiles (long TTL)
  market_fundamentals_cache — fundamentals (long TTL)
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import duckdb

from app.core.config import settings
from app.modules.market_data.providers.base import MarketQuoteInternal

logger = logging.getLogger(__name__)

_conn: Optional[duckdb.DuckDBPyConnection] = None
_conn_lock = threading.Lock()

_DDL = """
CREATE TABLE IF NOT EXISTS market_quotes_cache (
    internal_symbol  VARCHAR PRIMARY KEY,
    name             VARCHAR NOT NULL,
    category         VARCHAR NOT NULL,
    asset_type       VARCHAR NOT NULL,
    price            DOUBLE,
    change_absolute  DOUBLE,
    change_percent   DOUBLE,
    currency         VARCHAR NOT NULL,
    source           VARCHAR NOT NULL,
    source_type      VARCHAR NOT NULL,
    freshness_status VARCHAR NOT NULL,
    delay_minutes    INTEGER NOT NULL DEFAULT 0,
    is_stale         BOOLEAN NOT NULL DEFAULT false,
    is_fallback      BOOLEAN NOT NULL DEFAULT false,
    confidence_score DOUBLE NOT NULL DEFAULT 0.0,
    warning          VARCHAR,
    sparkline        VARCHAR,
    market_status    VARCHAR NOT NULL DEFAULT 'unknown',
    market_time      TIMESTAMP,
    provider_symbol  VARCHAR,
    fetched_at       TIMESTAMP NOT NULL,
    cached_at        TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS market_candles_cache (
    internal_symbol  VARCHAR NOT NULL,
    provider_symbol  VARCHAR NOT NULL,
    source           VARCHAR NOT NULL,
    ts               TIMESTAMP NOT NULL,
    open             DOUBLE,
    high             DOUBLE,
    low              DOUBLE,
    close            DOUBLE NOT NULL,
    volume           DOUBLE,
    currency         VARCHAR,
    PRIMARY KEY (internal_symbol, source, ts)
);

CREATE TABLE IF NOT EXISTS market_provider_logs (
    id               BIGINT DEFAULT nextval('market_log_seq'),
    provider         VARCHAR NOT NULL,
    internal_symbol  VARCHAR NOT NULL,
    provider_symbol  VARCHAR,
    asset_type       VARCHAR,
    fetched_at       TIMESTAMP NOT NULL,
    cache_hit        BOOLEAN NOT NULL DEFAULT false,
    freshness_status VARCHAR,
    rate_limited     BOOLEAN NOT NULL DEFAULT false,
    fallback_used    BOOLEAN NOT NULL DEFAULT false,
    error            VARCHAR,
    parse_error      BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS market_company_profiles (
    internal_symbol  VARCHAR PRIMARY KEY,
    provider_symbol  VARCHAR,
    source           VARCHAR NOT NULL,
    name             VARCHAR,
    exchange         VARCHAR,
    sector           VARCHAR,
    industry         VARCHAR,
    country          VARCHAR,
    currency         VARCHAR,
    website          VARCHAR,
    description      VARCHAR,
    cached_at        TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS market_fundamentals_cache (
    internal_symbol  VARCHAR PRIMARY KEY,
    provider_symbol  VARCHAR,
    source           VARCHAR NOT NULL,
    market_cap       DOUBLE,
    pe_ratio         DOUBLE,
    dividend_yield   DOUBLE,
    eps              DOUBLE,
    revenue          DOUBLE,
    profit_margin    DOUBLE,
    beta             DOUBLE,
    updated_at       TIMESTAMP,
    cached_at        TIMESTAMP NOT NULL
);
"""

_CREATE_SEQ = "CREATE SEQUENCE IF NOT EXISTS market_log_seq;"


def _get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        with _conn_lock:
            if _conn is None:
                db_path = Path(settings.DUCKDB_PATH)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                _conn = duckdb.connect(str(db_path))
                _conn.execute(_CREATE_SEQ)
                _conn.execute(_DDL)
    return _conn


class MarketCache:
    """Thread-safe DuckDB-backed market data cache."""

    def get_quote(self, internal_symbol: str) -> Optional[dict]:
        """Return cached row as dict, or None if not found."""
        try:
            conn = _get_conn()
            with _conn_lock:
                rows = conn.execute(
                    "SELECT * FROM market_quotes_cache WHERE internal_symbol = ?",
                    [internal_symbol],
                ).fetchdf()
            if rows.empty:
                return None
            row = rows.iloc[0].to_dict()
            # Deserialize sparkline JSON
            sparkline_raw = row.get("sparkline")
            row["sparkline"] = json.loads(sparkline_raw) if sparkline_raw else []
            return row
        except Exception as exc:
            logger.warning("MarketCache.get_quote error for %s: %s", internal_symbol, exc)
            return None

    def put_quote(self, quote: MarketQuoteInternal) -> None:
        """Upsert a quote into the cache."""
        try:
            now = datetime.now(timezone.utc)
            sparkline_json = json.dumps(quote.sparkline)
            market_time_val = quote.market_time.isoformat() if quote.market_time else None
            conn = _get_conn()
            with _conn_lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO market_quotes_cache (
                        internal_symbol, name, category, asset_type,
                        price, change_absolute, change_percent, currency,
                        source, source_type, freshness_status, delay_minutes,
                        is_stale, is_fallback, confidence_score, warning,
                        sparkline, market_status, market_time, provider_symbol,
                        fetched_at, cached_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    [
                        quote.internal_symbol, quote.name, quote.category, quote.asset_type,
                        quote.price, quote.change_absolute, quote.change_percent, quote.currency,
                        quote.source, quote.source_type, quote.freshness_status, quote.delay_minutes,
                        quote.is_stale, quote.is_fallback, quote.confidence_score, quote.warning,
                        sparkline_json, quote.market_status, market_time_val, quote.provider_symbol,
                        quote.fetched_at.isoformat(), now.isoformat(),
                    ],
                )
        except Exception as exc:
            logger.warning("MarketCache.put_quote error for %s: %s", quote.internal_symbol, exc)

    def log_fetch(
        self,
        *,
        provider: str,
        internal_symbol: str,
        provider_symbol: str,
        asset_type: str,
        cache_hit: bool,
        freshness_status: str,
        rate_limited: bool = False,
        fallback_used: bool = False,
        error: Optional[str] = None,
        parse_error: bool = False,
    ) -> None:
        try:
            conn = _get_conn()
            with _conn_lock:
                conn.execute(
                    """
                    INSERT INTO market_provider_logs (
                        provider, internal_symbol, provider_symbol, asset_type,
                        fetched_at, cache_hit, freshness_status,
                        rate_limited, fallback_used, error, parse_error
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    [
                        provider, internal_symbol, provider_symbol, asset_type,
                        datetime.now(timezone.utc).isoformat(), cache_hit, freshness_status,
                        rate_limited, fallback_used, error, parse_error,
                    ],
                )
        except Exception as exc:
            logger.debug("MarketCache.log_fetch error: %s", exc)

    def get_all_quotes(self, category: Optional[str] = None) -> list[dict]:
        """Return all cached quotes, optionally filtered by category."""
        try:
            conn = _get_conn()
            with _conn_lock:
                if category:
                    rows = conn.execute(
                        "SELECT * FROM market_quotes_cache WHERE category = ? ORDER BY internal_symbol",
                        [category],
                    ).fetchdf()
                else:
                    rows = conn.execute(
                        "SELECT * FROM market_quotes_cache ORDER BY category, internal_symbol"
                    ).fetchdf()
            result = []
            for _, row in rows.iterrows():
                d = row.to_dict()
                sparkline_raw = d.get("sparkline")
                d["sparkline"] = json.loads(sparkline_raw) if sparkline_raw else []
                result.append(d)
            return result
        except Exception as exc:
            logger.warning("MarketCache.get_all_quotes error: %s", exc)
            return []
