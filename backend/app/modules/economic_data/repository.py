"""DuckDB-backed cache for economic indicator data."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import duckdb

from app.core.duckdb import get_duckdb

logger = logging.getLogger(__name__)

_conn: Optional[duckdb.DuckDBPyConnection] = None
_conn_lock = threading.Lock()
_ddl_initialized = False

_DDL = """
CREATE TABLE IF NOT EXISTS economic_indicators_cache (
    series_id        VARCHAR NOT NULL,
    region           VARCHAR NOT NULL,
    indicator        VARCHAR NOT NULL,
    name             VARCHAR NOT NULL,
    value            DOUBLE,
    prev_value       DOUBLE,
    period           VARCHAR,
    unit             VARCHAR NOT NULL DEFAULT '%',
    source           VARCHAR NOT NULL,
    observation_date DATE NOT NULL,
    downloaded_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (series_id, observation_date)
);
"""

_TTL_HOURS: dict[str, int] = {
    "inflation": 24,
    "core_inflation": 24,
    "unemployment": 24,
    "gdp": 48,
    "policy_rate": 4,
    "bond_10y": 4,
    "euribor": 4,
    "index": 4,
    "forex": 4,
}


def _get_conn() -> duckdb.DuckDBPyConnection:
    global _conn, _ddl_initialized
    if not _ddl_initialized:
        with _conn_lock:
            if not _ddl_initialized:
                conn = get_duckdb()
                conn.execute(_DDL)
                _conn = conn
                _ddl_initialized = True
    return _conn  # type: ignore[return-value]


def upsert_indicator(
    series_id: str,
    region: str,
    indicator: str,
    name: str,
    value: Optional[float],
    prev_value: Optional[float],
    period: str,
    unit: str,
    source: str,
    observation_date: str,
) -> None:
    conn = _get_conn()
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT OR REPLACE INTO economic_indicators_cache
            (series_id, region, indicator, name, value, prev_value, period, unit,
             source, observation_date, downloaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [series_id, region, indicator, name, value, prev_value, period, unit,
         source, observation_date, now],
    )


def get_latest(series_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT series_id, region, indicator, name, value, prev_value, period, unit,
               source, observation_date::VARCHAR, downloaded_at
        FROM economic_indicators_cache
        WHERE series_id = ?
        ORDER BY observation_date DESC
        LIMIT 1
        """,
        [series_id],
    ).fetchone()
    if row is None:
        return None
    cols = ["series_id", "region", "indicator", "name", "value", "prev_value",
            "period", "unit", "source", "observation_date", "downloaded_at"]
    return dict(zip(cols, row))


def get_all_latest() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (series_id)
               series_id, region, indicator, name, value, prev_value, period, unit,
               source, observation_date::VARCHAR, downloaded_at
        FROM economic_indicators_cache
        ORDER BY series_id, observation_date DESC
        """
    ).fetchall()
    cols = ["series_id", "region", "indicator", "name", "value", "prev_value",
            "period", "unit", "source", "observation_date", "downloaded_at"]
    return [dict(zip(cols, r)) for r in rows]


def is_stale(series_id: str, indicator: str) -> bool:
    cached = get_latest(series_id)
    if cached is None:
        return True
    ttl = _TTL_HOURS.get(indicator, 24)
    downloaded_at = cached["downloaded_at"]
    if isinstance(downloaded_at, str):
        downloaded_at = datetime.fromisoformat(downloaded_at)
    age_hours = (datetime.now(timezone.utc) - downloaded_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    return age_hours > ttl
