from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class MacroIndicator:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # MacroIndicator-specific fields
    indicator_id: str = ""
    name: str = ""
    value: float = 0.0
    unit: str = ""
    period: str = ""       # e.g. "2024-Q1", "2024-01"
    frequency: str = ""    # "monthly", "quarterly", "yearly"


@dataclass
class EconomicEvent:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # EconomicEvent-specific fields
    event_name: str = ""
    date: Optional[date] = None
    forecast: Optional[float] = None
    actual: Optional[float] = None
    previous: Optional[float] = None
    impact: str = ""       # "low", "medium", "high"
