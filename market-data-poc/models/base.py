from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"


@dataclass
class AdapterResult:
    provider: str
    success: bool
    records: list  # list[ProviderRecord]
    error: str | None
    latency_ms: float
    raw_sample: dict | None
    metadata: ProviderMetadata


class ProviderStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class ProviderPriority(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FALLBACK = "fallback"
    SCRAPER = "scraper"


@dataclass
class ProviderCapability:
    provider_id: str
    assets: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    datasets: tuple[str, ...] = ()
    supports_historical: bool = False
    supports_intraday: bool = False
    supports_realtime: bool = False


@dataclass
class ProviderCoverage:
    provider_id: str
    region: str
    asset_type: str
    historical_depth_years: int = 0
    frequency: str = "unknown"
    gaps: tuple[str, ...] = ()


@dataclass
class ProviderHealth:
    provider: str
    status: ProviderStatus
    checked_at: datetime
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class ProviderScore:
    provider: str
    availability: float
    latency: float
    coverage: float
    historical_depth: float
    quality: float
    frequency: float
    reliability: float
    total: float
