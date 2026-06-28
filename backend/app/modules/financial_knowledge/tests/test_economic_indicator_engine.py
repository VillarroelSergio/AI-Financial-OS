"""Tests para EconomicIndicatorEngine."""
from __future__ import annotations
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.financial_knowledge.engines import economic_indicator_engine as engine
from app.modules.financial_knowledge.models import Trend, Severity


def _macro_row(catalog_id: str, value: float, unit: str = "%", country: str = "ES") -> dict:
    return {
        "catalog_item_id": catalog_id,
        "indicator_id": catalog_id,
        "country": country,
        "period": "2026-01",
        "value": value,
        "unit": unit,
        "provider_id": "test_provider",
        "quality_score": 0.9,
        "retrieved_at": datetime.now(timezone.utc),
    }


class TestComputeInsights:
    def test_inflation_above_target_generates_insight(self):
        rows = [_macro_row("es_cpi", 3.5)]
        insights = engine.compute_insights(macro_rows=rows)
        assert len(insights) == 1
        assert insights[0].category == "inflation"
        assert insights[0].value == 3.5

    def test_inflation_above_target_has_severity_medium(self):
        rows = [_macro_row("es_cpi", 3.5)]
        insights = engine.compute_insights(macro_rows=rows)
        assert insights[0].severity in (Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)

    def test_inflation_critical_threshold(self):
        rows = [_macro_row("us_cpi", 6.0, country="US")]
        insights = engine.compute_insights(macro_rows=rows)
        assert insights[0].severity == Severity.CRITICAL

    def test_interest_rates_generates_insight(self):
        rows = [_macro_row("ecb_rate", 4.5)]
        insights = engine.compute_insights(macro_rows=rows)
        assert len(insights) == 1
        assert insights[0].category == "interest_rates"

    def test_distance_to_target_computed_for_inflation(self):
        rows = [_macro_row("es_cpi", 3.0)]
        insights = engine.compute_insights(macro_rows=rows)
        assert insights[0].target_value == 2.0
        assert abs(insights[0].distance_to_target - 1.0) < 0.01

    def test_unknown_catalog_item_still_generates_insight(self):
        rows = [_macro_row("unknown_indicator", 42.0)]
        insights = engine.compute_insights(macro_rows=rows)
        assert len(insights) == 1
        assert insights[0].category == "other"

    def test_empty_rows_returns_empty(self):
        insights = engine.compute_insights(macro_rows=[])
        assert insights == []

    def test_duplicate_catalog_items_deduped(self):
        rows = [_macro_row("es_cpi", 3.0), _macro_row("es_cpi", 3.5)]
        insights = engine.compute_insights(macro_rows=rows)
        assert len(insights) == 1

    def test_quality_score_propagated(self):
        rows = [_macro_row("es_cpi", 3.0)]
        rows[0]["quality_score"] = 0.75
        insights = engine.compute_insights(macro_rows=rows)
        assert insights[0].quality_score == 0.75

    def test_interpretation_not_empty(self):
        rows = [_macro_row("es_cpi", 3.0)]
        insights = engine.compute_insights(macro_rows=rows)
        assert insights[0].interpretation
        assert len(insights[0].interpretation) > 5
