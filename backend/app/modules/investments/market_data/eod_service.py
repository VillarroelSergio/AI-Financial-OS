"""EodMarketService — fetches EOD closing prices once per calendar day."""
from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timezone
from typing import Optional

from app.modules.investments.market_data.cache import MarketCache
from app.modules.investments.market_data.router import get_router

logger = logging.getLogger(__name__)

_ensure_lock = threading.Lock()


class EodMarketService:
    def __init__(self) -> None:
        self._cache = MarketCache()

    def ensure_today(self) -> None:
        """Fetch EOD data for all catalog assets not yet cached for today.

        Acquires a non-blocking lock so concurrent calls at startup are no-ops.
        Safe to call from a daemon thread.
        """
        if not _ensure_lock.acquire(blocking=False):
            logger.debug("EodMarketService.ensure_today: already running, skipping")
            return
        try:
            router = get_router()
            today = datetime.now(timezone.utc).date()
            for asset in router.catalog:
                cached = self._cache.get_quote(asset.internal_symbol)
                if cached and self._is_today(cached, today):
                    continue
                try:
                    router.get_quote(asset, force_refresh=True, eod_only=True)
                except Exception as exc:
                    logger.warning(
                        "EodMarketService: failed for %s: %s",
                        asset.internal_symbol, exc,
                    )
        finally:
            _ensure_lock.release()

    def _is_today(self, row: dict, today: date) -> bool:
        cached_at = row.get("cached_at")
        if cached_at is None:
            return False
        if isinstance(cached_at, str):
            try:
                cached_at = datetime.fromisoformat(cached_at)
            except ValueError:
                return False
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        return cached_at.date() == today


_service: Optional[EodMarketService] = None
_service_lock = threading.Lock()


def get_eod_service() -> EodMarketService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = EodMarketService()
    return _service
