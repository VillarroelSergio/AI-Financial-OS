"""Modelos de datos del Market Intelligence Layer.

Consolidado desde market-data-poc/models/{base,assets,macro,market,company,news}.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

# ── Base ─────────────────────────────────────────────────────────────────────

@dataclass
class ProviderRecord:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0


@dataclass
class ProviderMetadata:
    name: str
    id: str
    category: str
    region: str
    method: str
    base_url: str
    requires_api_key: bool
    declared_update_frequency: str
    declared_historical_depth_years: int
    license: str
    notes: str = ""
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"


@dataclass
class AdapterResult:
    provider: str
    success: bool
    records: list
    error: Optional[str]
    latency_ms: float
    raw_sample: Optional[dict]
    metadata: ProviderMetadata


class ProviderStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class ProviderHealth:
    provider: str
    status: ProviderStatus
    checked_at: datetime
    latency_ms: float = 0.0
    error: Optional[str] = None


# ── Macro ─────────────────────────────────────────────────────────────────────

@dataclass
class MacroIndicator:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    indicator_id: str = ""
    name: str = ""
    value: float = 0.0
    unit: str = ""
    period: str = ""
    frequency: str = ""


@dataclass
class MacroSeries:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    series_id: str = ""
    name: str = ""
    unit: str = ""
    frequency: str = ""
    observations: list[dict] = field(default_factory=list)


# ── Assets ────────────────────────────────────────────────────────────────────

@dataclass
class CurrencyRate:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    base_currency: str = ""
    quote_currency: str = ""
    rate: float = 0.0
    date: Optional[date] = None
    frequency: str = "daily"


@dataclass
class YieldCurvePoint:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    maturity: str = ""
    yield_value: float = 0.0
    date: Optional[date] = None
    currency: str = ""


@dataclass
class BondYield(YieldCurvePoint):
    issuer: str = ""
    instrument_type: str = "government_bond"


@dataclass
class Commodity:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    price: float = 0.0
    unit: str = ""
    currency: str = "USD"


# ── Market ────────────────────────────────────────────────────────────────────

@dataclass
class MarketQuote:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    asset_type: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    currency: str = "EUR"
    market_status: str = ""


@dataclass
class HistoricalPrice:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    date: Optional[date] = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


# ── Company ───────────────────────────────────────────────────────────────────

@dataclass
class CompanyProfile:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    exchange: str = ""


# ── News ──────────────────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    title: str = ""
    published_at: Optional[datetime] = None
    source_name: str = ""
    url: str = ""
    category: str = ""
    related_asset: str = ""


@dataclass
class MarketNews:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    title: str = ""
    url: str = ""
    published_at: Optional[datetime] = None
    source_name: str = ""
    tickers: list[str] = field(default_factory=list)
