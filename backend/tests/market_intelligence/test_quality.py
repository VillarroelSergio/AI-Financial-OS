from datetime import datetime, timezone

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderMetadata, MacroIndicator,
)
from app.modules.market_intelligence.quality.engine import QualityEngine
from app.modules.market_intelligence.quality.checks import (
    check_freshness, check_completeness, check_validity, WEIGHTS,
)


def _meta():
    return ProviderMetadata(
        name="test", id="test", category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def _indicator():
    return CatalogIndicator(
        id="ipc_general", name="IPC España", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="ine",
    )


def _record(value: float = 2.8):
    return MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=datetime.now(timezone.utc),
        country="ES", region="Spain", value=value, indicator_id="ipc_general",
        name="IPC General", unit="%", period="2026-05", frequency="monthly",
    )


def _successful_result(records=None):
    if records is None:
        records = [_record()]
    return CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=records, error=None,
            latency_ms=120.0, raw_sample=None, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )


def test_score_successful_fetch_returns_positive_score():
    engine = QualityEngine()
    result = _successful_result()
    quality = engine.score(result, _indicator())
    assert quality.final_score > 0.0
    assert quality.final_score <= 1.0
    assert quality.passed is True


def test_score_failed_fetch_returns_zero():
    engine = QualityEngine()
    failed = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=False, records=[], error="timeout",
            latency_ms=10000.0, raw_sample=None, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )
    quality = engine.score(failed, _indicator())
    assert quality.final_score == 0.0
    assert quality.passed is False


def test_completeness_check_fails_with_no_records():
    result = _successful_result(records=[])
    result.adapter_result.success = True  # forzar
    check = check_completeness(result, _indicator())
    assert check.status == "fail"
    assert check.score == 0.0


def test_validity_check_with_valid_value():
    result = _successful_result()
    check = check_validity(result, _indicator())
    assert check.status == "pass"
    assert check.score == 1.0


def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"


def test_quality_result_has_five_checks():
    engine = QualityEngine()
    result = _successful_result()
    quality = engine.score(result, _indicator())
    assert len(quality.checks) == 5
