"""Finnhub provider — optional, requires free API key (FINNHUB_API_KEY).

Free tier: 60 API calls/minute.
Supports: US stocks, forex (limited), crypto, company profiles, fundamentals.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from app.core.config import settings

from .base import CompanyProfile, Fundamentals, MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_FINNHUB_BASE = "https://finnhub.io/api/v1"
_REQUEST_TIMEOUT = 12

_call_times: list[float] = []
_rate_lock = threading.Lock()
_MAX_CALLS_PER_MINUTE = 55  # leave buffer below 60


def _check_rate_limit() -> bool:
    now = time.monotonic()
    with _rate_lock:
        _call_times[:] = [t for t in _call_times if now - t < 60]
        if len(_call_times) >= _MAX_CALLS_PER_MINUTE:
            return False
        _call_times.append(now)
        return True


_SUPPORTED_ASSET_TYPES: set[str] = {
    "stock", "etf", "forex", "crypto",
}


class FinnhubProvider(MarketDataProvider):
    name = "finnhub"
    requires_api_key = True

    def __init__(self) -> None:
        self.api_key: Optional[str] = settings.FINNHUB_API_KEY.strip()
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
                "Finnhub no configurado (FINNHUB_API_KEY no definida)", is_fallback,
            )

        if not _check_rate_limit():
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "Finnhub: rate limit alcanzado (free tier, 60/min)", is_fallback,
            )

        try:
            resp = requests.get(
                f"{_FINNHUB_BASE}/quote",
                params={"symbol": provider_symbol, "token": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 429:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "Finnhub: 429 rate limit", is_fallback,
                )

            resp.raise_for_status()
            data = resp.json()

            price = data.get("c")  # current price
            prev_close = data.get("pc")  # previous close
            change_absolute: Optional[float] = data.get("d")   # change
            change_percent: Optional[float] = data.get("dp")   # change percent

            if not price:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "Finnhub: precio no disponible", is_fallback,
                )

            market_time: Optional[datetime] = None
            ts = data.get("t")
            if ts:
                try:
                    market_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                except Exception:
                    pass

            freshness = "unknown"
            if market_time:
                age_minutes = (datetime.now(timezone.utc) - market_time).total_seconds() / 60
                if age_minutes < 5:
                    freshness = "live"
                elif age_minutes < 30:
                    freshness = "fresh"
                elif age_minutes < 120:
                    freshness = "delayed"
                else:
                    freshness = "eod"

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=name,
                asset_type=asset_type,
                category=category,
                price=float(price),
                currency=currency,
                change_absolute=float(change_absolute) if change_absolute is not None else None,
                change_percent=float(change_percent) if change_percent is not None else None,
                source=self.name,
                source_type="live",
                fetched_at=datetime.now(timezone.utc),
                market_time=market_time,
                market_status="unknown",
                freshness_status=freshness,
                delay_minutes=0,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.90,
                warning=None,
                sparkline=[],
            )
        except requests.exceptions.Timeout:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "Finnhub: timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning("FinnhubProvider error for %s: %s", provider_symbol, type(exc).__name__)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"Finnhub: {exc}", is_fallback,
            )

    def get_company_profile(
        self, internal_symbol: str, provider_symbol: str
    ) -> Optional[CompanyProfile]:
        if not self.enabled or not _check_rate_limit():
            return None
        try:
            resp = requests.get(
                f"{_FINNHUB_BASE}/stock/profile2",
                params={"symbol": provider_symbol, "token": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            return CompanyProfile(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                source=self.name,
                name=data.get("name", ""),
                exchange=data.get("exchange", ""),
                sector="",
                industry=data.get("finnhubIndustry", ""),
                country=data.get("country", ""),
                currency=data.get("currency", ""),
                website=data.get("weburl"),
                description=None,
            )
        except Exception as exc:
            logger.warning("FinnhubProvider profile error for %s: %s", provider_symbol, exc)
            return None

    def get_fundamentals(
        self, internal_symbol: str, provider_symbol: str
    ) -> Optional[Fundamentals]:
        if not self.enabled or not _check_rate_limit():
            return None
        try:
            resp = requests.get(
                f"{_FINNHUB_BASE}/stock/metric",
                params={"symbol": provider_symbol, "metric": "all", "token": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json().get("metric", {})
            return Fundamentals(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                source=self.name,
                market_cap=data.get("marketCapitalization"),
                pe_ratio=data.get("peNormalizedAnnual"),
                dividend_yield=data.get("dividendYieldIndicatedAnnual"),
                eps=data.get("epsNormalizedAnnual"),
                revenue=data.get("revenuePerShareAnnual"),
                profit_margin=data.get("netProfitMarginAnnual"),
                beta=data.get("beta"),
                updated_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.warning("FinnhubProvider fundamentals error for %s: %s", provider_symbol, exc)
            return None
