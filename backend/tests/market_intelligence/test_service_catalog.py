from unittest.mock import MagicMock, patch


def _make_catalog_item(country: str = "", region: str = "") -> MagicMock:
    item = MagicMock()
    item.country = country
    item.region = region
    return item


def test_region_for_spain():
    from app.modules.market_intelligence.api.service import _region_for
    with patch("app.modules.market_intelligence.api.service._catalog") as mock_catalog:
        mock_catalog.get_by_id.return_value = _make_catalog_item(country="ES")
        assert _region_for("ipc_general") == "spain"


def test_region_for_eurozone():
    from app.modules.market_intelligence.api.service import _region_for
    with patch("app.modules.market_intelligence.api.service._catalog") as mock_catalog:
        mock_catalog.get_by_id.return_value = _make_catalog_item(country="", region="Eurozone")
        assert _region_for("tipo_bce") == "eurozone"


def test_region_for_usa():
    from app.modules.market_intelligence.api.service import _region_for
    with patch("app.modules.market_intelligence.api.service._catalog") as mock_catalog:
        mock_catalog.get_by_id.return_value = _make_catalog_item(country="US")
        assert _region_for("ipc_usa") == "usa"


def test_region_for_unknown():
    from app.modules.market_intelligence.api.service import _region_for
    with patch("app.modules.market_intelligence.api.service._catalog") as mock_catalog:
        mock_catalog.get_by_id.return_value = _make_catalog_item(country="JP")
        assert _region_for("nikkei225") is None


def test_region_for_missing_id():
    from app.modules.market_intelligence.api.service import _region_for
    with patch("app.modules.market_intelligence.api.service._catalog") as mock_catalog:
        mock_catalog.get_by_id.return_value = None
        assert _region_for("nonexistent") is None


def test_get_macro_snapshot_uses_catalog_not_hardcoded_sets():
    """Verify hardcoded sets are gone — _region_for is called via CatalogLoader."""
    import app.modules.market_intelligence.api.service as svc
    # Hardcoded sets must NOT exist
    assert not hasattr(svc, "_SPAIN_CATALOG_IDS"), "_SPAIN_CATALOG_IDS must be removed"
    assert not hasattr(svc, "_EUROZONE_CATALOG_IDS"), "_EUROZONE_CATALOG_IDS must be removed"
    assert not hasattr(svc, "_USA_CATALOG_IDS"), "_USA_CATALOG_IDS must be removed"
