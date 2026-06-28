"""Lanza ingesta en background una vez al arrancar la app."""
from __future__ import annotations
from threading import Thread
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.runner import run_ingestion

_status: dict = {"status": "idle", "last_run": None, "count": 0}


def get_ingest_status() -> dict:
    return _status.copy()


def launch_startup_ingest() -> None:
    """Lanza run_ingestion(priority='critical') en un daemon thread."""
    def _run() -> None:
        _status["status"] = "running"
        try:
            summary = run_ingestion(priority="critical")
            _status["count"] = summary.success
            _status["status"] = "done"
        except Exception:
            _status["status"] = "error"
        _status["last_run"] = datetime.now(timezone.utc).isoformat()

    Thread(target=_run, daemon=True).start()
