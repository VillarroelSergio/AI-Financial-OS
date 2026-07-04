"""Lanza ingesta en background una vez al arrancar la app."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Thread

from app.core.duckdb import is_in_memory
from app.modules.market_intelligence.ingestion.runner import run_ingestion

_status: dict = {"status": "idle", "last_run": None, "count": 0, "results": []}


def get_ingest_status() -> dict:
    from app.modules.market_intelligence.ingestion.runner import ADAPTER_LOAD_ERRORS

    status = _status.copy()
    if ADAPTER_LOAD_ERRORS:
        status["adapter_load_errors"] = dict(ADAPTER_LOAD_ERRORS)
    # El fallback en memoria significa que nada persiste: avisar siempre.
    status["storage"] = "memory" if is_in_memory() else "file"
    if status["storage"] == "memory":
        status["storage_warning"] = (
            "La base analítica está bloqueada por otro proceso; los datos de mercado "
            "no persisten en esta sesión. Cierra procesos duplicados del backend y reinicia."
        )
    return status


def launch_startup_ingest() -> None:
    """Lanza la ingesta de indicadores visibles en dashboard en un daemon thread."""
    def _run() -> None:
        _status["status"] = "running"
        try:
            # Limpieza previa: observaciones macro estampadas bajo bonos/commodities
            # por fallbacks antiguos (causa de indicadores clonados en Economía).
            from app.modules.market_intelligence.storage import repository
            try:
                repository.purge_mismatched_macro_observations()
            except Exception:  # noqa: BLE001 — la purga nunca debe impedir la ingesta
                pass
            summary = run_ingestion(dashboard=True)
            _status["count"] = summary.success
            _status["results"] = [
                {
                    "indicator": r.catalog_id,
                    "category": r.indicator.category,
                    "provider": r.provider_used,
                    "success": r.adapter_result.success,
                    "fallback_used": r.fallback_used,
                    "error": r.adapter_result.error,
                }
                for r in summary.results
            ]
            _status["status"] = "done"
        except Exception as exc:
            _status["error"] = str(exc)
            _status["status"] = "error"
        _status["last_run"] = datetime.now(timezone.utc).isoformat()

    Thread(target=_run, daemon=True).start()
