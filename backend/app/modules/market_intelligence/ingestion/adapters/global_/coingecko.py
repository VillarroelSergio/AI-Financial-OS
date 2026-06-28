"""CoinGecko adapter — top crypto market quotes (no API key required)."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MarketQuote
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter

_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&ids=bitcoin,ethereum,solana"
    "&order=market_cap_desc&per_page=3&page=1"
)


class CoinGeckoAdapter(BaseAdapter):
    name = "CoinGecko"
    category = "markets"
    region = "Global"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_URL, method="api", license="CoinGecko Public")
        t0 = time.time()
        try:
            r = requests.get(_URL, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc),
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        try:
            retrieved_at = datetime.now(timezone.utc)
            records = []
            for item in data:
                records.append(
                    MarketQuote(
                        provider=self.name,
                        source=_URL,
                        retrieved_at=retrieved_at,
                        country="GLOBAL",
                        region=self.region,
                        confidence_score=1.0,
                        symbol=item["symbol"].upper(),
                        name=item["name"],
                        asset_type="crypto",
                        price=float(item["current_price"]),
                        change_pct=float(item.get("price_change_percentage_24h") or 0.0),
                        currency="USD",
                    )
                )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"Parse error: {exc}",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample={"sample": data[0] if data else {}},
            metadata=metadata,
        )
