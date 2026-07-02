"""Verifica que todos los adapters migrados se importan sin error."""
import importlib

import pytest

ADAPTER_MODULES = [
    "app.modules.market_intelligence.ingestion.adapters.base",
    "app.modules.market_intelligence.ingestion.adapters.catalog",
    "app.modules.market_intelligence.ingestion.adapters.europe.ecb",
    "app.modules.market_intelligence.ingestion.adapters.europe.eurostat",
    "app.modules.market_intelligence.ingestion.adapters.europe.oecd",
    "app.modules.market_intelligence.ingestion.adapters.spain.ine",
    "app.modules.market_intelligence.ingestion.adapters.spain.bde",
    "app.modules.market_intelligence.ingestion.adapters.usa.fred",
    "app.modules.market_intelligence.ingestion.adapters.global_.frankfurter",
    "app.modules.market_intelligence.ingestion.adapters.global_.coingecko",
    "app.modules.market_intelligence.ingestion.adapters.global_.stooq",
]


@pytest.mark.parametrize("module_path", ADAPTER_MODULES)
def test_adapter_module_imports(module_path):
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_base_adapter_has_required_interface():
    from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
    assert hasattr(BaseAdapter, "fetch")
    assert hasattr(BaseAdapter, "is_available")
    assert hasattr(BaseAdapter, "supports")
    assert hasattr(BaseAdapter, "health_check")


def test_fred_adapter_fetch_bond_by_catalog_id_returns_yield():
    """us_2y (catalog ID) debe mapear a DGS2 y devolver un YieldCurvePoint, no un error."""
    from unittest.mock import MagicMock, patch

    from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
    from app.modules.market_intelligence.ingestion.models import YieldCurvePoint

    csv_content = "DATE,VALUE\n2026-05-01,4.20\n2026-06-01,4.15\n"
    mock_response = MagicMock()
    mock_response.text = csv_content
    mock_response.raise_for_status = MagicMock()

    adapter = FREDAdapter()
    with patch("requests.get", return_value=mock_response):
        result = adapter.fetch("us_2y")

    assert result.success is True
    assert len(result.records) == 1
    assert isinstance(result.records[0], YieldCurvePoint)
    assert result.records[0].maturity == "2Y"
    assert result.records[0].yield_value == 4.15
