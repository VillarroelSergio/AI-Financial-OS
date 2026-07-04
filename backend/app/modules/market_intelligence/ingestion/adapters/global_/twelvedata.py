"""Twelve Data adapter — AAPL real-time quote."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter, redact_api_key
from app.modules.market_intelligence.ingestion.config import get_api_key
from app.modules.market_intelligence.ingestion.models import AdapterResult, MarketQuote

_BASE_URL = "https://api.twelvedata.com/quote"


class TwelveDataAdapter(BaseAdapter):
    name = "Twelve Data"
    category = "markets"
    region = "Global"
    requires_api_key = True
    api_key_names = ("Twelve Data", "TWELVE_DATA", "TWELVEDATA")

    def fetch(self) -> AdapterResult:
        api_key = (
            get_api_key("Twelve Data")
            or get_api_key("TWELVE_DATA")
            or get_api_key("TWELVEDATA")
        )
        url = f"{_BASE_URL}?symbol=AAPL&apikey={api_key}"
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="Twelve Data")
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
            # {symbol, name, close, percent_change, currency}
            retrieved_at = datetime.now(timezone.utc)
            record = MarketQuote(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=retrieved_at,
                country="US",
                region=self.region,
                confidence_score=1.0,
                symbol=data["symbol"],
                name=data.get("name", data["symbol"]),
                asset_type="stock",
                price=float(data["close"]),
                change_pct=float(data.get("percent_change") or 0.0),
                currency=data.get("currency", "USD"),
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
            raw_sample=data,
            metadata=metadata,
        )

