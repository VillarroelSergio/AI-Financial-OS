from unittest.mock import MagicMock

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    ProviderMetadata,
)
from app.modules.market_intelligence.ingestion.orchestrator import ProviderOrchestrator


def _make_meta(name: str) -> ProviderMetadata:
    return ProviderMetadata(
        name=name, id=name, category="macro", region="Global",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def _make_adapter(name: str, success: bool, provider_id: str, supports: bool = True):
    adapter = MagicMock()
    adapter.name = name
    adapter.provider_id = provider_id
    adapter.is_available.return_value = True
    adapter.supports.return_value = supports
    adapter.fetch.return_value = AdapterResult(
        provider=name, success=success, records=[], error=None if success else "fail",
        latency_ms=50.0, raw_sample=None, metadata=_make_meta(name),
    )
    return adapter


def _make_indicator(primary: str, secondary: str | None = None, fallback: str | None = None):
    return CatalogIndicator(
        id="test_ind", name="Test", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="5y", retention="5y",
        unit="%", description="", provider_primary=primary,
        provider_secondary=secondary, provider_fallback=fallback,
    )


def test_uses_primary_when_available():
    primary = _make_adapter("primary", success=True, provider_id="primary")
    orch = ProviderOrchestrator([primary])
    result = orch.fetch_indicator(_make_indicator("primary"))
    assert result.provider_used == "primary"
    assert result.fallback_used is False
    assert result.adapter_result.success is True


def test_falls_back_to_secondary_when_primary_fails():
    primary = _make_adapter("primary", success=False, provider_id="primary")
    secondary = _make_adapter("secondary", success=True, provider_id="secondary")
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"
    assert result.fallback_used is True


def test_returns_failure_when_all_providers_fail():
    primary = _make_adapter("primary", success=False, provider_id="primary")
    orch = ProviderOrchestrator([primary])
    result = orch.fetch_indicator(_make_indicator("primary"))
    assert result.adapter_result.success is False
    assert result.provider_used == "none"


def test_skips_unavailable_adapter():
    primary = _make_adapter("primary", success=True, provider_id="primary")
    primary.is_available.return_value = False
    secondary = _make_adapter("secondary", success=True, provider_id="secondary")
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"


def test_skips_adapter_that_does_not_support_indicator():
    primary = _make_adapter("primary", success=True, provider_id="primary", supports=False)
    secondary = _make_adapter("secondary", success=True, provider_id="secondary", supports=True)
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"
