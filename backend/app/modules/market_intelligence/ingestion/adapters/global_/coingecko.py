"""CoinGecko adapter — top crypto market quotes (no API key required)."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MarketQuote
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter

_COINS = {"bitcoin": "bitcoin", "ethereum": "ethereum", "solana": "solana", "xrp": "ripple"}
_BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"


class CoinGeckoAdapter(BaseAdapter):
    name = "CoinGecko"
    category = "markets"
    region = "Global"
    requires_api_key = False
    supported_indicators = {key: {} for key in _COINS}

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ids = [_COINS[indicator_id]] if indicator_id in _COINS else list(_COINS.values())
        url = (
            f"{_BASE_URL}?vs_currency=usd&ids={','.join(ids)}"
            f"&order=market_cap_desc&per_page={len(ids)}&page=1"
        )
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="CoinGecko Public")
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
                        source=url,
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
