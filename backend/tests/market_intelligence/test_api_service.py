from unittest.mock import patch
import pytest

from app.modules.market_intelligence.api import service


def test_get_macro_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_macro_all", return_value=[]):
        result = service.get_macro_snapshot()
    assert result.status == "empty"
    assert hasattr(result, "spain")
    assert hasattr(result, "eurozone")
    assert hasattr(result, "usa")
    assert hasattr(result, "generated_at")
    assert isinstance(result.warnings, list)


def test_get_macro_snapshot_marks_repeated_values_for_review():
    rows = [
        {
            "catalog_item_id": "spain_cpi",
            "indicator_id": "cpi",
            "country": "ES",
            "period": "2026-05",
            "value": 1.8,
            "unit": "%",
            "provider_id": "test",
            "quality_score": 0.9,
            "retrieved_at": "2026-06-29T10:00:00Z",
        },
        {
            "catalog_item_id": "spain_core_cpi",
            "indicator_id": "core_cpi",
            "country": "ES",
            "period": "2026-05",
            "value": 1.8,
            "unit": "%",
            "provider_id": "test",
            "quality_score": 0.9,
            "retrieved_at": "2026-06-29T10:00:00Z",
        },
        {
            "catalog_item_id": "spain_unemployment",
            "indicator_id": "unemployment",
            "country": "ES",
            "period": "2026-05",
            "value": 1.8,
            "unit": "%",
            "provider_id": "test",
            "quality_score": 0.9,
            "retrieved_at": "2026-06-29T10:00:00Z",
        },
    ]
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_macro_all", return_value=rows):
        result = service.get_macro_snapshot()

    assert result.status == "partial"
    assert result.warnings
    assert {item.data_status for item in result.spain} == {"requires_review"}
    assert all(item.quality_score == 0.4 for item in result.spain)


def test_get_forex_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_forex", return_value=[]):
        result = service.get_forex_snapshot()
    assert hasattr(result, "rates")
    assert hasattr(result, "generated_at")


def test_get_bond_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_bonds", return_value=[]):
        result = service.get_bond_snapshot()
    assert hasattr(result, "yields")


def test_get_market_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_quotes", return_value=[]):
        result = service.get_market_snapshot()
    assert hasattr(result, "indices")
    assert hasattr(result, "crypto")


def test_get_news_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_news", return_value=[]):
        result = service.get_news_snapshot()
    assert hasattr(result, "items")
    assert isinstance(result.items, list)
