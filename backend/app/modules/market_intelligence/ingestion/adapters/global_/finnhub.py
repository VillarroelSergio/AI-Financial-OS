"""Finnhub adapter — AAPL real-time quote."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import AdapterResult
from app.modules.market_intelligence.ingestion.models import MarketQuote
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter, redact_api_key
from app.modules.market_intelligence.ingestion.config import get_api_key

_BASE_URL = "https://finnhub.io/api/v1/quote"


class FinnhubAdapter(BaseAdapter):
    name = "Finnhub"
    category = "markets"
    region = "Global"
    requires_api_key = True
    api_key_names = ("Finnhub", "FINNHUB")

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("Finnhub") or get_api_key("FINNHUB")
        url = f"{_BASE_URL}?symbol=AAPL&token={api_key}"
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="Finnhub")
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
            # {c: current, d: change, dp: change_pct, h: high, l: low, o: open, pc: prev_close}
            retrieved_at = datetime.now(timezone.utc)
            record = MarketQuote(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=retrieved_at,
                country="US",
                region=self.region,
                confidence_score=1.0,
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                price=float(data["c"]),
                change_pct=float(data.get("dp") or 0.0),
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
            raw_sample=data,
            metadata=metadata,
        )

