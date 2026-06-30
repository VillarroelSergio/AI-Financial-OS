"""Tests para PersonalImpactEngine."""
from __future__ import annotations
from datetime import datetime, timezone

import pytest

from app.modules.financial_knowledge.engines import personal_impact_engine as engine
from app.modules.financial_knowledge.models import (
    FinancialSignal, Direction, Severity,
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


class TestPersonalImpacts:
    def test_cash_drag_generated_when_inflation_above_target(self):
        signals = [_signal("inflation_above_target")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        types = [i.impact_type for i in impacts]
        assert "cash_drag" in types

    def test_mortgage_pressure_when_rates_high(self):
        signals = [_signal("rates_high")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        types = [i.impact_type for i in impacts]
        assert "mortgage_pressure" in types

    def test_fx_exposure_when_eur_weakness(self):
        signals = [_signal("eur_weakness")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        types = [i.impact_type for i in impacts]
        assert "fx_exposure_loss" in types

    def test_equity_drawdown_impact_generated(self):
        signals = [_signal("equity_market_drawdown")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        types = [i.impact_type for i in impacts]
        assert "equity_drawdown_impact" in types

    def test_energy_cost_pressure_when_oil_spike(self):
        signals = [_signal("oil_spike")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        types = [i.impact_type for i in impacts]
        assert "energy_cost_pressure" in types

    def test_no_impacts_when_no_signals(self):
        impacts = engine.compute_personal_impacts(signals=[], db=None)
        assert impacts == []

    def test_impacts_have_currency_eur(self):
        signals = [_signal("inflation_above_target")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        for impact in impacts:
            assert impact.currency == "EUR"

    def test_all_impacts_have_source_signals(self):
        signals = [_signal("inflation_above_target")]
        impacts = engine.compute_personal_impacts(signals=signals, db=None)
        for impact in impacts:
            assert len(impact.source_signals) > 0
