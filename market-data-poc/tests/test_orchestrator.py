from datetime import datetime

from adapters.base import BaseAdapter
from models.base import AdapterResult
from models.market import MarketQuote
from services.comparator import compare_equivalent_values
from services.orchestrator import ProviderOrchestrator


class DummyAdapter(BaseAdapter):
    category = "markets"
    region = "Global"
    capabilities = ("stocks",)
    requires_api_key = False

    def __init__(self, name, priority, success, price):
        self.name = name
        self.priority = priority
        self._success = success
        self._price = price

    def fetch(self):
        records = []
        if self._success:
            records.append(
                MarketQuote(
                    provider=self.name,
                    source="test",
                    retrieved_at=datetime.utcnow(),
                    country="GLOBAL",
                    region="Global",
                    symbol="AAPL",
                    asset_type="stock",
                    price=self._price,
                )
            )
        return AdapterResult(
            provider=self.name,
            success=self._success,
            records=records,
            error=None if self._success else "failed",
            latency_ms=1.0,
            raw_sample=None,
            metadata=self._make_metadata(),
        )


def test_orchestrator_falls_back_to_secondary_provider():
    primary = DummyAdapter("Primary", "primary", False, 0)
    secondary = DummyAdapter("Secondary", "secondary", True, 100)

    result = ProviderOrchestrator([primary, secondary]).fetch("stocks", use_cache=False)

    assert result.success is True
    assert result.provider == "Secondary"


def test_compare_equivalent_values_detects_price_spread():
    one = DummyAdapter("One", "primary", True, 100).fetch()
    two = DummyAdapter("Two", "secondary", True, 101).fetch()

    metrics = compare_equivalent_values([one, two])

    assert len(metrics) == 1
    assert metrics[0].key == "symbol:AAPL:stock"
    assert metrics[0].spread_abs == 1
