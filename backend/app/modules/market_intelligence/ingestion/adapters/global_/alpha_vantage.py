"""Alpha Vantage adapter — IBM global quote."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter, redact_api_key
from app.modules.market_intelligence.ingestion.config import get_api_key
from app.modules.market_intelligence.ingestion.models import AdapterResult, MarketQuote

_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageAdapter(BaseAdapter):
    name = "Alpha Vantage"
    category = "markets"
    region = "Global"
    requires_api_key = True
    api_key_names = ("Alpha Vantage", "ALPHA_VANTAGE")

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("Alpha Vantage") or get_api_key("ALPHA_VANTAGE")
        url = f"{_BASE_URL}?function=GLOBAL_QUOTE&symbol=IBM&apikey={api_key}"
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="Alpha Vantage")
        t0 = time.time()
        try:
            r = requests.get(url, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=redact_api_key(str(exc), api_key),
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        try:
            quote = data["Global Quote"]
            retrieved_at = datetime.now(timezone.utc)
            record = MarketQuote(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=retrieved_at,
                country="US",
                region=self.region,
                confidence_score=1.0,
                symbol=quote["01. symbol"],
                name=quote["01. symbol"],
                asset_type="stock",
                price=float(quote["05. price"]),
                change_pct=float(quote.get("10. change percent", "0%").replace("%", "") or 0),
                currency="USD",
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"Parse error: {exc}",
                latency_ms=latency_ms,
                raw_sample={"raw": data},
                metadata=metadata,
            )

        return AdapterResult(
            provider=self.name,
            success=True,
            records=[record],
            error=None,
            latency_ms=latency_ms,
            raw_sample={"Global Quote": quote},
            metadata=metadata,
        )

