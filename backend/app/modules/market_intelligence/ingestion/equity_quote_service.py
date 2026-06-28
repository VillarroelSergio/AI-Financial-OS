"""Lightweight equity quote fetcher over existing MI adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
import yfinance as yf

from app.modules.market_intelligence.ingestion.config import get_api_key


@dataclass
class EquityQuoteResult:
    ticker: str
    price: float
    currency: str
    provider: str
    retrieved_at: datetime
    from_cache: bool = False
    success: bool = True
    error: Optional[str] = None


def _try_finnhub(ticker: str, expected_currency: str) -> Optional[EquityQuoteResult]:
    api_key = get_api_key("Finnhub") or get_api_key("FINNHUB")
    if not api_key:
        return None
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = float(data.get("c") or 0.0)
        if price <= 0:
            return None
        return EquityQuoteResult(
            ticker=ticker,
            price=price,
            currency=expected_currency,
            provider="finnhub",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def _try_alpha_vantage(ticker: str, expected_currency: str) -> Optional[EquityQuoteResult]:
    api_key = get_api_key("Alpha Vantage") or get_api_key("ALPHA_VANTAGE")
    if not api_key:
        return None
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price_str = data.get("Global Quote", {}).get("05. price", "0")
        price = float(price_str or 0)
        if price <= 0:
            return None
        return EquityQuoteResult(
            ticker=ticker,
            price=price,
            currency=expected_currency,
            provider="alpha_vantage",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def _try_yfinance(yfinance_symbol: str) -> Optional[EquityQuoteResult]:
    try:
        t = yf.Ticker(yfinance_symbol)
        info = t.fast_info
        price = info.last_price
        if price is None or price <= 0:
            return None
        currency = (getattr(info, "currency", None) or "USD").upper()
        return EquityQuoteResult(
            ticker=yfinance_symbol,
            price=float(price),
            currency=currency,
            provider="yfinance",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def get_equity_quote(
    ticker: str,
    yfinance_symbol: str,
    expected_currency: str = "USD",
) -> EquityQuoteResult:
    """Fetch equity quote. Tries Finnhub → Alpha Vantage → yfinance."""
    result = (
        _try_finnhub(ticker, expected_currency)
        or _try_alpha_vantage(ticker, expected_currency)
        or _try_yfinance(yfinance_symbol)
    )
    if result:
        return result
    return EquityQuoteResult(
        ticker=ticker,
        price=0.0,
        currency="",
        provider="none",
        retrieved_at=datetime.now(timezone.utc),
        success=False,
        error="All providers failed or returned zero price",
    )
