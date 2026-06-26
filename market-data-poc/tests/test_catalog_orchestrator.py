from unittest.mock import Mock
from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from services.orchestrator import ProviderOrchestrator


def _make_metadata(name="TestAdapter"):
    return ProviderMetadata(
        name=name, id=name.lower(), category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=5,
        license="open",
    )


def _make_indicator(primary="bde", secondary="ecb", fallback=None):
    return CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%", description="",
        provider_primary=primary, provider_secondary=secondary,
        provider_fallback=fallback,
    )


def _make_adapter(name, provider_id, supported, success=True):
    adapter = Mock()
    adapter.name = name
    adapter.is_available.return_value = True
    adapter.supports.side_effect = lambda ind_id: ind_id in supported
    meta = _make_metadata(name)
    adapter.fetch.return_value = AdapterResult(
        provider=name, success=success, records=[], error=None,
        latency_ms=50.0, raw_sample=None, metadata=meta,
    )
    # Mock the provider ID via capabilities attr (used by _get_adapter)
    adapter._provider_id = provider_id
    return adapter


def _make_orchestrator(adapters):
    orch = ProviderOrchestrator(adapters)
    # Patch _get_adapter to look up by _provider_id
    def _get_adapter(pid):
        return next((a for a in adapters if a._provider_id == pid), None)
    orch._get_adapter = _get_adapter
    return orch


def test_fetch_indicator_uses_primary():
    bde = _make_adapter("BDE", "bde", {"euribor_3m"})
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"})
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert isinstance(result, CatalogFetchResult)
    assert result.provider_used == "bde"
    assert result.fallback_used is False
    assert result.catalog_id == "euribor_3m"


def test_fetch_indicator_falls_back_to_secondary_when_primary_fails():
    bde = _make_adapter("BDE", "bde", {"euribor_3m"}, success=False)
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"}, success=True)
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert result.provider_used == "ecb"
    assert result.fallback_used is True


def test_fetch_indicator_skips_unsupported_providers():
    bde = _make_adapter("BDE", "bde", set())  # no soporta euribor_3m
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"})
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert result.provider_used == "ecb"
    assert result.fallback_used is True


def test_fetch_indicator_returns_failed_result_when_no_provider_works():
    bde = _make_adapter("BDE", "bde", set())
    orch = _make_orchestrator([bde])
    indicator = _make_indicator(primary="bde", secondary=None, fallback=None)
    result = orch.fetch_indicator(indicator)
    assert isinstance(result, CatalogFetchResult)
    assert result.adapter_result.success is False
