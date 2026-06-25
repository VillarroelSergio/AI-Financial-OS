from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Dividend:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    ex_date: Optional[date] = None
    payment_date: Optional[date] = None
    amount: float = 0.0
    currency: str = ""
    frequency: str = ""


@dataclass
class ETF:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    isin: str = ""
    ter: Optional[float] = None
    currency: str = ""
    sector_weights: dict[str, float] = field(default_factory=dict)
    country_weights: dict[str, float] = field(default_factory=dict)
    holdings: list[dict] = field(default_factory=list)
    dividend_policy: str = ""


@dataclass
class Fund:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    name: str = ""
    isin: str = ""
    category: str = ""
    currency: str = ""
    return_ytd: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None


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


@dataclass
class Currency:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    pair: str = ""
    base: str = ""
    quote: str = ""
    rate: float = 0.0


@dataclass
class YieldCurve:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    curve_date: Optional[date] = None
    yields: dict[str, float] = field(default_factory=dict)


@dataclass
class EconomicCalendar:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    event: str = ""
    event_date: Optional[datetime] = None
    impact: str = ""
    forecast: Optional[float] = None
    actual: Optional[float] = None
    previous: Optional[float] = None


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


@dataclass
class CorporateAction:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    action_type: str = ""
    effective_date: Optional[date] = None
    description: str = ""


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
