"""TwelveData provider — free tier, requires API key (TWELVEDATA_API_KEY).

Free tier: 800 req/day, 8 req/min.
Supports: indices, stocks (US + EU), forex, crypto, commodities.
Does NOT support: fundamentals.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import requests

from .base import MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_TWELVEDATA_BASE = "https://api.twelvedata.com"
_REQUEST_TIMEOUT = 10

_SUPPORTED_ASSET_TYPES: frozenset[str] = frozenset([
    "index", "stock", "etf", "forex", "crypto", "commodity", "bond", "volatility"
])


class TwelveDataProvider(MarketDataProvider):
    name = "twelvedata"
    requires_api_key = True

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.environ.get("TWELVEDATA_API_KEY") or ""
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
                "TwelveData no configurado (TWELVEDATA_API_KEY no definida)", is_fallback,
            )

        try:
            resp = requests.get(
                f"{_TWELVEDATA_BASE}/price",
                params={"symbol": provider_symbol, "apikey": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 429:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "rate_limited", is_fallback,
                )

            resp.raise_for_status()
            data = resp.json()

            # TwelveData /price returns {"price": "150.00"} or {"code": 400, "message": "..."}
            if "code" in data and data["code"] != 200:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    f"provider_error: {data.get('message', 'unknown')}", is_fallback,
                )

            raw_price = data.get("price")
            if raw_price is None:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "provider_error: price field missing", is_fallback,
                )

            price = float(raw_price)

            # Fetch previous close for change calculation via /quote endpoint
            prev_close: Optional[float] = None
            market_time: Optional[datetime] = None
            market_open: Optional[bool] = None
            try:
                quote_resp = requests.get(
                    f"{_TWELVEDATA_BASE}/quote",
                    params={"symbol": provider_symbol, "apikey": self.api_key},
                    timeout=_REQUEST_TIMEOUT,
                )
                if quote_resp.status_code == 200:
                    qd = quote_resp.json()
                    close_raw = qd.get("close") or qd.get("previous_close")
                    if close_raw:
                        prev_close = float(close_raw)
                    dt_raw = qd.get("datetime")
                    if dt_raw:
                        try:
                            market_time = datetime.fromisoformat(dt_raw).replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass
                    market_open = qd.get("is_market_open")
            except Exception:
                pass  # prev_close remains None — change fields will be None

            change_absolute: Optional[float] = None
            change_percent: Optional[float] = None
            if prev_close and prev_close != 0:
                change_absolute = round(price - prev_close, 6)
                change_percent = round((price - prev_close) / prev_close * 100, 4)

            freshness = "unknown"
            if market_time:
                age_min = (datetime.now(timezone.utc) - market_time).total_seconds() / 60
                if age_min < 5:
                    freshness = "live"
                elif age_min < 30:
                    freshness = "fresh"
                elif age_min < 120:
                    freshness = "delayed"
                else:
                    freshness = "eod"
            elif price is not None:
                freshness = "delayed"

            market_status = (
                "open" if market_open is True
                else "closed" if market_open is False
                else "unknown"
            )

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
                market_time=market_time,
                market_status=market_status,
                freshness_status=freshness,
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
                "provider_timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning("TwelveDataProvider error for %s: %s", provider_symbol, exc)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"provider_error: {exc}", is_fallback,
            )
