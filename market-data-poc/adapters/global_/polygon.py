"""Polygon adapter - previous close for AAPL using the freemium API."""
import time
from datetime import datetime, timezone

import requests

from adapters.base import BaseAdapter
from config.settings import get_api_key
from models.base import AdapterResult
from models.market import MarketQuote

_BASE_URL = "https://api.polygon.io"


class PolygonAdapter(BaseAdapter):
    name = "Polygon"
    category = "markets"
    region = "Global"
    requires_api_key = True
    api_key_names = ("POLYGON",)
    capabilities = ("stocks", "etf", "forex", "crypto", "dividends", "earnings", "intraday", "realtime")
    priority = "primary"

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("POLYGON")
        metadata = self._make_metadata(
            id="polygon",
            base_url=_BASE_URL,
            method="api",
            license="freemium",
            declared_update_frequency="realtime",
            declared_historical_depth_years=20,
            notes="Freemium market data API.",
        )
        t0 = time.perf_counter()
        url = f"{_BASE_URL}/v2/aggs/ticker/AAPL/prev"
        try:
            response = requests.get(
                url,
                params={"adjusted": "true", "apiKey": api_key},
                timeout=10,
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            result = (data.get("results") or [])[0]
            record = MarketQuote(
                provider=self.name,
                source=url,
                retrieved_at=datetime.now(timezone.utc),
                country="US",
                region=self.region,
                confidence_score=0.95,
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                price=float(result["c"]),
                change_pct=0.0,
                currency="USD",
                market_status="previous_close",
            )
            return AdapterResult(
                provider=self.name,
                success=True,
                records=[record],
                error=None,
                latency_ms=latency_ms,
                raw_sample={"ticker": data.get("ticker"), "resultsCount": data.get("resultsCount")},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=_redact_api_key(str(exc), api_key),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None,
                metadata=metadata,
            )


def _redact_api_key(value: str, api_key: str | None) -> str:
    return value.replace(api_key, "***") if api_key else value


Adapter = PolygonAdapter
