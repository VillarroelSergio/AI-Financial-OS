"""Conexión SQLite (WAL) del Market Intelligence Layer — ECO-3b.

Sustituye a DuckDB: mismo motor que el resto de la app, sin el fallback-a-memoria del
mono-escritor. WAL + busy_timeout permiten lectura/escritura concurrente (daemon de
ingesta + requests de FastAPI) sobre un único fichero. Ver ADR docs/internal/eco3_adr_storage_engine.md.

financial_knowledge sigue en DuckDB (fuera del alcance del ADR); por eso MI tiene su
propia conexión aquí en vez de reusar app.core.duckdb.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path

from app.core.config import settings
from app.modules.market_intelligence.storage.migrations import run_migrations

logger = logging.getLogger("market_intelligence.db")

# datetime/date crudos → ISO string. Solo se disparan cuando nuestro código MI pasa un
# objeto como parámetro; SQLAlchemy (BD personal) serializa por su cuenta y no colisiona.
sqlite3.register_adapter(datetime, lambda d: d.isoformat())
sqlite3.register_adapter(date, lambda d: d.isoformat())
# Solo la columna DATE de precios históricos vuelve como date (get_price_change_1y hace
# aritmética). El resto de fechas/timestamps son TEXT ISO (comparación lexicográfica basta).
sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode()))

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()
_migrations_run = False


def get_conn() -> sqlite3.Connection:
    """Conexión única compartida (WAL, autocommit). Idempotente."""
    global _conn, _migrations_run
    with _lock:
        if _conn is None:
            db_path = Path(settings.MI_SQLITE_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # ponytail: una sola conexión compartida entre threads (check_same_thread=False);
            # a decenas de filas/día el mutex interno de sqlite3 + WAL sobra. Conexión por
            # thread solo si la contención se vuelve medible.
            _conn = sqlite3.connect(
                str(db_path),
                check_same_thread=False,
                isolation_level=None,  # autocommit, como DuckDB
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            _conn.execute("PRAGMA journal_mode=WAL")
            _conn.execute("PRAGMA busy_timeout=5000")
            logger.info("MI SQLite opened: %s", db_path)
        if not _migrations_run:
            run_migrations(_conn)
            _migrations_run = True
        return _conn
