"""Market Regime Engine — clasifica el régimen macro/mercado actual."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from app.modules.financial_knowledge._shared import now as _now
from app.modules.financial_knowledge._shared import uid as _uid
from app.modules.financial_knowledge.models import (
    FinancialSignal,
    GrowthRegime,
    InflationRegime,
    MarketRegime,
    MarketTrend,
    RatesRegime,
    RiskLevel,
)

logger = logging.getLogger("financial_knowledge.market_regime_engine")

_REGIME_RULES_PATH = Path(__file__).parent.parent / "rules" / "regime_rules.yaml"


def _load_rules() -> dict:
    if _REGIME_RULES_PATH.exists():
        return yaml.safe_load(_REGIME_RULES_PATH.read_text(encoding="utf-8")) or {}
    return {}


def _active_signal_types(signals: list[FinancialSignal]) -> set[str]:
    return {s.signal_type for s in signals}


def _classify_risk_level(active: set[str], rules: dict) -> tuple[RiskLevel, float]:
    risk_off_rule = rules.get("risk_off", {})
    risk_on_rule = rules.get("risk_on", {})

    risk_off_required = set(risk_off_rule.get("required_signals", []))
    risk_on_required = set(risk_on_rule.get("required_signals", []))

    if risk_off_required and risk_off_required.issubset(active):
        confidence = risk_off_rule.get("confidence", 0.75)
        optional = set(risk_off_rule.get("optional_signals", []))
        bonus = len(optional & active) * 0.05
        return RiskLevel.RISK_OFF, min(confidence + bonus, 0.95)

    if risk_on_required and risk_on_required.issubset(active):
        return RiskLevel.RISK_ON, risk_on_rule.get("confidence", 0.65)

    return RiskLevel.NEUTRAL, 0.5


def _classify_inflation_regime(active: set[str], rules: dict) -> InflationRegime:
    if rules.get("inflationary", {}).get("required_signals", []):
        if set(rules["inflationary"]["required_signals"]).issubset(active):
            return InflationRegime.INFLATIONARY
    if "inflation_decelerating" in active:
        return InflationRegime.DISINFLATIONARY
    if "inflation_above_target" in active:
        return InflationRegime.INFLATIONARY
    return InflationRegime.STABLE


def _classify_rates_regime(active: set[str], rules: dict) -> RatesRegime:
    if "rates_falling" in active or "cutting_cycle" in active:
        return RatesRegime.CUTTING_CYCLE
    if "rates_rising" in active:
        return RatesRegime.HIKING_CYCLE
    if "rates_high" in active:
        return RatesRegime.HIGH_RATES
    return RatesRegime.STABLE


def _classify_growth_regime(active: set[str], rules: dict) -> GrowthRegime:
    recession_rule = rules.get("recession_risk", {})
    required = set(recession_rule.get("required_signals", []))
    if required and required.issubset(active):
        return GrowthRegime.RECESSION_RISK
    if "employment_weakening" in active:
        return GrowthRegime.SLOWDOWN
    if "equity_market_positive" in active and "inflation_above_target" not in active:
        return GrowthRegime.EXPANSION
    return GrowthRegime.UNKNOWN


def _classify_market_trend(active: set[str]) -> MarketTrend:
    if "equity_market_drawdown" in active:
        return MarketTrend.BEAR
    if "equity_market_positive" in active:
        return MarketTrend.BULL
    return MarketTrend.SIDEWAYS


def _build_explanation(
    risk: RiskLevel,
    inflation: InflationRegime,
    rates: RatesRegime,
    growth: GrowthRegime,
    trend: MarketTrend,
    active: set[str],
) -> str:
    parts = [
        f"Régimen de riesgo: {risk.value}",
        f"Inflación: {inflation.value}",
        f"Tipos: {rates.value}",
        f"Crecimiento: {growth.value}",
        f"Tendencia mercado: {trend.value}",
    ]
    key_signals = [s for s in active if s in {
        "inflation_above_target", "yield_curve_inverted", "equity_market_drawdown",
        "rates_high", "employment_weakening", "oil_spike",
    }]
    if key_signals:
        parts.append(f"Señales clave: {', '.join(key_signals)}")
    return ". ".join(parts)


def compute_regime(signals: list[FinancialSignal]) -> MarketRegime:
    """Clasifica el régimen de mercado actual basándose en las señales activas."""
    rules = _load_rules()
    active = _active_signal_types(signals)

    risk_level, confidence = _classify_risk_level(active, rules)
    inflation_regime = _classify_inflation_regime(active, rules)
    rates_regime = _classify_rates_regime(active, rules)
    growth_regime = _classify_growth_regime(active, rules)
    market_trend = _classify_market_trend(active)

    explanation = _build_explanation(risk_level, inflation_regime, rates_regime, growth_regime, market_trend, active)

    regime = MarketRegime(
        id=_uid(),
        risk_level=risk_level,
        inflation_regime=inflation_regime,
        rates_regime=rates_regime,
        growth_regime=growth_regime,
        market_trend=market_trend,
        confidence_score=confidence,
        explanation=explanation,
        computed_at=_now(),
        signals_used=list(active),
    )

    logger.info(
        "MarketRegimeEngine: risk=%s inflation=%s rates=%s growth=%s trend=%s confidence=%.2f",
        risk_level.value, inflation_regime.value, rates_regime.value,
        growth_regime.value, market_trend.value, confidence,
    )
    return regime
