"""ECO-5: ingesta en background con scheduler por frecuencia.

Un tick horario ingesta SOLO los items cuyo `last_success + frequency` ha vencido
(scheduler.due_item_ids), en vez de refetchear todo cada 6 h. El estado de /ingest-status
distingue la corrida en curso de la última completada, protegido con lock.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from threading import Lock, Thread

from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.ingestion import scheduler
from app.modules.market_intelligence.ingestion.runner import run_ingestion

# Frecuencia del tick. El refresco real lo decide el scheduler por item; el tick solo debe
# ser lo bastante fino para no retrasar una serie diaria más de una hora.
logger = logging.getLogger("market_intelligence.startup")

TICK_SECONDS = 3600
# El histórico profundo se baja una vez (solo faltantes) y luego se refresca a diario.
HISTORY_REFRESH_SECONDS = 86400

_lock = Lock()
_status: dict = {"current": None, "last_run": None}
_last_history_refresh: datetime | None = None


def get_ingest_status() -> dict:
    from app.modules.market_intelligence.ingestion.runner import ADAPTER_LOAD_ERRORS

    with _lock:
        status = {"current": _status["current"], "last_run": _status["last_run"]}
    if ADAPTER_LOAD_ERRORS:
        status["adapter_load_errors"] = dict(ADAPTER_LOAD_ERRORS)
    status["storage"] = "file"  # ECO-3b: SQLite WAL, sin fallback a memoria
    return status


def _summary_to_status(summary) -> dict:
    return {
        "run_id": summary.run_id,
        "started_at": summary.started_at.isoformat(),
        "finished_at": summary.finished_at.isoformat(),
        "total": summary.total,
        "success": summary.success,
        "failed": summary.failed,
        "fallbacks_used": summary.fallbacks_used,
        "results": [
            {
                "indicator": r.catalog_id,
                "category": r.indicator.category,
                "provider": r.provider_used,
                "status": "ok" if r.adapter_result.success else "error",
                "fallback_used": r.fallback_used,
                "error": r.adapter_result.error,
            }
            for r in summary.results
        ],
    }


def _run_due() -> None:
    from app.modules.market_intelligence.storage import repository

    now = datetime.now(timezone.utc)
    indicators = [i for i in CatalogLoader().load_all() if i.dashboard]
    try:
        state = repository.get_ingest_state()
    except Exception:
        state = {}
    due = scheduler.due_item_ids(indicators, state, now)
    if not due:
        return  # nada vencido → ninguna llamada de red este tick

    with _lock:
        _status["current"] = {
            "started_at": now.isoformat(), "in_progress": True, "due_count": len(due),
        }
    try:
        summary = run_ingestion(dashboard=True, item_ids=due)
        with _lock:
            _status["last_run"] = _summary_to_status(summary)
    except Exception as exc:
        with _lock:
            _status["last_run"] = {"error": str(exc), "finished_at":
                                   datetime.now(timezone.utc).isoformat()}
    finally:
        with _lock:
            _status["current"] = None


def _backfill_history_once() -> None:
    """Histórico profundo la primera vez (solo instrumentos sin serie). Idempotente:
    en reinicios con datos ya presentes no baja nada. En background, nunca bloquea la UI."""
    global _last_history_refresh
    from app.modules.market_intelligence.ingestion.history_backfill import backfill_all

    try:
        n = backfill_all(years=5, only_missing=True)
        if n:
            logger.info("startup history backfill: %d filas", n)
    except Exception as exc:  # el histórico es best-effort; no debe tumbar la ingesta
        logger.warning("startup history backfill falló: %s", exc)
    _last_history_refresh = datetime.now(timezone.utc)


def _refresh_history_if_due() -> None:
    """Refresco diario de la cola de la serie para que la ficha no se congele.
    ponytail: re-baja 1 año (idempotente); pasar a ventana corta si algún proveedor limita."""
    global _last_history_refresh
    now = datetime.now(timezone.utc)
    if _last_history_refresh and (now - _last_history_refresh).total_seconds() < HISTORY_REFRESH_SECONDS:
        return
    from app.modules.market_intelligence.ingestion.history_backfill import backfill_all

    try:
        backfill_all(years=1, only_missing=False)
    except Exception as exc:
        logger.warning("history refresh falló: %s", exc)
    _last_history_refresh = now


def launch_startup_ingest() -> None:
    """Tick de ingesta por frecuencia mientras la app viva (primer tick inmediato)."""
    def _loop() -> None:
        _backfill_history_once()  # una vez, antes del primer tick
        while True:
            _run_due()
            _refresh_history_if_due()
            time.sleep(TICK_SECONDS)

    Thread(target=_loop, daemon=True).start()
