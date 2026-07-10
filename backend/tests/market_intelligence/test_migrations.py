import sqlite3

import pytest

from app.modules.market_intelligence.storage.migrations import run_migrations

EXPECTED_TABLES = [
    "mi_providers",
    "mi_catalog_items",
    "mi_provider_mappings",
    "mi_raw_records",
    "mi_normalized_records",
    "mi_market_quotes",
    "mi_historical_prices",
    "mi_macro_observations",
    "mi_currency_rates",
    "mi_bond_yields",
    "mi_commodities",
    "mi_company_profiles",
    "mi_news_items",
    "mi_provider_health_logs",
    "mi_data_quality_checks",
    "mi_ai_datasheets",
    "mi_ingest_state",
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def _tables(conn) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()}


def test_migrations_create_all_tables(conn):
    run_migrations(conn)
    existing = _tables(conn)
    for table in EXPECTED_TABLES:
        assert table in existing, f"Missing table: {table}"


def test_migrations_are_idempotent(conn):
    run_migrations(conn)
    run_migrations(conn)  # segunda vez no debe fallar
    assert len(_tables(conn)) == len(EXPECTED_TABLES)
