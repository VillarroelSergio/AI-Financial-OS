from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from datetime import datetime


def _make_metadata():
    return ProviderMetadata(
        name="Test", id="test", category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=5,
        license="open",
    )


def test_catalog_indicator_required_fields():
    ind = CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%",
        description="Tipo de referencia", provider_primary="bde",
    )
    assert ind.id == "euribor_3m"
    assert ind.provider_secondary is None
    assert ind.provider_fallback is None


def test_catalog_indicator_optional_providers():
    ind = CatalogIndicator(
        id="eur_usd", name="EUR/USD", category="forex",
        subcategory="major_pairs", country="GLOBAL", region="Global",
        frequency="daily", priority="high", dashboard=True, ai=True,
        historical="5y", retention="2y", unit="rate", description="",
        provider_primary="frankfurter", provider_secondary="ecb",
        provider_fallback="polygon",
    )
    assert ind.provider_secondary == "ecb"
    assert ind.provider_fallback == "polygon"


def test_catalog_fetch_result():
    ind = CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%", description="",
        provider_primary="bde",
    )
    result = AdapterResult(
        provider="BDE", success=True, records=[], error=None,
        latency_ms=100.0, raw_sample=None, metadata=_make_metadata(),
    )
    cfr = CatalogFetchResult(
        indicator=ind, adapter_result=result,
        provider_used="bde", fallback_used=False, catalog_id="euribor_3m",
    )
    assert cfr.catalog_id == "euribor_3m"
    assert cfr.fallback_used is False
