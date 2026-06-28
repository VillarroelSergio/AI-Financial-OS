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
