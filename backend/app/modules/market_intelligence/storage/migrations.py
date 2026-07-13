"""DDL SQLite para el Market Intelligence Layer (ECO-3b, antes DuckDB).

Ejecutar run_migrations(conn) al arrancar o con market:intelligence:init-db.
Todas las tablas usan CREATE TABLE IF NOT EXISTS para ser idempotentes.

Tipos: DOUBLE→REAL, BIGINT→INTEGER, BOOLEAN→INTEGER (0/1). Los timestamps son TEXT
(ISO); solo mi_historical_prices.date se declara DATE para que vuelva como objeto date
(get_price_change_1y hace aritmética de fechas). Ver storage/db.py.
"""
from __future__ import annotations

import sqlite3

_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS mi_providers (
        id                TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        region            TEXT,
        category          TEXT,
        status            TEXT DEFAULT 'ok',
        coverage_score    REAL DEFAULT 0.0,
        quality_score     REAL DEFAULT 0.0,
        integration_score REAL DEFAULT 0.0,
        reliability_score REAL DEFAULT 0.0,
        created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_catalog_items (
        id                TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        category          TEXT,
        subcategory       TEXT,
        country           TEXT,
        region            TEXT,
        frequency         TEXT,
        priority          TEXT,
        dashboard_visible INTEGER DEFAULT 1,
        ai_visible        INTEGER DEFAULT 1,
        historical_window TEXT,
        retention_policy  TEXT,
        model_type        TEXT,
        unit              TEXT,
        description       TEXT,
        created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_provider_mappings (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        role              TEXT NOT NULL,
        provider_symbol   TEXT,
        provider_series_id TEXT,
        endpoint          TEXT,
        priority_order    INTEGER DEFAULT 0,
        enabled           INTEGER DEFAULT 1,
        notes             TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_raw_records (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        raw_payload_json  TEXT,
        source_url        TEXT,
        retrieved_at      TEXT NOT NULL,
        ingestion_run_id  TEXT,
        checksum          TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_normalized_records (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        model_type        TEXT,
        observed_at       TEXT,
        value_numeric     REAL,
        value_text        TEXT,
        currency          TEXT,
        unit              TEXT,
        period            TEXT,
        frequency         TEXT,
        metadata_json     TEXT,
        source_url        TEXT,
        retrieved_at      TEXT,
        confidence_score  REAL DEFAULT 1.0,
        quality_score     REAL DEFAULT 1.0,
        created_at        TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_market_quotes (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        asset_type      TEXT,
        price           REAL,
        change_pct      REAL,
        currency        TEXT DEFAULT 'USD',
        market_status   TEXT,
        observed_at     TEXT,
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_historical_prices (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        date            DATE,
        open            REAL,
        high            REAL,
        low             REAL,
        close           REAL,
        volume          INTEGER,
        currency        TEXT DEFAULT 'USD',
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_macro_observations (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        indicator_id    TEXT,
        country         TEXT,
        period          TEXT,
        frequency       TEXT,
        value           REAL,
        unit            TEXT,
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0,
        source_url      TEXT,
        retrieved_at    TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_currency_rates (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        base_currency   TEXT,
        quote_currency  TEXT,
        rate            REAL,
        date            TEXT,
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_bond_yields (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        country         TEXT,
        maturity        TEXT,
        yield_value     REAL,
        date            TEXT,
        currency        TEXT DEFAULT 'USD',
        issuer          TEXT,
        instrument_type TEXT DEFAULT 'government_bond',
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_commodities (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        name            TEXT,
        price           REAL,
        unit            TEXT,
        currency        TEXT DEFAULT 'USD',
        observed_at     TEXT,
        provider_id     TEXT,
        quality_score   REAL DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_company_profiles (
        id            TEXT PRIMARY KEY,
        symbol        TEXT,
        name          TEXT,
        sector        TEXT,
        industry      TEXT,
        market_cap    REAL,
        exchange      TEXT,
        isin          TEXT,
        figi          TEXT,
        country       TEXT,
        provider_id   TEXT,
        quality_score REAL DEFAULT 1.0,
        updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_news_items (
        id              TEXT PRIMARY KEY,
        title           TEXT,
        published_at    TEXT,
        source_name     TEXT,
        url             TEXT,
        category        TEXT,
        related_asset   TEXT,
        sentiment_score REAL DEFAULT 0.0,
        importance_score REAL DEFAULT 0.5,
        provider_id     TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_provider_health_logs (
        id              TEXT PRIMARY KEY,
        provider_id     TEXT NOT NULL,
        catalog_item_id TEXT,
        status          TEXT,
        latency_ms      INTEGER,
        error_message   TEXT,
        checked_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_data_quality_checks (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        provider_id     TEXT,
        check_type      TEXT,
        status          TEXT,
        details_json    TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_ai_datasheets (
        id              TEXT PRIMARY KEY,
        snapshot_date   TEXT NOT NULL,
        scope           TEXT NOT NULL DEFAULT 'daily',
        datasheet_json  TEXT NOT NULL,
        quality_score   REAL DEFAULT 0.0,
        generated_at    TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ECO-5: última ingesta por item — base del scheduler por frecuencia (solo refetch
    # cuando last_success + frequency ha vencido) y del estado estructurado de /ingest-status.
    """
    CREATE TABLE IF NOT EXISTS mi_ingest_state (
        catalog_item_id TEXT PRIMARY KEY,
        frequency       TEXT,
        last_status     TEXT,
        provider_used   TEXT,
        fallback_used   INTEGER DEFAULT 0,
        last_run_id     TEXT,
        last_run_at     TEXT,
        last_success_at TEXT
    )
    """,
    # MKT-6: la ficha de instrumento lee series por (catalog_item_id, date). Sin índice
    # el GET escanea toda la tabla; con 5 años x decenas de instrumentos ya se nota.
    "CREATE INDEX IF NOT EXISTS idx_hist_prices_item_date ON mi_historical_prices (catalog_item_id, date)",
]


def run_migrations(conn: sqlite3.Connection) -> None:
    """Crea todas las tablas MI en SQLite si no existen."""
    for ddl in _DDL_STATEMENTS:
        conn.execute(ddl)
