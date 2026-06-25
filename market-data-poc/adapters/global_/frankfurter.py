"""Frankfurter adapter - free ECB-backed FX rates."""
import time
from datetime import datetime, timezone

import requests

from adapters.base import BaseAdapter
from models.assets import CurrencyRate
from models.base import AdapterResult

_BASE_URL = "https://api.frankfurter.app"
_PAIRS = ("USD", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY")
_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}


class FrankfurterAdapter(BaseAdapter):
    name = "Frankfurter"
    category = "markets"
    region = "Global"
    requires_api_key = False
    capabilities = ("currency", "forex", "historical")
    priority = "primary"

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(
            id="frankfurter",
            base_url=_BASE_URL,
            method="api",
            license="open",
            declared_update_frequency="daily",
            declared_historical_depth_years=25,
            notes="Free exchange-rate API based on ECB reference rates.",
        )
        t0 = time.perf_counter()
        url = f"{_BASE_URL}/latest"
        params = {"from": "EUR", "to": ",".join(_PAIRS)}
        try:
            response = requests.get(url, params=params, headers=_HEADERS, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            obs_date = datetime.fromisoformat(data["date"]).date()
            records = [
                CurrencyRate(
                    provider=self.name,
                    source=response.url,
                    retrieved_at=datetime.now(timezone.utc),
                    country="GLOBAL",
                    region=self.region,
                    confidence_score=0.95,
                    base_currency=data.get("base", "EUR"),
                    quote_currency=quote,
                    rate=float(rate),
                    date=obs_date,
                    frequency="daily",
                )
                for quote, rate in (data.get("rates") or {}).items()
            ]
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "Frankfurter response contained no rates",
                latency_ms=latency_ms,
                raw_sample={"date": data.get("date"), "rates": list((data.get("rates") or {}).keys())},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None,
                metadata=metadata,
            )


Adapter = FrankfurterAdapter
