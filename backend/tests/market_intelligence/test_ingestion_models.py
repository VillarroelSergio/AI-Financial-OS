from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.config import get_api_key
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    BondYield,
    MacroIndicator,
    ProviderHealth,
    ProviderMetadata,
    ProviderStatus,
)


def _meta():
    return ProviderMetadata(
        name="test", id="test", category="macro", region="Global",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def test_adapter_result_success():
    result = AdapterResult(
        provider="test", success=True, records=[], error=None,
        latency_ms=50.0, raw_sample=None, metadata=_meta(),
    )
    assert result.success is True
    assert result.latency_ms == 50.0


def test_macro_indicator_defaults():
    now = datetime.now(timezone.utc)
    ind = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain",
    )
    assert ind.confidence_score == 1.0
    assert ind.value == 0.0


def test_bond_yield_inherits_yield_curve_point():
    now = datetime.now(timezone.utc)
    b = BondYield(
        provider="FRED", source="https://fred.org", retrieved_at=now,
        country="US", region="USA", maturity="10Y", yield_value=4.32,
    )
    assert b.instrument_type == "government_bond"
    assert b.yield_value == 4.32


def test_get_api_key_missing_returns_none():
    result = get_api_key("nonexistent_provider_xyz")
    assert result is None


def test_provider_health_status_enum():
    now = datetime.now(timezone.utc)
    h = ProviderHealth(provider="test", status=ProviderStatus.DEGRADED, checked_at=now)
    assert h.status == ProviderStatus.DEGRADED
