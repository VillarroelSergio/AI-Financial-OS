"""Tests para FinancialSignalEngine."""
from __future__ import annotations
from datetime import datetime, timezone


from app.modules.financial_knowledge.engines import financial_signal_engine as engine
from app.modules.financial_knowledge.models import (
    EconomicIndicatorInsight, Trend, Severity,
)


def _insight(category: str, value: float, trend: Trend = Trend.STABLE, quality: float = 0.9) -> EconomicIndicatorInsight:
    return EconomicIndicatorInsight(
        id="test-id",
        indicator_id=f"{category}_test",
        name=category,
        category=category,
        country="ES",
        value=value,
        unit="%",
        period="2026-01",
        trend=trend,
        severity=Severity.MEDIUM,
        quality_score=quality,
        computed_at=datetime.now(timezone.utc),
    )


def _quote(catalog_id: str, asset_type: str, change_pct: float, quality: float = 0.9) -> dict:
    return {
        "catalog_item_id": catalog_id,
        "symbol": catalog_id.upper(),
        "asset_type": asset_type,
        "price": 100.0,
        "change_pct": change_pct,
        "currency": "USD",
        "observed_at": datetime.now(timezone.utc),
        "provider_id": "test",
        "quality_score": quality,
    }


def _forex(base: str, quote: str, rate: float) -> dict:
    return {
        "catalog_item_id": f"{base.lower()}_{quote.lower()}",
        "base_currency": base,
        "quote_currency": quote,
        "rate": rate,
        "date": "2026-01-01",
        "provider_id": "test",
        "quality_score": 0.9,
    }


def _bond(country: str, maturity: str, yield_value: float) -> dict:
    return {
        "catalog_item_id": f"bond_{country.lower()}_{maturity.lower()}",
        "country": country,
        "maturity": maturity,
        "yield_value": yield_value,
        "date": "2026-01-01",
        "provider_id": "test",
        "quality_score": 0.9,
    }


class TestInflationSignals:
    def test_inflation_above_target_signal_generated(self):
        insights = [_insight("inflation", 3.5)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "inflation_above_target" in types

    def test_inflation_accelerating_when_rising_trend(self):
        insights = [_insight("inflation", 3.5, trend=Trend.RISING)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "inflation_accelerating" in types

    def test_inflation_decelerating_when_falling_trend(self):
        insights = [_insight("inflation", 3.5, trend=Trend.FALLING)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "inflation_decelerating" in types

    def test_no_inflation_signal_when_at_target(self):
        insights = [_insight("inflation", 2.0)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "inflation_above_target" not in types


class TestRatesSignals:
    def test_rates_high_when_above_threshold(self):
        insights = [_insight("interest_rates", 4.5)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "rates_high" in types

    def test_rates_rising_signal(self):
        insights = [_insight("interest_rates", 3.5, trend=Trend.RISING)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "rates_rising" in types


class TestMarketSignals:
    def test_equity_drawdown_signal(self):
        quotes = [_quote("sp500", "equity_index", -6.0)]
        signals = engine.compute_signals(insights=[], quotes=quotes, forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "equity_market_drawdown" in types

    def test_equity_positive_signal(self):
        quotes = [_quote("sp500", "equity_index", 1.5)]
        signals = engine.compute_signals(insights=[], quotes=quotes, forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "equity_market_positive" in types

    def test_no_equity_drawdown_below_threshold(self):
        quotes = [_quote("sp500", "equity_index", -3.0)]
        signals = engine.compute_signals(insights=[], quotes=quotes, forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert "equity_market_drawdown" not in types

    def test_yield_curve_inverted_when_2y_above_10y(self):
        bonds = [_bond("US", "2Y", 5.0), _bond("US", "10Y", 4.5)]
        signals = engine.compute_signals(insights=[], quotes=[], forex=[], bonds=bonds)
        types = [s.signal_type for s in signals]
        assert "yield_curve_inverted" in types

    def test_yield_curve_not_inverted_when_normal(self):
        bonds = [_bond("US", "2Y", 4.0), _bond("US", "10Y", 4.5)]
        signals = engine.compute_signals(insights=[], quotes=[], forex=[], bonds=bonds)
        types = [s.signal_type for s in signals]
        assert "yield_curve_inverted" not in types

    def test_deduplication_keeps_highest_confidence(self):
        # Dos fuentes generando la misma señal
        insights = [_insight("inflation", 4.0), _insight("core_inflation", 4.0)]
        signals = engine.compute_signals(insights=insights, quotes=[], forex=[], bonds=[])
        types = [s.signal_type for s in signals]
        assert types.count("inflation_above_target") == 1
