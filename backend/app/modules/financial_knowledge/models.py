"""Modelos de datos del Financial Knowledge Layer.

Estructuras internas usadas por los engines. No son modelos de BD directos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# ── Enums ─────────────────────────────────────────────────────────────────────

class Trend(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Direction(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"


class InflationRegime(str, Enum):
    INFLATIONARY = "inflationary"
    DISINFLATIONARY = "disinflationary"
    DEFLATIONARY = "deflationary"
    STABLE = "stable"


class RatesRegime(str, Enum):
    HIGH_RATES = "high_rates"
    LOW_RATES = "low_rates"
    CUTTING_CYCLE = "cutting_cycle"
    HIKING_CYCLE = "hiking_cycle"
    STABLE = "stable"


class GrowthRegime(str, Enum):
    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    RECESSION_RISK = "recession_risk"
    UNKNOWN = "unknown"


class MarketTrend(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


# ── EconomicIndicatorInsight ───────────────────────────────────────────────────

@dataclass
class EconomicIndicatorInsight:
    id: str
    indicator_id: str
    name: str
    category: str
    country: str
    value: float
    unit: str
    period: str
    trend: Trend
    severity: Severity
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


# ── FinancialSignal ────────────────────────────────────────────────────────────

@dataclass
class FinancialSignal:
    id: str
    signal_type: str
    name: str
    category: str
    description: str
    direction: Direction
    severity: Severity
    confidence_score: float
    quality_score: float
    computed_at: datetime
    affected_assets: list[str] = field(default_factory=list)
    affected_user_domains: list[str] = field(default_factory=list)
    source_indicators: list[str] = field(default_factory=list)
    rule_id: Optional[str] = None


# ── MarketRegime ───────────────────────────────────────────────────────────────

@dataclass
class MarketRegime:
    id: str
    risk_level: RiskLevel
    inflation_regime: InflationRegime
    rates_regime: RatesRegime
    growth_regime: GrowthRegime
    market_trend: MarketTrend
    confidence_score: float
    explanation: str
    computed_at: datetime
    regime_type: Optional[str] = None
    signals_used: list[str] = field(default_factory=list)


# ── CorrelationInsight ────────────────────────────────────────────────────────

@dataclass
class CorrelationInsight:
    id: str
    signal_id: str
    signal_type: str
    asset_type: str
    user_domain: str
    relationship_type: str
    description: str
    confidence_score: float
    computed_at: datetime


# ── PersonalImpact ─────────────────────────────────────────────────────────────

@dataclass
class PersonalImpact:
    id: str
    impact_type: str
    user_domain: str
    title: str
    description: str
    severity: Severity
    confidence_score: float
    computed_at: datetime
    estimated_monthly_impact: Optional[float] = None
    estimated_portfolio_impact: Optional[float] = None
    currency: str = "EUR"
    related_accounts: list[str] = field(default_factory=list)
    related_holdings: list[str] = field(default_factory=list)
    related_goals: list[str] = field(default_factory=list)
    source_signals: list[str] = field(default_factory=list)


# ── KnowledgeGraph ─────────────────────────────────────────────────────────────

@dataclass
class KnowledgeGraphNode:
    id: str
    node_type: str
    label: str
    computed_at: datetime
    properties: dict = field(default_factory=dict)


@dataclass
class KnowledgeGraphEdge:
    id: str
    source_id: str
    target_id: str
    relationship: str
    computed_at: datetime
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


# ── AIDatasheet ────────────────────────────────────────────────────────────────

@dataclass
class AIDatasheet:
    generated_at: datetime
    quality_score: float
    market_regime: Optional[dict] = None
    macro_insights: list[dict] = field(default_factory=list)
    financial_signals: list[dict] = field(default_factory=list)
    personal_impacts: list[dict] = field(default_factory=list)
    portfolio_context: dict = field(default_factory=dict)
    news_context: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
