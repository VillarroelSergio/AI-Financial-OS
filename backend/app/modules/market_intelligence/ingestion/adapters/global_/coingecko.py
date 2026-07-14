"""CoinGecko adapter — top crypto market quotes (no API key required)."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    HistoricalPrice,
    MarketQuote,
)

_COINS = {"bitcoin": "bitcoin", "ethereum": "ethereum", "solana": "solana", "xrp": "ripple"}
_BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"

# El runner pide los coins de uno en uno; sin cache son 4 llamadas HTTP seguidas
# y el free tier de CoinGecko devuelve 429 en la última. Una llamada batcheada
# por ventana de 60 s cubre toda la ingesta.
_CACHE_TTL_S = 60.0
_cache: tuple[float, list] | None = None


def _fetch_all_markets() -> list:
    global _cache
    if _cache is not None and (time.time() - _cache[0]) < _CACHE_TTL_S:
        return _cache[1]
    url = (
        f"{_BASE_URL}?vs_currency=usd&ids={','.join(_COINS.values())}"
        f"&order=market_cap_desc&per_page={len(_COINS)}&page=1"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    _cache = (time.time(), data)
    return data


def fetch_crypto_history(catalog_id: str, years: int | None = None) -> list[HistoricalPrice]:
    """MKT-6: serie EOD de cripto desde CoinGecko market_chart. Solo `close` (la API no da
    OHLC diario en free tier). El free tier tope a 365 días → profundidad máx 1 año."""
    coin = _COINS[catalog_id]
    days = min((years or 1) * 365, 365)
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days={days}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    prices = r.json().get("prices") or []
    now = datetime.now(timezone.utc)
    by_date: dict = {}  # último precio del día gana (market_chart trae varios puntos intradía)
    for ts, price in prices:
        by_date[datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()] = price
    out: list[HistoricalPrice] = []
    for d, price in sorted(by_date.items()):
        rec = HistoricalPrice(
            provider="CoinGecko", source=url, retrieved_at=now,
            country="GLOBAL", region="Global", symbol=catalog_id.upper(), date=d,
            open=0.0, high=0.0, low=0.0, close=float(price), volume=0.0,
        )
        rec.currency = "USD"  # HistoricalPrice no tiene el campo; persist lee getattr
        out.append(rec)
    if not out:
        raise ValueError("CoinGecko market_chart returned no prices")
    return out


class CoinGeckoAdapter(BaseAdapter):
    name = "CoinGecko"
    category = "markets"
    region = "Global"
    requires_api_key = False
    supported_indicators = {key: {} for key in _COINS}

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ids = [_COINS[indicator_id]] if indicator_id in _COINS else list(_COINS.values())
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="CoinGecko Public")
        t0 = time.time()
        try:
            data = [item for item in _fetch_all_markets() if item.get("id") in ids]
            latency_ms = (time.time() - t0) * 1000
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
                        source=_BASE_URL,
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

        if not records:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"CoinGecko no devolvió datos para {ids}",
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
