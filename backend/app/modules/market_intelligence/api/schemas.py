"""Pydantic output schemas para la Market Intelligence API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MacroDataPoint(BaseModel):
    catalog_item_id: str
    indicator_id: Optional[str] = None
    country: Optional[str] = None
    period: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class MacroSnapshotOut(BaseModel):
    spain: list[MacroDataPoint] = []
    eurozone: list[MacroDataPoint] = []
    usa: list[MacroDataPoint] = []
    generated_at: str
    warnings: list[str] = []


class QuoteOut(BaseModel):
    catalog_item_id: str
    symbol: Optional[str] = None
    asset_type: Optional[str] = None
    price: Optional[float] = None
    change_pct: Optional[float] = None
    currency: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class MarketSnapshotOut(BaseModel):
    indices: list[QuoteOut] = []
    crypto: list[QuoteOut] = []
    commodities: list[QuoteOut] = []
    generated_at: str
    warnings: list[str] = []


class ForexRateOut(BaseModel):
    catalog_item_id: str
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    rate: Optional[float] = None
    date: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class ForexSnapshotOut(BaseModel):
    rates: list[ForexRateOut] = []
    generated_at: str
    warnings: list[str] = []


class BondYieldOut(BaseModel):
    catalog_item_id: str
    country: Optional[str] = None
    maturity: Optional[str] = None
    yield_value: Optional[float] = None
    date: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class BondSnapshotOut(BaseModel):
    yields: list[BondYieldOut] = []
    generated_at: str
    warnings: list[str] = []


class NewsItemOut(BaseModel):
    id: str
    title: Optional[str] = None
    published_at: Optional[str] = None
    source_name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    provider_id: Optional[str] = None


class NewsSnapshotOut(BaseModel):
    items: list[NewsItemOut] = []
    generated_at: str


class AiDatasheetOut(BaseModel):
    generated_at: str
    quality_score: float = 1.0
    scope: str = "daily"
    macro: dict = {}
    markets: dict = {}
    forex: dict = {}
    bonds: dict = {}
    news: list = []
    sources: list[str] = []
    warnings: list[str] = []


class MarketIntelligenceSnapshotOut(BaseModel):
    generated_at: str
    macro: MacroSnapshotOut
    market: MarketSnapshotOut
    forex: ForexSnapshotOut
    bonds: BondSnapshotOut
    news: NewsSnapshotOut


class ImpactComparative(BaseModel):
    id: str
    title: str
    description: str
    market_value: Optional[float] = None
    market_label: str
    personal_value: Optional[float] = None
    personal_label: str
    signal: str  # "positive" | "negative" | "neutral" | "warning"
    signal_text: str
    source_ids: list[str] = []


class PersonalImpactOut(BaseModel):
    generated_at: str
    comparatives: list[ImpactComparative] = []
    warnings: list[str] = []
