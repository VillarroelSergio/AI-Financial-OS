"""Yahoo Finance provider — primary source, no API key required.

Wraps yfinance. Universal coverage. Data freshness is not guaranteed (delayed).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from .base import MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)


class YahooFinanceProvider(MarketDataProvider):
    name = "yahoo"
    enabled = True
    requires_api_key = False

    def supports(self, asset_type: str, symbol: str) -> bool:
        # Yahoo Finance is the catch-all fallback
        return True

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
        try:
            ticker = yf.Ticker(provider_symbol)
            fast = ticker.fast_info
            price = fast.last_price

            prev_close = fast.previous_close
            change_absolute: Optional[float] = None
            change_percent: Optional[float] = None
            if price is not None and prev_close and prev_close != 0:
                change_absolute = round(float(price - prev_close), 6)
                change_percent = round(float((price - prev_close) / prev_close * 100), 4)

            try:
                hist = ticker.history(period="1d", interval="5m")
                sparkline = (
                    [float(v) for v in hist["Close"].dropna().tolist()]
                    if not hist.empty
                    else []
                )
            except Exception:
                sparkline = []

            try:
                market_state = getattr(fast, "market_state", None)
                market_open = market_state == "REGULAR" if market_state else None
            except Exception:
                market_open = None

            market_status = (
                "open" if market_open is True
                else "closed" if market_open is False
                else "unknown"
            )

            freshness = "unknown"
            if price is not None:
                # yfinance doesn't reliably tell us how fresh the data is;
                # we mark it "delayed" to be conservative
                freshness = "delayed"

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=name,
                asset_type=asset_type,
                category=category,
                price=float(price) if price is not None else None,
                currency=currency,
                change_absolute=change_absolute,
                change_percent=change_percent,
                source=self.name,
                source_type="delayed",
                fetched_at=datetime.now(timezone.utc),
                market_time=None,
                market_status=market_status,
                freshness_status=freshness,
                delay_minutes=15,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.70,
                warning="Dato retrasado (Yahoo Finance). Puede no reflejar el precio actual." if price is not None else None,
                sparkline=sparkline,
            )
        except Exception as exc:
            logger.warning("YahooFinanceProvider error for %s: %s", provider_symbol, exc)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"Yahoo: {exc}", is_fallback=is_fallback,
            )
