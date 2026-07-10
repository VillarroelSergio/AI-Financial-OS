"""ECO-5: estado de ingesta por item y job de retención (SQLite en memoria, ECO-3b)."""
import sqlite3
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.market_intelligence.storage import repository
from app.modules.market_intelligence.storage.migrations import run_migrations


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
    run_migrations(c)
    with patch("app.modules.market_intelligence.storage.repository.get_conn", return_value=c):
        yield c
    c.close()


def test_retention_years_parsing():
    assert repository._retention_years("5y") == 5
    assert repository._retention_years("30y") == 30
    assert repository._retention_years("") is None
    assert repository._retention_years(None) is None
    assert repository._retention_years("forever") is None


def test_record_ingest_result_roundtrip_and_success_not_overwritten(conn):
    now = datetime(2026, 7, 6, tzinfo=timezone.utc)
    repository.record_ingest_result("ipc_general", "monthly", "ok", "eurostat", False, "run1", now)
    state = repository.get_ingest_state()["ipc_general"]
    assert state["last_status"] == "ok"
    assert state["provider_used"] == "eurostat"

    # Un fallo posterior NO debe borrar el last_success_at (el scheduler cuenta con él).
    later = datetime(2026, 7, 7, tzinfo=timezone.utc)
    repository.record_ingest_result("ipc_general", "monthly", "error", "eurostat", False, "run2", later)
    state = repository.get_ingest_state()["ipc_general"]
    assert state["last_status"] == "error"
    assert state["last_success_at"] is not None


def test_apply_retention_prunes_old_periods(conn):
    # ipc_general tiene retention 10y en el catálogo → corte ≈ 2016.
    for pid, period in [("old", "2015-01"), ("new", "2026-01")]:
        conn.execute(
            "INSERT INTO mi_macro_observations "
            "(id, catalog_item_id, indicator_id, country, period, frequency, value, unit, "
            " provider_id, quality_score, source_url, retrieved_at) "
            "VALUES (?, 'ipc_general', 'ipc', 'ES', ?, 'monthly', 1.0, '%', 'eurostat', 1.0, '', ?)",
            [pid, period, datetime.now(timezone.utc)],
        )
    deleted = repository.apply_retention(now=datetime(2026, 7, 6, tzinfo=timezone.utc))
    assert deleted["macro_rows"] >= 1
    remaining = {r[0] for r in conn.execute(
        "SELECT period FROM mi_macro_observations WHERE catalog_item_id = 'ipc_general'"
    ).fetchall()}
    assert "2026-01" in remaining
    assert "2015-01" not in remaining
