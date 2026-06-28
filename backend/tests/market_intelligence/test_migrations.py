import duckdb
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
]


@pytest.fixture
def conn():
    c = duckdb.connect(":memory:")
    yield c
    c.close()


def test_migrations_create_all_tables(conn):
    run_migrations(conn)
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    for table in EXPECTED_TABLES:
        assert table in existing, f"Missing table: {table}"


def test_migrations_are_idempotent(conn):
    run_migrations(conn)
    run_migrations(conn)  # segunda vez no debe fallar
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert len(existing) == len(EXPECTED_TABLES)
