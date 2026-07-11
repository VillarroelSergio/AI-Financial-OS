import importlib
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.runner import IngestionSummary


def _reload():
    import app.modules.market_intelligence.ingestion.startup as mod
    importlib.reload(mod)
    return mod


def test_get_ingest_status_initial():
    mod = _reload()
    status = mod.get_ingest_status()
    assert status["current"] is None
    assert status["last_run"] is None


def _fake_catalog():
    loader = MagicMock()
    loader.load_all.return_value = [SimpleNamespace(id="x", dashboard=True, frequency="daily")]
    return MagicMock(return_value=loader)


def test_run_due_sets_last_run():
    mod = _reload()
    summary = MagicMock(spec=IngestionSummary)
    summary.run_id = "abc123"
    summary.started_at = summary.finished_at = MagicMock()
    summary.started_at.isoformat.return_value = "2026-07-06T00:00:00Z"
    summary.total, summary.success, summary.failed, summary.fallbacks_used = 1, 1, 0, 0
    summary.results = []

    with patch.object(mod, "CatalogLoader", _fake_catalog()), \
         patch.object(mod.scheduler, "due_item_ids", return_value=["x"]), \
         patch.object(mod, "run_ingestion", return_value=summary) as run:
        mod._run_due()

    run.assert_called_once()
    assert mod.get_ingest_status()["last_run"]["success"] == 1
    assert mod.get_ingest_status()["current"] is None


def test_run_due_skips_when_nothing_due():
    mod = _reload()
    with patch.object(mod, "CatalogLoader", _fake_catalog()), \
         patch.object(mod.scheduler, "due_item_ids", return_value=[]), \
         patch.object(mod, "run_ingestion") as run:
        mod._run_due()
    run.assert_not_called()  # ningún item vencido → ninguna llamada de red


def test_run_due_records_error():
    mod = _reload()
    with patch.object(mod, "CatalogLoader", _fake_catalog()), \
         patch.object(mod.scheduler, "due_item_ids", return_value=["x"]), \
         patch.object(mod, "run_ingestion", side_effect=RuntimeError("boom")):
        mod._run_due()
    assert "boom" in mod.get_ingest_status()["last_run"]["error"]
