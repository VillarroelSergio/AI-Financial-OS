"""Tests para MarketRegimeEngine."""
from __future__ import annotations
from datetime import datetime, timezone


from app.modules.financial_knowledge.engines import market_regime_engine as engine
from app.modules.financial_knowledge.models import (
    FinancialSignal, Direction, Severity, RiskLevel, InflationRegime,
    RatesRegime, GrowthRegime, MarketTrend,
)


def _signal(signal_type: str, confidence: float = 0.8) -> FinancialSignal:
    return FinancialSignal(
        id=f"sig-{signal_type}",
        signal_type=signal_type,
        name=signal_type,
        category="macro",
        description=signal_type,
        direction=Direction.NEGATIVE,
        severity=Severity.MEDIUM,
        confidence_score=confidence,
        quality_score=0.9,
        computed_at=datetime.now(timezone.utc),
    )


class TestComputeRegime:
    def test_risk_off_when_drawdown_and_inverted_curve(self):
        signals = [_signal("equity_market_drawdown"), _signal("yield_curve_inverted")]
        regime = engine.compute_regime(signals)
        assert regime.risk_level == RiskLevel.RISK_OFF

    def test_risk_on_when_positive_market(self):
        signals = [_signal("equity_market_positive")]
        regime = engine.compute_regime(signals)
        assert regime.risk_level == RiskLevel.RISK_ON

    def test_neutral_when_no_strong_signals(self):
        signals = [_signal("inflation_above_target")]
        regime = engine.compute_regime(signals)
        assert regime.risk_level == RiskLevel.NEUTRAL

    def test_inflationary_regime_when_inflation_signal(self):
        signals = [_signal("inflation_above_target")]
        regime = engine.compute_regime(signals)
        assert regime.inflation_regime == InflationRegime.INFLATIONARY

    def test_disinflationary_when_decelerating(self):
        signals = [_signal("inflation_decelerating")]
        regime = engine.compute_regime(signals)
        assert regime.inflation_regime == InflationRegime.DISINFLATIONARY

    def test_high_rates_regime(self):
        signals = [_signal("rates_high")]
        regime = engine.compute_regime(signals)
        assert regime.rates_regime == RatesRegime.HIGH_RATES

    def test_cutting_cycle_regime(self):
        signals = [_signal("rates_falling")]
        regime = engine.compute_regime(signals)
        assert regime.rates_regime == RatesRegime.CUTTING_CYCLE

    def test_bear_market_trend(self):
        signals = [_signal("equity_market_drawdown")]
        regime = engine.compute_regime(signals)
        assert regime.market_trend == MarketTrend.BEAR

    def test_bull_market_trend(self):
        signals = [_signal("equity_market_positive")]
        regime = engine.compute_regime(signals)
        assert regime.market_trend == MarketTrend.BULL

    def test_recession_risk_growth_regime(self):
        signals = [_signal("equity_market_drawdown"), _signal("yield_curve_inverted")]
        regime = engine.compute_regime(signals)
        assert regime.growth_regime == GrowthRegime.RECESSION_RISK

    def test_regime_has_explanation(self):
        signals = [_signal("inflation_above_target")]
        regime = engine.compute_regime(signals)
        assert regime.explanation
        assert len(regime.explanation) > 10

    def test_empty_signals_returns_neutral_regime(self):
        regime = engine.compute_regime([])
        assert regime.risk_level == RiskLevel.NEUTRAL
        assert regime.confidence_score == 0.5

    def test_signals_used_populated(self):
        signals = [_signal("rates_high"), _signal("inflation_above_target")]
        regime = engine.compute_regime(signals)
        assert "rates_high" in regime.signals_used
        assert "inflation_above_target" in regime.signals_used
