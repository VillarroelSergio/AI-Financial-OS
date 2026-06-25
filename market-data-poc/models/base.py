from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProviderRecord:
    provider: str
    source: str
    retrieved_at: datetime
    country: str        # "ES", "US", "EA", "GLOBAL"
    region: str         # "Spain", "Eurozone", "USA", "Global"
    confidence_score: float = 1.0  # 0.0–1.0


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


@dataclass
class AdapterResult:
    provider: str
    success: bool
    records: list  # list[ProviderRecord]
    error: str | None
    latency_ms: float
    raw_sample: dict | None
    metadata: ProviderMetadata
