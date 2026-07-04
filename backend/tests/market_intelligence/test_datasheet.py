"""TDD tests for AI Datasheet generator."""
from unittest.mock import patch

from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet


def _empty_macro():
    from datetime import datetime, timezone

    from app.modules.market_intelligence.api.schemas import MacroSnapshotOut
    return MacroSnapshotOut(spain=[], eurozone=[], usa=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_forex():
    from datetime import datetime, timezone

    from app.modules.market_intelligence.api.schemas import ForexSnapshotOut
    return ForexSnapshotOut(rates=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_bonds():
    from datetime import datetime, timezone

    from app.modules.market_intelligence.api.schemas import BondSnapshotOut
    return BondSnapshotOut(yields=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_news():
    from datetime import datetime, timezone

    from app.modules.market_intelligence.api.schemas import NewsSnapshotOut
    return NewsSnapshotOut(items=[], generated_at=datetime.now(timezone.utc).isoformat())


def test_generate_ai_datasheet_returns_valid_structure():
    with (
        patch("app.modules.market_intelligence.ai.datasheet.service.get_macro_snapshot", return_value=_empty_macro()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_forex_snapshot", return_value=_empty_forex()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_bond_snapshot", return_value=_empty_bonds()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_news_snapshot", return_value=_empty_news()),
        patch("app.modules.market_intelligence.ai.datasheet.repository.save_ai_datasheet"),
    ):
        result = generate_ai_datasheet(scope="daily")

    assert hasattr(result, "generated_at")
    assert hasattr(result, "quality_score")
    assert hasattr(result, "macro")
    assert hasattr(result, "forex")
    assert hasattr(result, "bonds")
    assert hasattr(result, "news")
    assert hasattr(result, "warnings")
    assert result.scope == "daily"


def test_datasheet_quality_score_is_between_0_and_1():
    with (
        patch("app.modules.market_intelligence.ai.datasheet.service.get_macro_snapshot", return_value=_empty_macro()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_forex_snapshot", return_value=_empty_forex()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_bond_snapshot", return_value=_empty_bonds()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_news_snapshot", return_value=_empty_news()),
        patch("app.modules.market_intelligence.ai.datasheet.repository.save_ai_datasheet"),
    ):
        result = generate_ai_datasheet(scope="daily")

    assert 0.0 <= result.quality_score <= 1.0
