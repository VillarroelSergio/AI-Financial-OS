"""DuckDB DDL para el Market Intelligence Layer.

Ejecutar run_migrations(conn) al arrancar o con market:intelligence:init-db.
Todas las tablas usan CREATE TABLE IF NOT EXISTS para ser idempotentes.
"""
from __future__ import annotations

import duckdb

_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS mi_providers (
        id                TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        region            TEXT,
        category          TEXT,
        status            TEXT DEFAULT 'ok',
        coverage_score    DOUBLE DEFAULT 0.0,
        quality_score     DOUBLE DEFAULT 0.0,
        integration_score DOUBLE DEFAULT 0.0,
        reliability_score DOUBLE DEFAULT 0.0,
        created_at        TIMESTAMP DEFAULT current_timestamp,
        updated_at        TIMESTAMP DEFAULT current_timestamp
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
        dashboard_visible BOOLEAN DEFAULT true,
        ai_visible        BOOLEAN DEFAULT true,
        historical_window TEXT,
        retention_policy  TEXT,
        model_type        TEXT,
        unit              TEXT,
        description       TEXT,
        created_at        TIMESTAMP DEFAULT current_timestamp,
        updated_at        TIMESTAMP DEFAULT current_timestamp
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
        enabled           BOOLEAN DEFAULT true,
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
        retrieved_at      TIMESTAMP NOT NULL,
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
        observed_at       TIMESTAMP,
        value_numeric     DOUBLE,
        value_text        TEXT,
        currency          TEXT,
        unit              TEXT,
        period            TEXT,
        frequency         TEXT,
        metadata_json     TEXT,
        source_url        TEXT,
        retrieved_at      TIMESTAMP,
        confidence_score  DOUBLE DEFAULT 1.0,
        quality_score     DOUBLE DEFAULT 1.0,
        created_at        TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_market_quotes (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        asset_type      TEXT,
        price           DOUBLE,
        change_pct      DOUBLE,
        currency        TEXT DEFAULT 'USD',
        market_status   TEXT,
        observed_at     TIMESTAMP,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_historical_prices (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        date            DATE,
        open            DOUBLE,
        high            DOUBLE,
        low             DOUBLE,
        close           DOUBLE,
        volume          BIGINT,
        currency        TEXT DEFAULT 'USD',
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
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
        value           DOUBLE,
        unit            TEXT,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0,
        source_url      TEXT,
        retrieved_at    TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_currency_rates (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        base_currency   TEXT,
        quote_currency  TEXT,
        rate            DOUBLE,
        date            DATE,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_bond_yields (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        country         TEXT,
        maturity        TEXT,
        yield_value     DOUBLE,
        date            DATE,
        currency        TEXT DEFAULT 'USD',
        issuer          TEXT,
        instrument_type TEXT DEFAULT 'government_bond',
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_commodities (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        name            TEXT,
        price           DOUBLE,
        unit            TEXT,
        currency        TEXT DEFAULT 'USD',
        observed_at     TIMESTAMP,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_company_profiles (
        id            TEXT PRIMARY KEY,
        symbol        TEXT,
        name          TEXT,
        sector        TEXT,
        industry      TEXT,
        market_cap    DOUBLE,
        exchange      TEXT,
        isin          TEXT,
        figi          TEXT,
        country       TEXT,
        provider_id   TEXT,
        quality_score DOUBLE DEFAULT 1.0,
        updated_at    TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_news_items (
        id              TEXT PRIMARY KEY,
        title           TEXT,
        published_at    TIMESTAMP,
        source_name     TEXT,
        url             TEXT,
        category        TEXT,
        related_asset   TEXT,
        sentiment_score DOUBLE DEFAULT 0.0,
        importance_score DOUBLE DEFAULT 0.5,
        provider_id     TEXT,
        created_at      TIMESTAMP DEFAULT current_timestamp
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
        checked_at      TIMESTAMP DEFAULT current_timestamp
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
        created_at      TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_ai_datasheets (
        id              TEXT PRIMARY KEY,
        snapshot_date   DATE NOT NULL,
        scope           TEXT NOT NULL DEFAULT 'daily',
        datasheet_json  TEXT NOT NULL,
        quality_score   DOUBLE DEFAULT 0.0,
        generated_at    TIMESTAMP DEFAULT current_timestamp
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
        fallback_used   BOOLEAN DEFAULT false,
        last_run_id     TEXT,
        last_run_at     TIMESTAMP,
        last_success_at TIMESTAMP
    )
    """,
]


def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Crea todas las tablas MI en DuckDB si no existen."""
    for ddl in _DDL_STATEMENTS:
        conn.execute(ddl)
