"""Schemas del catálogo de datos de mercado."""
from __future__ import annotations

from dataclasses import dataclass


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
