"""RequestBudget — daily per-provider request counter.

Uses market_provider_logs (existing DuckDB table) as the source of truth.
Only providers with a configured daily_limit are budget-tracked.
Providers without a limit (stooq, yahoo, finnhub) are always allowed.
"""
from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_budget: Optional["RequestBudget"] = None
_budget_lock = threading.Lock()


class RequestBudget:
    """Daily per-provider request counter."""

    def __init__(self, limits: dict[str, int]) -> None:
        self._limits = limits  # {"alphavantage": 400, "twelvedata": 700, ...}

    def can_request(self, provider: str) -> bool:
        """Return True if provider has remaining daily budget (or no limit)."""
        limit = self._limits.get(provider)
        if limit is None:
            return True  # unlimited provider
        try:
            used = self._count_today(provider)
            return used < limit
        except Exception as exc:
            logger.warning("RequestBudget.can_request error for %s: %s", provider, exc)
            return True  # fail open — don't block on budget errors

    def record_request(self, provider: str) -> None:
        """No-op: DuckDB log_fetch in cache.py is the source of truth."""
        # Counts are read directly from market_provider_logs.
        # record_request exists for test mocking and future in-memory caching.
        pass

    def get_remaining(self, provider: str) -> int:
        """Return estimated remaining requests for today."""
        limit = self._limits.get(provider)
        if limit is None:
            return 9999
        try:
            used = self._count_today(provider)
            return max(0, limit - used)
        except Exception:
            return 0

    def _count_today(self, provider: str) -> int:
        """Count log entries for provider since midnight UTC today."""
        from app.modules.market_data.cache import _get_conn, _conn_lock
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        conn = _get_conn()
        with _conn_lock:
            result = conn.execute(
                """
                SELECT COUNT(*) FROM market_provider_logs
                WHERE provider = ?
                  AND fetched_at >= ?
                  AND cache_hit = false
                """,
                [provider, today_start.isoformat()],
            ).fetchone()
        return int(result[0]) if result else 0


def get_budget() -> RequestBudget:
    """Module-level singleton. Limits loaded from market_data_config.yaml."""
    global _budget
    if _budget is None:
        with _budget_lock:
            if _budget is None:
                from pathlib import Path
                import yaml
                config_path = Path(__file__).parent / "config" / "market_data_config.yaml"
                cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                raw = cfg.get("request_budget", {})
                limits = {p: v["daily_limit"] for p, v in raw.items() if "daily_limit" in v}
                _budget = RequestBudget(limits=limits)
    return _budget
