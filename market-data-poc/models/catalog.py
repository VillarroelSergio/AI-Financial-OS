from dataclasses import dataclass
from models.base import AdapterResult


@dataclass
class CatalogIndicator:
    id: str
    name: str
    category: str
    subcategory: str
    country: str
    region: str
    frequency: str
    priority: str
    dashboard: bool
    ai: bool
    historical: str
    retention: str
    unit: str
    description: str
    provider_primary: str
    provider_secondary: str | None = None
    provider_fallback: str | None = None


@dataclass
class CatalogFetchResult:
    indicator: CatalogIndicator
    adapter_result: AdapterResult
    provider_used: str
    fallback_used: bool
    catalog_id: str
