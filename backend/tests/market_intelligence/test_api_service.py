from unittest.mock import patch

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


def test_get_macro_snapshot_keeps_all_values():
    # ECO-1: la clonación (P1) se corta en origen (allowlists honestas en adapters),
    # así que la lectura ya NO filtra ni degrada indicadores por compartir valor.
    rows = [
        {
            "catalog_item_id": "ipc_general",
            "indicator_id": "ipc_general",
            "country": "ES",
            "period": "2026-05",
            "value": 1.8,
            "unit": "%",
            "provider_id": "test",
            "quality_score": 0.9,
            "retrieved_at": "2026-06-29T10:00:00Z",
        },
        {
            "catalog_item_id": "ipc_subyacente",
            "indicator_id": "ipc_subyacente",
            "country": "ES",
            "period": "2026-05",
            "value": 1.8,
            "unit": "%",
            "provider_id": "test",
            "quality_score": 0.9,
            "retrieved_at": "2026-06-29T10:00:00Z",
        },
        {
            "catalog_item_id": "pib_spain",
            "indicator_id": "pib_spain",
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

    # Sin filtro de "repetidos": los 3 items españoles se conservan.
    assert result.status == "partial"  # solo hay región spain
    assert {p.catalog_item_id for p in result.spain} == {"ipc_general", "ipc_subyacente", "pib_spain"}
    assert not any("repetid" in w.lower() for w in result.warnings)


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


def test_get_market_snapshot_includes_display_name():
    rows = [{
        "catalog_item_id": "sp500",
        "symbol": "^SPX",
        "asset_type": "index",
        "price": 5800.0,
        "change_pct": 0.5,
        "currency": "USD",
        "observed_at": "2026-06-01T10:00:00Z",
        "provider_id": "stooq",
        "quality_score": 0.9,
    }]
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_quotes", return_value=rows):
        result = service.get_market_snapshot()
    assert result.indices[0].display_name == "S&P 500"
    assert result.indices[0].display_country == "US"


def test_get_macro_snapshot_includes_display_name():
    rows = [{
        "catalog_item_id": "ipc_general",
        "indicator_id": "ipc_general",
        "country": "ES",
        "period": "2026-05",
        "value": 2.1,
        "unit": "%",
        "provider_id": "ine",
        "quality_score": 0.9,
        "retrieved_at": "2026-06-01T10:00:00Z",
    }]
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_macro_all", return_value=rows):
        result = service.get_macro_snapshot()
    assert result.spain[0].display_name is not None
    assert "ipc" in result.spain[0].display_name.lower() or "general" in result.spain[0].display_name.lower()
    assert result.spain[0].description is not None
