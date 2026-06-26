from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class CompanyProfile:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # CompanyProfile-specific fields
    symbol: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    exchange: str = ""


@dataclass
class CompanyMetric:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # CompanyMetric-specific fields
    symbol: str = ""
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    revenue: Optional[float] = None


@dataclass
class Dividend:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # Dividend-specific fields
    symbol: str = ""
    ex_date: Optional[date] = None
    pay_date: Optional[date] = None
    amount: float = 0.0
    currency: str = "EUR"
