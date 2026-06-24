"""Stooq provider — primary free data source, no API key required."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Optional

import requests

from .base import AssetType, FreshnessStatus, MarketCandle, MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_STOOQ_BASE = "https://stooq.com"
_REQUEST_TIMEOUT = 12
_MIN_CALL_INTERVAL = 1.0  # seconds between consecutive Stooq calls (be polite)

_last_call_lock = threading.Lock()
_last_call_time: float = 0.0

_SUPPORTED_ASSET_TYPES: set[str] = {
    "index", "forex", "commodity", "volatility", "crypto",
}


def _throttle() -> None:
    global _last_call_time
    with _last_call_lock:
        now = time.monotonic()
        gap = now - _last_call_time
        if gap < _MIN_CALL_INTERVAL:
            time.sleep(_MIN_CALL_INTERVAL - gap)
        _last_call_time = time.monotonic()


def _get(url: str) -> requests.Response:
    _throttle()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,text/csv,*/*",
    }
    return requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)


def _parse_stooq_date(date_str: str, time_str: str = "") -> Optional[datetime]:
    try:
        if time_str and time_str != "N/A":
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class StooqProvider(MarketDataProvider):
    name = "stooq"
    enabled = True
    requires_api_key = False

    def supports(self, asset_type: str, symbol: str) -> bool:
        return asset_type in _SUPPORTED_ASSET_TYPES

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
            # Get daily history for last 10 trading days → gives current + prev close + sparkline
            history = self._fetch_history_days(provider_symbol, n_days=14)
            if not history or len(history) < 1:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "Stooq: sin datos disponibles", is_fallback,
                )

            last = history[-1]
            prev = history[-2] if len(history) >= 2 else None

            price = last.get("Close")
            if price is None or price == 0:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "Stooq: precio no disponible (N/A)", is_fallback,
                )

            prev_close = prev["Close"] if prev else None
            change_absolute: Optional[float] = None
            change_percent: Optional[float] = None
            if prev_close and prev_close != 0:
                change_absolute = round(price - prev_close, 6)
                change_percent = round((price - prev_close) / prev_close * 100, 4)

            market_time = _parse_stooq_date(last.get("Date", ""), last.get("Time", ""))

            # Freshness: Stooq provides EOD data for most assets
            freshness: FreshnessStatus = "eod"
            market_status = "closed"

            sparkline = [r["Close"] for r in history if r.get("Close")]

            # Try to determine if today's data is fresh
            if market_time:
                age_minutes = (datetime.now(timezone.utc) - market_time).total_seconds() / 60
                if age_minutes < 30:
                    freshness = "fresh"
                    market_status = "unknown"
                elif age_minutes < 240:
                    freshness = "delayed"

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=name,
                asset_type=asset_type,
                category=category,
                price=float(price),
                currency=currency,
                change_absolute=change_absolute,
                change_percent=change_percent,
                source=self.name,
                source_type="eod",
                fetched_at=datetime.now(timezone.utc),
                market_time=market_time,
                market_status=market_status,
                freshness_status=freshness,
                delay_minutes=0,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.85,
                warning=None,
                sparkline=sparkline,
            )
        except requests.exceptions.Timeout:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "Stooq: timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning("StooqProvider error for %s: %s", provider_symbol, exc)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"Stooq: {exc}", is_fallback,
            )

    def _fetch_history_days(self, symbol: str, n_days: int = 14) -> list[dict]:
        """Fetch last n_days of daily EOD data from Stooq CSV endpoint."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days * 2)  # 2× for weekends/holidays
        d1 = start_date.strftime("%Y%m%d")
        d2 = end_date.strftime("%Y%m%d")
        url = f"{_STOOQ_BASE}/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d"

        resp = _get(url)
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}")

        text = resp.text.strip()
        if not text or "No data" in text or text.startswith("<!"):
            return []

        lines = text.splitlines()
        if len(lines) < 2:
            return []

        # Expected header: Date,Open,High,Low,Close,Volume
        header = [h.strip() for h in lines[0].split(",")]
        rows: list[dict] = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) < len(header):
                continue
            row = dict(zip(header, parts))
            try:
                close_str = row.get("Close", "N/A").strip()
                if close_str in ("N/A", "", "0"):
                    continue
                rows.append({
                    "Date": row.get("Date", "").strip(),
                    "Time": row.get("Time", "").strip(),
                    "Close": float(close_str),
                    "Open": float(row.get("Open", 0) or 0),
                    "High": float(row.get("High", 0) or 0),
                    "Low": float(row.get("Low", 0) or 0),
                    "Volume": float(row.get("Volume", 0) or 0),
                })
            except (ValueError, KeyError):
                continue

        # Return last n_days rows
        return rows[-n_days:] if rows else []

    def get_history(
        self,
        internal_symbol: str,
        provider_symbol: str,
        interval: str = "1d",
        range_: str = "1mo",
    ) -> list[MarketCandle]:
        range_map = {"1w": 10, "1mo": 35, "3mo": 100, "1y": 370, "5y": 1830}
        n_days = range_map.get(range_, 35)
        rows = self._fetch_history_days(provider_symbol, n_days=n_days)
        candles = []
        for r in rows:
            dt = _parse_stooq_date(r["Date"])
            if dt:
                candles.append(MarketCandle(
                    internal_symbol=internal_symbol,
                    provider_symbol=provider_symbol,
                    source=self.name,
                    timestamp=dt,
                    open=r["Open"],
                    high=r["High"],
                    low=r["Low"],
                    close=r["Close"],
                    volume=r.get("Volume"),
                    currency="",  # not returned by Stooq
                ))
        return candles
