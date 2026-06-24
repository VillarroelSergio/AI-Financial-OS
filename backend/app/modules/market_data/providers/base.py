"""Base interfaces and normalized models for market data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

FreshnessStatus = Literal[
    "live",     # price ≤5 min old, market open
    "fresh",    # price ≤15 min old
    "delayed",  # price 15–60 min old or provider declares delay
    "eod",      # end-of-day close (market closed)
    "closed",   # market confirmed closed, price is last close
    "stale",    # cache exists but TTL exceeded
    "error",    # provider error, no price available
    "unknown",  # no reliable freshness info
]

AssetType = Literal[
    "index", "stock", "etf", "forex", "crypto",
    "bond", "commodity", "volatility",
]


@dataclass
class MarketQuoteInternal:
    """Normalized internal quote model — all providers return this."""
    internal_symbol: str
    provider_symbol: str
    name: str
    asset_type: str
    category: str
    price: Optional[float]
    currency: str
    change_absolute: Optional[float]
    change_percent: Optional[float]
    source: str                           # provider name
    source_type: str                      # "live", "eod", "delayed", "cache"
    fetched_at: datetime
    market_time: Optional[datetime]
    market_status: str                    # "open", "closed", "unknown"
    freshness_status: FreshnessStatus
    delay_minutes: int
    is_stale: bool
    is_fallback: bool
    confidence_score: float               # 0.0–1.0
    warning: Optional[str]
    sparkline: list[float] = field(default_factory=list)


@dataclass
class MarketCandle:
    internal_symbol: str
    provider_symbol: str
    source: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    currency: str


@dataclass
class CompanyProfile:
    internal_symbol: str
    provider_symbol: str
    source: str
    name: str
    exchange: str
    sector: str
    industry: str
    country: str
    currency: str
    website: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Fundamentals:
    internal_symbol: str
    provider_symbol: str
    source: str
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    eps: Optional[float]
    revenue: Optional[float]
    profit_margin: Optional[float]
    beta: Optional[float]
    updated_at: datetime


class MarketDataProvider(ABC):
    """Abstract base for all market data providers."""

    name: str = "unknown"
    enabled: bool = True
    requires_api_key: bool = False

    @abstractmethod
    def supports(self, asset_type: str, symbol: str) -> bool:
        """Return True if this provider can fetch the given asset."""
        ...

    @abstractmethod
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
        """Fetch a live/recent quote. Must never raise — return error quote on failure."""
        ...

    def get_history(
        self,
        internal_symbol: str,
        provider_symbol: str,
        interval: str = "1d",
        range_: str = "1mo",
    ) -> list[MarketCandle]:
        """Fetch OHLCV history. Optional — providers can leave this as NotImplementedError."""
        raise NotImplementedError

    def get_company_profile(self, internal_symbol: str, provider_symbol: str) -> Optional[CompanyProfile]:
        return None

    def get_fundamentals(self, internal_symbol: str, provider_symbol: str) -> Optional[Fundamentals]:
        return None

    def _error_quote(
        self,
        internal_symbol: str,
        provider_symbol: str,
        name: str,
        asset_type: str,
        category: str,
        currency: str,
        warning: str,
        is_fallback: bool = False,
    ) -> MarketQuoteInternal:
        return MarketQuoteInternal(
            internal_symbol=internal_symbol,
            provider_symbol=provider_symbol,
            name=name,
            asset_type=asset_type,
            category=category,
            price=None,
            currency=currency,
            change_absolute=None,
            change_percent=None,
            source=self.name,
            source_type="error",
            fetched_at=datetime.now(timezone.utc),
            market_time=None,
            market_status="unknown",
            freshness_status="error",
            delay_minutes=0,
            is_stale=False,
            is_fallback=is_fallback,
            confidence_score=0.0,
            warning=warning,
            sparkline=[],
        )
