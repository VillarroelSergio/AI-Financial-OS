"""Shared DuckDB connection for all analytics modules.

DuckDB only allows one writer connection per file at a time. All modules
(market_data cache, economic_data repository, etc.) must share this single
connection instead of each opening their own.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

import duckdb

from app.core.config import settings

logger = logging.getLogger(__name__)

_conn: Optional[duckdb.DuckDBPyConnection] = None
_conn_lock = threading.Lock()
_in_memory = False
_local = threading.local()


def is_in_memory() -> bool:
    """True si la conexión cayó al fallback en memoria (otro proceso tiene el lock).

    En ese modo los datos ingeridos NO persisten y las lecturas ven una BD vacía;
    los consumidores deben avisar al usuario en vez de mostrar 'sin datos' mudo.
    """
    return _in_memory


def get_duckdb() -> duckdb.DuckDBPyConnection:
    global _conn, _in_memory
    with _conn_lock:
        if _conn is None:
            db_path = Path(settings.DUCKDB_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                _conn = duckdb.connect(str(db_path))
                logger.info("DuckDB opened: %s", db_path)
            except Exception:
                logger.warning(
                    "DuckDB file locked by another process, falling back to in-memory DB. "
                    "Ingested data will NOT persist and reads will be empty."
                )
                _conn = duckdb.connect(":memory:")
                _in_memory = True
    # Un DuckDBPyConnection no es seguro para queries concurrentes desde varios
    # threads (ingesta en daemon thread + requests de FastAPI). Cada thread usa
    # su propio cursor (conexión duplicada sobre la misma BD).
    cursor = getattr(_local, "cursor", None)
    if cursor is None:
        cursor = _conn.cursor()
        _local.cursor = cursor
    return cursor
