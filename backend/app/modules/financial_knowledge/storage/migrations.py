"""DuckDB DDL para el Financial Knowledge Layer.

Ejecutar run_migrations(conn) al arrancar.
"""
from __future__ import annotations
import duckdb

_DDL_STATEMENTS = [
    # fk_economic_indicator_insights
    """CREATE TABLE IF NOT EXISTS fk_economic_indicator_insights (
        id                    TEXT PRIMARY KEY,
        indicator_id          TEXT NOT NULL,
        catalog_item_id       TEXT,
        name                  TEXT NOT NULL,
        category              TEXT,
        country               TEXT,
        value                 DOUBLE,
        unit                  TEXT,
        period                TEXT,
        previous_value        DOUBLE,
        change_abs            DOUBLE,
        change_pct            DOUBLE,
        trend                 TEXT,
        target_value          DOUBLE,
        distance_to_target    DOUBLE,
        interpretation        TEXT,
        severity              TEXT,
        quality_score         DOUBLE DEFAULT 1.0,
        source_provider       TEXT,
        rule_id               TEXT,
        computed_at           TIMESTAMP NOT NULL,
        created_at            TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_financial_signals
    """CREATE TABLE IF NOT EXISTS fk_financial_signals (
        id                        TEXT PRIMARY KEY,
        signal_type               TEXT NOT NULL,
        name                      TEXT NOT NULL,
        category                  TEXT,
        description               TEXT,
        direction                 TEXT,
        severity                  TEXT,
        confidence_score          DOUBLE DEFAULT 1.0,
        quality_score             DOUBLE DEFAULT 1.0,
        affected_assets_json      TEXT,
        affected_user_domains_json TEXT,
        source_indicators_json    TEXT,
        rule_id                   TEXT,
        computed_at               TIMESTAMP NOT NULL,
        created_at                TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_market_regimes
    """CREATE TABLE IF NOT EXISTS fk_market_regimes (
        id                TEXT PRIMARY KEY,
        regime_type       TEXT,
        risk_level        TEXT,
        inflation_regime  TEXT,
        rates_regime      TEXT,
        growth_regime     TEXT,
        market_trend      TEXT,
        confidence_score  DOUBLE DEFAULT 0.0,
        signals_used_json TEXT,
        explanation       TEXT,
        computed_at       TIMESTAMP NOT NULL,
        created_at        TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_correlation_insights
    """CREATE TABLE IF NOT EXISTS fk_correlation_insights (
        id                TEXT PRIMARY KEY,
        signal_id         TEXT NOT NULL,
        signal_type       TEXT,
        asset_type        TEXT,
        user_domain       TEXT,
        relationship_type TEXT,
        description       TEXT,
        confidence_score  DOUBLE DEFAULT 0.8,
        computed_at       TIMESTAMP NOT NULL,
        created_at        TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_personal_impacts
    """CREATE TABLE IF NOT EXISTS fk_personal_impacts (
        id                          TEXT PRIMARY KEY,
        impact_type                 TEXT NOT NULL,
        user_domain                 TEXT,
        title                       TEXT NOT NULL,
        description                 TEXT,
        severity                    TEXT,
        estimated_monthly_impact    DOUBLE,
        estimated_portfolio_impact  DOUBLE,
        currency                    TEXT DEFAULT 'EUR',
        related_accounts_json       TEXT,
        related_holdings_json       TEXT,
        related_goals_json          TEXT,
        source_signals_json         TEXT,
        confidence_score            DOUBLE DEFAULT 0.5,
        computed_at                 TIMESTAMP NOT NULL,
        created_at                  TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_knowledge_graph_nodes
    """CREATE TABLE IF NOT EXISTS fk_knowledge_graph_nodes (
        id          TEXT PRIMARY KEY,
        node_type   TEXT NOT NULL,
        label       TEXT NOT NULL,
        properties_json TEXT,
        computed_at TIMESTAMP NOT NULL,
        created_at  TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_knowledge_graph_edges
    """CREATE TABLE IF NOT EXISTS fk_knowledge_graph_edges (
        id              TEXT PRIMARY KEY,
        source_id       TEXT NOT NULL,
        target_id       TEXT NOT NULL,
        relationship    TEXT NOT NULL,
        weight          DOUBLE DEFAULT 1.0,
        properties_json TEXT,
        computed_at     TIMESTAMP NOT NULL,
        created_at      TIMESTAMP DEFAULT current_timestamp
    )""",
    # fk_ai_datasheets
    """CREATE TABLE IF NOT EXISTS fk_ai_datasheets (
        id              TEXT PRIMARY KEY,
        scope           TEXT NOT NULL DEFAULT 'daily',
        datasheet_json  TEXT NOT NULL,
        quality_score   DOUBLE DEFAULT 0.0,
        generated_at    TIMESTAMP NOT NULL,
        created_at      TIMESTAMP DEFAULT current_timestamp
    )""",
]

def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Crea todas las tablas FK en DuckDB si no existen."""
    for ddl in _DDL_STATEMENTS:
        conn.execute(ddl)
