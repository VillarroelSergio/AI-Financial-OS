"""Tests para AIDatasheetGenerator."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from app.modules.financial_knowledge.engines import ai_datasheet_generator as generator
from app.modules.financial_knowledge.models import (
    Direction,
    EconomicIndicatorInsight,
    FinancialSignal,
    GrowthRegime,
    InflationRegime,
    MarketRegime,
    MarketTrend,
    PersonalImpact,
    RatesRegime,
    RiskLevel,
    Severity,
    Trend,
)


def _insight(name: str, severity: Severity = Severity.MEDIUM) -> EconomicIndicatorInsight:
    return EconomicIndicatorInsight(
        id=f"ins-{name}",
        indicator_id=name,
        name=name,
        category="inflation",
        country="ES",
        value=3.0,
        unit="%",
        period="2026-01",
        trend=Trend.STABLE,
        severity=severity,
        quality_score=0.9,
        computed_at=datetime.now(timezone.utc),
    )


def _signal(signal_type: str, severity: Severity = Severity.MEDIUM) -> FinancialSignal:
    return FinancialSignal(
        id=f"sig-{signal_type}",
        signal_type=signal_type,
        name=signal_type,
        category="macro",
        description=signal_type,
        direction=Direction.NEGATIVE,
        severity=severity,
        confidence_score=0.8,
        quality_score=0.9,
        computed_at=datetime.now(timezone.utc),
    )


def _regime() -> MarketRegime:
    return MarketRegime(
        id="regime-1",
        risk_level=RiskLevel.NEUTRAL,
        inflation_regime=InflationRegime.INFLATIONARY,
        rates_regime=RatesRegime.HIGH_RATES,
        growth_regime=GrowthRegime.SLOWDOWN,
        market_trend=MarketTrend.SIDEWAYS,
        confidence_score=0.7,
        explanation="Test regime",
        computed_at=datetime.now(timezone.utc),
    )


def _impact() -> PersonalImpact:
    return PersonalImpact(
        id="imp-1",
        impact_type="cash_drag",
        user_domain="cash",
        title="Cash drag",
        description="Erosión del efectivo",
        severity=Severity.MEDIUM,
        confidence_score=0.7,
        computed_at=datetime.now(timezone.utc),
    )


class TestGenerateDatasheet:
    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_datasheet_includes_regime(self, _):
        ds = generator.generate_datasheet([_insight("cpi")], [_signal("inflation_above_target")], _regime(), [])
        assert ds.market_regime is not None
        assert ds.market_regime["risk_level"] == "neutral"

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_datasheet_includes_signals(self, _):
        signals = [_signal("inflation_above_target"), _signal("rates_high")]
        ds = generator.generate_datasheet([], signals, _regime(), [])
        assert len(ds.financial_signals) == 2

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_datasheet_includes_impacts(self, _):
        ds = generator.generate_datasheet([], [], _regime(), [_impact()])
        assert len(ds.personal_impacts) == 1

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_quality_score_is_average_of_inputs(self, _):
        insights = [_insight("cpi")]
        signals = [_signal("inf")]
        ds = generator.generate_datasheet(insights, signals, None, [])
        assert 0.0 <= ds.quality_score <= 1.0

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_warning_when_no_insights(self, _):
        ds = generator.generate_datasheet([], [_signal("rates_high")], _regime(), [])
        assert any("insight" in w.lower() for w in ds.warnings)

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_warning_when_no_signals(self, _):
        ds = generator.generate_datasheet([_insight("cpi")], [], _regime(), [])
        assert any("señal" in w.lower() for w in ds.warnings)

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_warning_when_no_regime(self, _):
        ds = generator.generate_datasheet([], [], None, [])
        assert any("régimen" in w.lower() for w in ds.warnings)

    @patch("app.modules.financial_knowledge.engines.ai_datasheet_generator.mi_repo.get_latest_news", return_value=[])
    def test_datasheet_to_json_is_valid_json(self, _):
        import json
        ds = generator.generate_datasheet([_insight("cpi")], [_signal("inf")], _regime(), [])
        json_str = generator.datasheet_to_json(ds)
        parsed = json.loads(json_str)
        assert "market_regime" in parsed
        assert "financial_signals" in parsed
        assert "macro_insights" in parsed
        assert "personal_impacts" in parsed
        assert "quality_score" in parsed
