"""Tests del diagnóstico de ingesta: motivos por proveedor y aviso de modo memoria."""
from unittest.mock import MagicMock

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.orchestrator import ProviderOrchestrator
from app.modules.market_intelligence.ingestion.startup import get_ingest_status


def _make_meta(name: str) -> ProviderMetadata:
    return ProviderMetadata(
        name=name, id=name, category="macro", region="Global",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def _make_indicator(primary: str, secondary: str | None = None):
    return CatalogIndicator(
        id="test_ind", name="Test", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="5y", retention="5y",
        unit="%", description="", provider_primary=primary,
        provider_secondary=secondary, provider_fallback=None,
    )


def test_failure_error_includes_reason_per_provider():
    failing = MagicMock()
    failing.name = "primary"
    failing.provider_id = "primary"
    failing.is_available.return_value = True
    failing.supports.return_value = True
    failing.fetch.return_value = AdapterResult(
        provider="primary", success=False, records=[], error="HTTP 429 rate limit",
        latency_ms=10.0, raw_sample=None, metadata=_make_meta("primary"),
    )
    unavailable = MagicMock()
    unavailable.name = "secondary"
    unavailable.provider_id = "secondary"
    unavailable.is_available.return_value = False

    orch = ProviderOrchestrator([failing, unavailable])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))

    assert result.adapter_result.success is False
    assert "primary: HTTP 429 rate limit" in result.adapter_result.error
    assert "secondary: no disponible" in result.adapter_result.error


def test_ingest_status_reports_storage_mode(monkeypatch):
    status = get_ingest_status()
    assert status["storage"] in ("file", "memory")

    monkeypatch.setattr(
        "app.modules.market_intelligence.ingestion.startup.is_in_memory", lambda: True
    )
    status = get_ingest_status()
    assert status["storage"] == "memory"
    assert "no persisten" in status["storage_warning"]
