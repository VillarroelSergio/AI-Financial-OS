from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    # Base fields (ProviderRecord composition)
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0

    # NewsItem-specific fields
    title: str = ""
    published_at: Optional[datetime] = None
    source_name: str = ""
    url: str = ""
    category: str = ""        # "macro", "markets", "companies", "crypto", "general"
    related_asset: str = ""   # ticker or asset name if identifiable
