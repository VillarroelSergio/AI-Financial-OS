"""Schemas Pydantic del Financial Knowledge Layer para la API REST."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EconomicIndicatorInsightOut(BaseModel):
    id: str
    indicator_id: str
    name: str
    category: str
    country: str
    value: float
    unit: str
    period: str
    trend: str
    severity: str
    quality_score: float
    computed_at: datetime
    catalog_item_id: Optional[str] = None
    previous_value: Optional[float] = None
    change_abs: Optional[float] = None
    change_pct: Optional[float] = None
    target_value: Optional[float] = None
    distance_to_target: Optional[float] = None
    interpretation: Optional[str] = None
    source_provider: Optional[str] = None
    rule_id: Optional[str] = None

    model_config = {"from_attributes": True}


class FinancialSignalOut(BaseModel):
    id: str
    signal_type: str
    name: str
    category: str
    description: str
    direction: str
    severity: str
    confidence_score: float
    quality_score: float
    computed_at: datetime
    affected_assets: list[str] = []
    affected_user_domains: list[str] = []
    source_indicators: list[str] = []
    rule_id: Optional[str] = None

    model_config = {"from_attributes": True}


class MarketRegimeOut(BaseModel):
    id: str
    risk_level: str
    inflation_regime: str
    rates_regime: str
    growth_regime: str
    market_trend: str
    confidence_score: float
    explanation: str
    computed_at: datetime
    regime_type: Optional[str] = None
    signals_used: list[str] = []

    model_config = {"from_attributes": True}


class PersonalImpactOut(BaseModel):
    id: str
    impact_type: str
    user_domain: str
    title: str
    description: str
    severity: str
    confidence_score: float
    computed_at: datetime
    estimated_monthly_impact: Optional[float] = None
    estimated_portfolio_impact: Optional[float] = None
    currency: str = "EUR"
    related_accounts: list[str] = []
    related_holdings: list[str] = []
    related_goals: list[str] = []
    source_signals: list[str] = []

    model_config = {"from_attributes": True}


class AIDatasheetOut(BaseModel):
    generated_at: datetime
    quality_score: float
    market_regime: Optional[dict] = None
    macro_insights: list[dict] = []
    financial_signals: list[dict] = []
    personal_impacts: list[dict] = []
    portfolio_context: dict = {}
    news_context: list[dict] = []
    warnings: list[str] = []
    sources: list[str] = []

    model_config = {"from_attributes": True}


class KnowledgeSnapshotOut(BaseModel):
    generated_at: datetime
    quality_score: float
    regime: Optional[MarketRegimeOut] = None
    signals: list[FinancialSignalOut] = []
    insights: list[EconomicIndicatorInsightOut] = []
    personal_impacts: list[PersonalImpactOut] = []
    warnings: list[str] = []

    model_config = {"from_attributes": True}


class RecomputeResultOut(BaseModel):
    success: bool
    message: str
    insights_computed: int = 0
    signals_computed: int = 0
    regime_computed: bool = False
    impacts_computed: int = 0
    datasheet_generated: bool = False
    errors: list[str] = []
