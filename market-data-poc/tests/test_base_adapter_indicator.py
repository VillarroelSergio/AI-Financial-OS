from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from datetime import datetime


class _LegacyAdapter(BaseAdapter):
    name = "Legacy"
    category = "macro"
    region = "Global"

    def fetch(self, indicator_id=None):
        metadata = self._make_metadata()
        return AdapterResult(
            provider=self.name, success=True, records=[],
            error=None, latency_ms=10.0, raw_sample=None, metadata=metadata,
        )


class _MigratedAdapter(BaseAdapter):
    name = "Migrated"
    category = "macro"
    region = "Global"
    supported_indicators = {
        "euribor_3m": {"series": "BE001"},
        "euribor_12m": {"series": "BE002"},
    }

    def fetch(self, indicator_id=None):
        metadata = self._make_metadata()
        return AdapterResult(
            provider=self.name, success=True, records=[],
            error=None, latency_ms=10.0, raw_sample=None, metadata=metadata,
        )


def test_legacy_adapter_has_no_supported_indicators():
    adapter = _LegacyAdapter()
    assert adapter.supported_indicators == {}


def test_legacy_adapter_supports_nothing():
    adapter = _LegacyAdapter()
    assert adapter.supports("euribor_3m") is False


def test_migrated_adapter_supports_declared_indicators():
    adapter = _MigratedAdapter()
    assert adapter.supports("euribor_3m") is True
    assert adapter.supports("euribor_12m") is True


def test_migrated_adapter_does_not_support_undeclared():
    adapter = _MigratedAdapter()
    assert adapter.supports("pib_spain") is False


def test_legacy_fetch_accepts_none():
    adapter = _LegacyAdapter()
    result = adapter.fetch(indicator_id=None)
    assert result.success is True


def test_legacy_fetch_accepts_indicator_id_without_crash():
    adapter = _LegacyAdapter()
    result = adapter.fetch(indicator_id="euribor_3m")
    assert result is not None
