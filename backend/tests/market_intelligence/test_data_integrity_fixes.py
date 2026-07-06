"""Tests de integridad de datos MI: tablas reales, guard de persistencia, purga y unidades FRED."""
from datetime import datetime, timezone

import duckdb
import pytest

from app.modules.market_intelligence.api.impact import _get_mi_data
from app.modules.market_intelligence.ingestion.adapters.usa.fred import _parse_fred_csv
from app.modules.market_intelligence.ingestion.models import MacroIndicator, YieldCurvePoint
from app.modules.market_intelligence.storage import repository
from app.modules.market_intelligence.storage.migrations import run_migrations


@pytest.fixture
def duck(monkeypatch):
    conn = duckdb.connect(":memory:")
    run_migrations(conn)
    # ECO-4: impact.py ya no toca get_duckdb; lee vía repository/macro_series (única puerta).
    monkeypatch.setattr("app.modules.market_intelligence.storage.repository.get_duckdb", lambda: conn)
    monkeypatch.setattr(repository, "_migrations_run", True)
    yield conn
    conn.close()


def test_get_mi_data_reads_real_tables(duck):
    """Regresión: impact.py consultaba tablas (mi_macro, mi_quotes...) e ids inexistentes."""
    duck.execute(
        "INSERT INTO mi_macro_observations (id, catalog_item_id, value, period, frequency, retrieved_at) VALUES "
        "('1', 'ipc_general', 2.8, '2026-06', 'monthly', '2026-06-01'), "
        "('2', 'tipo_bce', 2.15, '2026-06', 'monthly', '2026-06-01')"
    )
    duck.execute(
        "INSERT INTO mi_currency_rates (id, catalog_item_id, rate, date) VALUES ('3', 'eur_usd', 1.13, '2026-06-30')"
    )
    duck.execute(
        "INSERT INTO mi_bond_yields (id, catalog_item_id, yield_value, date) VALUES "
        "('4', 'spain_10y', 3.12, '2026-06-30'), ('5', 'germany_10y', 2.56, '2026-06-30')"
    )
    duck.execute(
        "INSERT INTO mi_market_quotes (id, catalog_item_id, price, observed_at) VALUES ('6', 'brent', 84.3, '2026-06-30')"
    )
    duck.execute(
        "INSERT INTO mi_historical_prices (id, catalog_item_id, date, close) VALUES "
        "('7', 'sp500', '2025-06-28', 5300.0), ('8', 'sp500', '2026-06-30', 5945.0)"
    )

    mi = _get_mi_data()
    assert mi["ipc_general"] == 2.8
    assert mi["tipo_bce"] == 2.15
    assert mi["eur_usd"] == 1.13
    assert mi["brent"] == 84.3
    assert mi["spain_10y"] == 3.12
    assert mi["risk_premium_bps"] == pytest.approx(56.0)
    assert mi["index_avg_change_1y"] == pytest.approx((5945.0 - 5300.0) / 5300.0 * 100)


def _macro_record(indicator_id: str = "FEDFUNDS") -> MacroIndicator:
    return MacroIndicator(
        provider="FRED", source="", retrieved_at=datetime.now(timezone.utc),
        country="US", region="USA", confidence_score=1.0,
        indicator_id=indicator_id, name="Fed Funds", value=3.63,
        unit="%", period="2026-06", frequency="monthly",
    )


def test_guard_blocks_macro_records_under_non_macro_items():
    """Regresión: Fed Funds persistido bajo us_2y/wti clonaba 3,63% en toda la región EEUU."""
    record = _macro_record()
    assert repository._record_matches_catalog("wti", record) is False
    assert repository._record_matches_catalog("us_2y", record) is False
    assert repository._record_matches_catalog("fed_funds_rate", record) is True
    # Ids desconocidos no se bloquean
    assert repository._record_matches_catalog("no_existe", record) is True


def _yield_point(maturity: str) -> YieldCurvePoint:
    return YieldCurvePoint(
        provider="FRED", source="", retrieved_at=datetime.now(timezone.utc),
        country="US", region="USA", confidence_score=1.0,
        maturity=maturity, yield_value=3.7, date=None, currency="USD",
    )


def test_guard_blocks_wrong_maturity_for_bond_items():
    """Los adapters de curva devuelven las 8 maturities; solo persiste la del item."""
    assert repository._record_matches_catalog("us_2y", _yield_point("2Y")) is True
    assert repository._record_matches_catalog("us_2y", _yield_point("1M")) is False
    assert repository._record_matches_catalog("spain_10y", _yield_point("10Y")) is True


def test_purge_removes_wrong_maturity_bond_rows(duck):
    duck.execute(
        "INSERT INTO mi_bond_yields (id, catalog_item_id, maturity, yield_value, date) VALUES "
        "('1', 'us_2y', '1M', 4.1, '2026-06-30'), ('2', 'us_2y', '2Y', 3.72, '2026-06-30')"
    )
    purged = repository.purge_mismatched_macro_observations()
    assert purged == 1
    remaining = duck.execute("SELECT maturity FROM mi_bond_yields").fetchall()
    assert remaining == [("2Y",)]


def test_purge_removes_contaminated_macro_rows(duck):
    duck.execute(
        "INSERT INTO mi_macro_observations (id, catalog_item_id, value, retrieved_at) VALUES "
        "('1', 'wti', 3.63, '2026-06-01'), ('2', 'us_2y', 3.63, '2026-06-01'), "
        "('3', 'ipc_general', 2.8, '2026-06-01')"
    )
    purged = repository.purge_mismatched_macro_observations()
    assert purged == 2
    remaining = duck.execute("SELECT catalog_item_id FROM mi_macro_observations").fetchall()
    assert remaining == [("ipc_general",)]
    # Idempotente
    assert repository.purge_mismatched_macro_observations() == 0


def test_fred_csv_respects_series_unit():
    """Regresión: INDPRO/UMCSENT se mostraban como '%' siendo índices."""
    csv_text = "DATE,INDPRO\n2026-04-01,102.1\n2026-05-01,102.65\n"
    records = _parse_fred_csv(csv_text, "INDPRO", "US Industrial Production", "http://x", unit="index")
    assert records
    assert all(r.unit == "index" for r in records)
    assert records[-1].value == 102.65
