"""Pydantic output schemas para la Market Intelligence API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MacroHistoryPoint(BaseModel):
    period: str
    value: float


class MacroDataPoint(BaseModel):
    catalog_item_id: str
    indicator_id: Optional[str] = None
    country: Optional[str] = None
    period: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0
    data_status: str = "ok"
    retrieved_at: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    subcategory: Optional[str] = None
    frequency: Optional[str] = None
    priority: Optional[str] = None
    previous_value: Optional[float] = None
    delta: Optional[float] = None
    history: list[MacroHistoryPoint] = []


class MacroSnapshotOut(BaseModel):
    status: str = "empty"
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
    data_status: str = "ok"
    observed_at: Optional[str] = None
    display_name: Optional[str] = None
    display_country: Optional[str] = None


class MarketSnapshotOut(BaseModel):
    status: str = "empty"
    indices: list[QuoteOut] = []
    crypto: list[QuoteOut] = []
    commodities: list[QuoteOut] = []
    generated_at: str
    warnings: list[str] = []
    quality_score: float = 0.0


class ForexRateOut(BaseModel):
    catalog_item_id: str
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    rate: Optional[float] = None
    date: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0
    data_status: str = "ok"


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
    data_status: str = "ok"


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


class HistoryPointOut(BaseModel):
    date: str
    close: float
    volume: Optional[int] = None


class HistoryStatsOut(BaseModel):
    previous_close: Optional[float] = None
    open: Optional[float] = None
    day_low: Optional[float] = None
    day_high: Optional[float] = None
    week52_low: Optional[float] = None
    week52_high: Optional[float] = None
    range_change_pct: Optional[float] = None
    volume: Optional[int] = None


class InstrumentHistoryOut(BaseModel):
    """MKT-6: serie histórica EOD de un instrumento. `available_ranges` se deriva del
    span real de la serie (regla ECO-2: no se ofrecen rangos que la serie no cubre)."""
    indicator_code: str
    name: Optional[str] = None
    region: Optional[str] = None
    currency: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0
    last_updated: Optional[str] = None
    granularity: str = "eod"
    available_ranges: list[str] = []
    range: str = "max"
    stats: HistoryStatsOut = HistoryStatsOut()
    series: list[HistoryPointOut] = []


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
    signal: str  # "positive" | "negative" | "neutral" | "warning" | "no_data"
    signal_text: str
    source_ids: list[str] = []


class PersonalImpactOut(BaseModel):
    generated_at: str
    comparatives: list[ImpactComparative] = []
    warnings: list[str] = []


# ── ECO-6: overview agregado (1 request en vez de 5; agrupado temático en backend) ──

class ThemedGroupOut(BaseModel):
    theme: str
    indicators: list[MacroDataPoint] = []


class RegionBlockOut(BaseModel):
    themes: list[ThemedGroupOut] = []


class EconomyOverviewOut(BaseModel):
    status: str = "empty"
    generated_at: str
    warnings: list[str] = []
    global_indicators: list[MacroDataPoint] = []
    regions: dict[str, RegionBlockOut] = {}  # "ES" | "EA" | "US"
    impact: PersonalImpactOut
    bonds: BondSnapshotOut
    forex: ForexSnapshotOut
    personal_economy: dict = {}
