from unittest.mock import patch, MagicMock
import importlib
from app.modules.market_intelligence.ingestion.runner import IngestionSummary


def test_get_ingest_status_initial():
    """Status is idle before launch."""
    import app.modules.market_intelligence.ingestion.startup as mod
    # Re-import to get a fresh module state
    importlib.reload(mod)
    status = mod.get_ingest_status()
    assert status["status"] == "idle"
    assert status["last_run"] is None
    assert status["count"] == 0


def test_launch_startup_ingest_sets_running_then_done():
    """Launch sets status to done after run_ingestion completes."""
    import app.modules.market_intelligence.ingestion.startup as mod
    importlib.reload(mod)

    mock_summary = MagicMock(spec=IngestionSummary)
    mock_summary.success = 42

    with patch(
        "app.modules.market_intelligence.ingestion.startup.run_ingestion",
        return_value=mock_summary,
    ):
        mod.launch_startup_ingest()
        import time
        time.sleep(0.3)  # let daemon thread complete

    status = mod.get_ingest_status()
    assert status["status"] == "done"
    assert status["count"] == 42
    assert status["last_run"] is not None


def test_launch_startup_ingest_sets_error_on_exception():
    """Launch sets status to error when run_ingestion raises."""
    import app.modules.market_intelligence.ingestion.startup as mod
    importlib.reload(mod)

    with patch(
        "app.modules.market_intelligence.ingestion.startup.run_ingestion",
        side_effect=RuntimeError("boom"),
    ):
        mod.launch_startup_ingest()
        import time
        time.sleep(0.3)

    status = mod.get_ingest_status()
    assert status["status"] == "error"
