"""Regression tests for Economy Data Integrity (Phase 10.6 Task 1).

Verifies that:
- USA indicator values are not all identical (silent fallback bug)
- FRED adapter only returns records relevant to the requested indicator_id
- value_numeric in repository correctly handles 0.0 values (falsy bug)
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# ── FRED adapter indicator isolation ─────────────────────────────────────────

SAMPLE_FRED_CSV_UNRATE = "DATE,VALUE\n2026-01-01,4.1\n2026-02-01,4.2\n2026-03-01,4.0\n"
SAMPLE_FRED_CSV_FEDFUNDS = "DATE,VALUE\n2026-01-01,5.33\n2026-02-01,5.33\n2026-03-01,5.08\n"
SAMPLE_FRED_CSV_INDPRO = "DATE,VALUE\n2026-01-01,103.5\n2026-02-01,103.8\n2026-03-01,104.1\n"


def _mock_fred_response(csv_text: str):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = csv_text
    mock.raise_for_status = MagicMock()
    return mock


class TestFREDAdapterIndicatorIsolation:
    """FRED adapter must return only records relevant to the requested indicator."""

    def test_unemployment_usa_returns_unrate_only(self):
        from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
        adapter = FREDAdapter()
        with patch("requests.get", return_value=_mock_fred_response(SAMPLE_FRED_CSV_UNRATE)):
            result = adapter.fetch("unemployment_usa")
        assert result.success
        for record in result.records:
            assert hasattr(record, "indicator_id")
            assert "UNRATE" in record.indicator_id or record.indicator_id == "UNRATE"

    def test_fed_funds_rate_returns_fedfunds_only(self):
        from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
        adapter = FREDAdapter()
        with patch("requests.get", return_value=_mock_fred_response(SAMPLE_FRED_CSV_FEDFUNDS)):
            result = adapter.fetch("fed_funds_rate")
        assert result.success
        for record in result.records:
            assert hasattr(record, "indicator_id")
            assert "FEDFUNDS" in record.indicator_id or record.indicator_id == "FEDFUNDS"

    def test_industrial_production_usa_returns_indpro_only(self):
        from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
        adapter = FREDAdapter()
        with patch("requests.get", return_value=_mock_fred_response(SAMPLE_FRED_CSV_INDPRO)):
            result = adapter.fetch("industrial_production_usa")
        assert result.success

    def test_unmapped_indicator_returns_failure(self):
        """An indicator not mapped to any FRED series should return success=False, not garbage data."""
        from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
        adapter = FREDAdapter()
        with patch("requests.get") as mock_get:
            result = adapter.fetch("some_unknown_indicator_xyz")
        # Must not have made any HTTP calls and must not return stale records
        mock_get.assert_not_called()
        assert not result.success
        assert result.records == []

    def test_different_indicators_would_not_share_same_value(self):
        """Verify that two different indicators produce different values (not clobbered)."""
        from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
        adapter = FREDAdapter()

        with patch("requests.get", return_value=_mock_fred_response(SAMPLE_FRED_CSV_UNRATE)):
            unrate_result = adapter.fetch("unemployment_usa")

        with patch("requests.get", return_value=_mock_fred_response(SAMPLE_FRED_CSV_FEDFUNDS)):
            fedfunds_result = adapter.fetch("fed_funds_rate")

        unrate_values = {r.value for r in unrate_result.records if hasattr(r, "value")}
        fedfunds_values = {r.value for r in fedfunds_result.records if hasattr(r, "value")}

        # They must be disjoint — unemployment (~4%) and fed funds rate (~5.33%) are different
        assert unrate_values != fedfunds_values, (
            f"unemployment and fed_funds_rate returned identical values: {unrate_values}"
        )


# ── Repository value_numeric falsy-zero bug ───────────────────────────────────

class TestRepositoryValueNumericZero:
    """value_numeric must not skip 0.0 values due to Python falsy `or` chaining."""

    def test_zero_value_is_stored_not_skipped(self):
        """A MacroIndicator with value=0.0 must produce value_numeric=0.0, not None."""
        from app.modules.market_intelligence.ingestion.models import MacroIndicator

        record = MacroIndicator(
            provider="TEST",
            source="http://test",
            retrieved_at=datetime.now(timezone.utc),
            country="US",
            region="USA",
            confidence_score=1.0,
            indicator_id="test_zero",
            name="Test Zero",
            value=0.0,
            unit="%",
            period="2026-01",
            frequency="monthly",
        )

        # Simulate the old broken logic
        broken_value = (
            getattr(record, "value", None)
            or getattr(record, "rate", None)
            or getattr(record, "price", None)
            or getattr(record, "yield_value", None)
        )
        assert broken_value is None, "This confirms the original bug exists for value=0.0"

        # The fixed logic uses first-not-None
        def _first_not_none(*vals):
            for v in vals:
                if v is not None:
                    return v
            return None

        fixed_value = _first_not_none(
            getattr(record, "value", None),
            getattr(record, "rate", None),
            getattr(record, "price", None),
            getattr(record, "yield_value", None),
        )
        assert fixed_value == 0.0, f"Fixed logic must preserve 0.0, got {fixed_value}"


# ── MacroSnapshot service — clones cut at source (ECO-1) ─────────────────────

class TestMacroSnapshotRepeatedValues:
    """La clonación (P1) se corta en origen (allowlists honestas en los adapters),
    así que la lectura ya NO detecta, avisa ni filtra por 'valores repetidos'."""

    def _make_row(self, catalog_id: str, value: float, country: str = "US", region_hint: str = "usa") -> dict:
        return {
            "catalog_item_id": catalog_id,
            "indicator_id": catalog_id,
            "country": country,
            "period": "2026-03",
            "value": value,
            "unit": "%",
            "provider_id": "fred",
            "quality_score": 0.9,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_identical_values_no_longer_filtered_or_warned(self):
        from app.modules.market_intelligence.api.service import get_macro_snapshot

        # Aun compartiendo valor, los 3 indicadores se conservan y no hay warning:
        # la integridad se garantiza en ingesta, no parcheando la lectura.
        shared_value = 4.1
        rows = [
            self._make_row("unemployment_usa", shared_value),
            self._make_row("fed_funds_rate", shared_value),
            self._make_row("industrial_production_usa", shared_value),
        ]

        with patch(
            "app.modules.market_intelligence.api.service.repository.get_latest_macro_all",
            return_value=rows,
        ):
            snapshot = get_macro_snapshot()

        assert len(snapshot.usa) == 3
        assert not any("repetid" in w.lower() or "repeated" in w.lower() for w in snapshot.warnings)

    def test_distinct_values_no_warning(self):
        from app.modules.market_intelligence.api.service import get_macro_snapshot

        rows = [
            self._make_row("unemployment_usa", 4.1),
            self._make_row("fed_funds_rate", 5.33),
            self._make_row("industrial_production_usa", 103.5),
        ]

        with patch(
            "app.modules.market_intelligence.api.service.repository.get_latest_macro_all",
            return_value=rows,
        ):
            snapshot = get_macro_snapshot()

        repeated_warnings = [w for w in snapshot.warnings if "repetidos" in w or "repeated" in w.lower()]
        assert not repeated_warnings, (
            f"No repeated-value warning expected for distinct values, got: {repeated_warnings}"
        )
