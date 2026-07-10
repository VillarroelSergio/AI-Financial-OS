import sqlite3
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    MacroIndicator,
    ProviderMetadata,
)
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import CheckResult, QualityResult
from app.modules.market_intelligence.storage.migrations import run_migrations


@pytest.fixture
def in_memory_conn():
    c = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def patch_conn(in_memory_conn):
    with patch("app.modules.market_intelligence.storage.repository.get_conn", return_value=in_memory_conn):
        yield


def _meta():
    return ProviderMetadata(
        name="INE", id="ine", category="macro", region="Spain",
        method="api", base_url="https://ine.es", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=10,
        license="open",
    )


def _indicator():
    return CatalogIndicator(
        id="ipc_general", name="IPC España", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="ine",
    )


def _quality():
    return QualityResult(
        final_score=0.92,
        checks=[CheckResult("freshness", "pass", 1.0)],
    )


def test_persist_macro_and_read_back(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    now = datetime.now(timezone.utc)
    record = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain", indicator_id="ipc_general",
        name="IPC General", value=2.8, unit="%", period="2026-05", frequency="monthly",
    )
    fetch_result = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=[record], error=None,
            latency_ms=120.0, raw_sample={"test": 1}, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )

    repository.persist_fetch_result(fetch_result, _quality(), "run001")

    result = repository.get_latest_macro("ipc_general")
    assert result is not None
    assert result["catalog_item_id"] == "ipc_general"
    assert result["value"] == pytest.approx(2.8)


def test_idempotent_raw_records(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    now = datetime.now(timezone.utc)
    record = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain", indicator_id="ipc_general",
        name="IPC General", value=2.8, unit="%", period="2026-05", frequency="monthly",
    )
    fetch_result = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=[record], error=None,
            latency_ms=120.0, raw_sample={"same": "payload"}, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )

    repository.persist_fetch_result(fetch_result, _quality(), "run001")
    repository.persist_fetch_result(fetch_result, _quality(), "run002")

    count = in_memory_conn.execute("SELECT COUNT(*) FROM mi_raw_records").fetchone()[0]
    assert count == 1  # segundo insert con mismo checksum no persiste


def test_log_provider_health(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    repository.log_provider_health("ine", "ipc_general", "success", 120)
    count = in_memory_conn.execute("SELECT COUNT(*) FROM mi_provider_health_logs").fetchone()[0]
    assert count == 1
