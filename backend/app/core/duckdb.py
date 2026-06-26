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


def get_duckdb() -> duckdb.DuckDBPyConnection:
    global _conn
    with _conn_lock:
        if _conn is None:
            db_path = Path(settings.DUCKDB_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                _conn = duckdb.connect(str(db_path))
                logger.info("DuckDB opened: %s", db_path)
            except Exception:
                logger.warning("DuckDB file locked, falling back to in-memory DB")
                _conn = duckdb.connect(":memory:")
        return _conn
