"""Alpha Vantage provider — optional, requires free API key (ALPHA_VANTAGE_API_KEY).

Free tier: 25 requests/day (standard), 500/day with email signup.
Supports: stocks, forex, crypto, indices (via ETF proxies).
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from app.core.config import settings

from .base import MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_AV_BASE = "https://www.alphavantage.co/query"
_REQUEST_TIMEOUT = 15

# Rate limiter state (free tier: max ~5 req/min to be safe)
_call_times: list[float] = []
_rate_lock = threading.Lock()
_MAX_CALLS_PER_MINUTE = 5


def _check_rate_limit() -> bool:
    """Return True if we can make a call, False if rate limited."""
    now = time.monotonic()
    with _rate_lock:
        # Remove calls older than 60 seconds
        _call_times[:] = [t for t in _call_times if now - t < 60]
        if len(_call_times) >= _MAX_CALLS_PER_MINUTE:
            return False
        _call_times.append(now)
        return True


_SUPPORTED_ASSET_TYPES: set[str] = {
    "stock", "etf", "forex", "crypto",
}


class AlphaVantageProvider(MarketDataProvider):
    name = "alphavantage"
    requires_api_key = True

    def __init__(self) -> None:
        self.api_key: Optional[str] = settings.ALPHA_VANTAGE_API_KEY.strip()
        self.enabled: bool = bool(self.api_key)

    def supports(self, asset_type: str, symbol: str) -> bool:
        return self.enabled and asset_type in _SUPPORTED_ASSET_TYPES

    def get_quote(
        self,
        internal_symbol: str,
        provider_symbol: str,
        name: str,
        asset_type: str,
        category: str,
        currency: str,
        is_fallback: bool = False,
    ) -> MarketQuoteInternal:
        if not self.enabled:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "AlphaVantage no configurado (ALPHA_VANTAGE_API_KEY no definida)", is_fallback,
            )

        if not _check_rate_limit():
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "AlphaVantage: límite de llamadas alcanzado (free tier)", is_fallback,
            )

        try:
            if asset_type == "forex":
                data = self._get_forex_quote(provider_symbol)
            elif asset_type == "crypto":
                data = self._get_crypto_quote(provider_symbol, currency)
            else:
                data = self._get_global_quote(provider_symbol)

            if data is None:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "AlphaVantage: sin datos", is_fallback,
                )

            price = data.get("price")
            change_absolute = data.get("change_absolute")
            change_percent = data.get("change_percent")

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=name,
                asset_type=asset_type,
                category=category,
                price=price,
                currency=currency,
                change_absolute=change_absolute,
                change_percent=change_percent,
                source=self.name,
                source_type="delayed",
                fetched_at=datetime.now(timezone.utc),
                market_time=None,
                market_status="unknown",
                freshness_status="delayed",
                delay_minutes=15,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.80,
                warning=None,
                sparkline=[],
            )
        except requests.exceptions.Timeout:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "AlphaVantage: timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning(
                "AlphaVantageProvider error for %s: %s",
                provider_symbol,
                type(exc).__name__,
            )
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"AlphaVantage: {exc}", is_fallback,
            )

    def _get_global_quote(self, symbol: str) -> Optional[dict]:
        resp = requests.get(
            _AV_BASE,
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()

        if "Note" in body or "Information" in body:
            raise ValueError("AlphaVantage free tier rate limit reached")

        gq = body.get("Global Quote", {})
        price_str = gq.get("05. price")
        if not price_str:
            return None

        price = float(price_str)
        change_str = gq.get("09. change", "0")
        pct_str = gq.get("10. change percent", "0%").replace("%", "")
        return {
            "price": price,
            "change_absolute": float(change_str) if change_str else None,
            "change_percent": float(pct_str) if pct_str else None,
        }

    def _get_forex_quote(self, pair: str) -> Optional[dict]:
        # pair format: "EURUSD"
        if len(pair) < 6:
            return None
        from_cur = pair[:3].upper()
        to_cur = pair[3:6].upper()
        resp = requests.get(
            _AV_BASE,
            params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_cur,
                "to_currency": to_cur,
                "apikey": self.api_key,
            },
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        if "Note" in body or "Information" in body:
            raise ValueError("AlphaVantage free tier rate limit reached")
        rate_info = body.get("Realtime Currency Exchange Rate", {})
        price_str = rate_info.get("5. Exchange Rate")
        if not price_str:
            return None
        return {"price": float(price_str), "change_absolute": None, "change_percent": None}

    def _get_crypto_quote(self, symbol: str, currency: str) -> Optional[dict]:
        # symbol format: "BTCUSD" → market="USD", coin="BTC"
        coin = symbol.replace("USD", "").replace("EUR", "")
        market = currency if currency else "USD"
        resp = requests.get(
            _AV_BASE,
            params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": coin,
                "to_currency": market,
                "apikey": self.api_key,
            },
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        if "Note" in body or "Information" in body:
            raise ValueError("AlphaVantage free tier rate limit reached")
        rate_info = body.get("Realtime Currency Exchange Rate", {})
        price_str = rate_info.get("5. Exchange Rate")
        if not price_str:
            return None
        return {"price": float(price_str), "change_absolute": None, "change_percent": None}
