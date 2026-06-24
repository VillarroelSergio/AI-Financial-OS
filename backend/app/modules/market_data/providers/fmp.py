"""Financial Modeling Prep provider — optional, requires free API key (FMP_API_KEY).

Free tier: 250 requests/day, end-of-day data only on free plan for most endpoints.
Supports: stocks, ETFs, company profiles, fundamentals, ratios.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from .base import CompanyProfile, Fundamentals, MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_FMP_BASE = "https://financialmodelingprep.com/api/v3"
_REQUEST_TIMEOUT = 15

_call_times: list[float] = []
_rate_lock = threading.Lock()
_MAX_CALLS_PER_DAY = 230  # buffer below 250
_calls_today = 0
_calls_today_lock = threading.Lock()
_calls_date = ""


def _check_rate_limit() -> bool:
    global _calls_today, _calls_date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _calls_today_lock:
        if _calls_date != today:
            _calls_date = today
            _calls_today = 0
        if _calls_today >= _MAX_CALLS_PER_DAY:
            return False
        _calls_today += 1
        return True


_SUPPORTED_ASSET_TYPES: set[str] = {
    "stock", "etf",
}


class FMPProvider(MarketDataProvider):
    name = "fmp"
    requires_api_key = True

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.environ.get("FMP_API_KEY") or ""
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
                "FMP no configurado (FMP_API_KEY no definida)", is_fallback,
            )

        if not _check_rate_limit():
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "FMP: límite diario alcanzado (free tier, 250/día)", is_fallback,
            )

        try:
            resp = requests.get(
                f"{_FMP_BASE}/quote/{provider_symbol}",
                params={"apikey": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 403:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "FMP: acceso denegado (límite free tier o símbolo no disponible)", is_fallback,
                )

            resp.raise_for_status()
            items = resp.json()
            if not items:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "FMP: sin datos para este símbolo", is_fallback,
                )

            data = items[0]
            price = data.get("price")
            if price is None:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "FMP: precio no disponible", is_fallback,
                )

            change_absolute: Optional[float] = data.get("change")
            change_percent: Optional[float] = data.get("changesPercentage")

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=data.get("name", name),
                asset_type=asset_type,
                category=category,
                price=float(price),
                currency=data.get("currency", currency),
                change_absolute=float(change_absolute) if change_absolute is not None else None,
                change_percent=float(change_percent) if change_percent is not None else None,
                source=self.name,
                source_type="eod",
                fetched_at=datetime.now(timezone.utc),
                market_time=None,
                market_status="unknown",
                freshness_status="eod",
                delay_minutes=0,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.82,
                warning=None,
                sparkline=[],
            )
        except requests.exceptions.Timeout:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "FMP: timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning("FMPProvider error for %s: %s", provider_symbol, exc)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"FMP: {exc}", is_fallback,
            )

    def get_company_profile(
        self, internal_symbol: str, provider_symbol: str
    ) -> Optional[CompanyProfile]:
        if not self.enabled or not _check_rate_limit():
            return None
        try:
            resp = requests.get(
                f"{_FMP_BASE}/profile/{provider_symbol}",
                params={"apikey": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            items = resp.json()
            if not items:
                return None
            data = items[0]
            return CompanyProfile(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                source=self.name,
                name=data.get("companyName", ""),
                exchange=data.get("exchangeShortName", ""),
                sector=data.get("sector", ""),
                industry=data.get("industry", ""),
                country=data.get("country", ""),
                currency=data.get("currency", ""),
                website=data.get("website"),
                description=data.get("description"),
            )
        except Exception as exc:
            logger.warning("FMPProvider profile error for %s: %s", provider_symbol, exc)
            return None

    def get_fundamentals(
        self, internal_symbol: str, provider_symbol: str
    ) -> Optional[Fundamentals]:
        if not self.enabled or not _check_rate_limit():
            return None
        try:
            resp = requests.get(
                f"{_FMP_BASE}/ratios-ttm/{provider_symbol}",
                params={"apikey": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            items = resp.json()
            if not items:
                return None
            data = items[0]
            return Fundamentals(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                source=self.name,
                market_cap=None,
                pe_ratio=data.get("priceEarningsRatioTTM"),
                dividend_yield=data.get("dividendYieldTTM"),
                eps=data.get("earningsPerShareTTM") if hasattr(data, "get") else None,
                revenue=None,
                profit_margin=data.get("netProfitMarginTTM"),
                beta=None,
                updated_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.warning("FMPProvider fundamentals error for %s: %s", provider_symbol, exc)
            return None
