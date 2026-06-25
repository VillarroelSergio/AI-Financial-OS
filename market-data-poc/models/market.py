from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class MarketQuote:
    # Base fields (from ProviderRecord, via composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str        # "ES", "US", "EA", "GLOBAL"
    region: str         # "Spain", "Eurozone", "USA", "Global"
    confidence_score: float = 1.0

    # MarketQuote-specific fields
    symbol: str = ""
    name: str = ""
    asset_type: str = ""   # "stock", "etf", "index", "forex", "crypto", "bond"
    price: float = 0.0
    change_pct: float = 0.0
    currency: str = "EUR"
    market_status: str = ""  # "open", "closed", "pre", "after"


@dataclass
class HistoricalPrice:
    # Base fields (from ProviderRecord, via composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # HistoricalPrice-specific fields
    symbol: str = ""
    date: Optional[date] = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
