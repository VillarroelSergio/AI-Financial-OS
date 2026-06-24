"""ProviderRouter — selects the best provider for each asset and manages cache + fallback.

Algorithm per asset:
  1. Check DuckDB cache. Return immediately if fresh (within TTL).
  2. Try providers in routing order for this asset_type.
     - Skip disabled providers and those without API key.
     - Skip if provider.supports() returns False.
     - On success: cache result, return.
     - On error: log, try next provider.
  3. If all providers fail: return stale cache (marked stale) or error quote.
  4. Optional cross-validation: if two providers agree within 1%, increase confidence.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from app.modules.market_data.cache import MarketCache
from app.modules.market_data.providers import (
    AlphaVantageProvider,
    FinnhubProvider,
    FMPProvider,
    MarketDataProvider,
    MarketQuoteInternal,
    StooqProvider,
    YahooFinanceProvider,
)

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config" / "market_data_config.yaml"


@dataclass
class AssetConfig:
    """Full asset descriptor loaded from market_data_config.yaml."""
    internal_symbol: str    # e.g. "^IBEX" (used as API symbol for backward compat)
    name: str
    category: str
    asset_type: str
    currency: str
    provider_symbols: dict[str, str]   # {"stooq": "^ibex", "yahoo": "^IBEX", ...}


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_asset_catalog(config: dict) -> list[AssetConfig]:
    catalog = []
    for internal_sym, meta in config.get("symbol_mappings", {}).items():
        catalog.append(AssetConfig(
            internal_symbol=internal_sym,
            name=meta["name"],
            category=meta["category"],
            asset_type=meta["asset_type"],
            currency=meta["currency"],
            provider_symbols={
                k: v for k, v in meta.get("providers", {}).items() if v
            },
        ))
    return catalog


# Routing key from asset_type
def _route_key(asset_type: str, category: str) -> str:
    mapping = {
        "index": "indices",
        "stock": "stocks_us",
        "etf": "stocks_us",
        "forex": "forex",
        "crypto": "crypto",
        "commodity": "commodity",
        "bond": "bond",
        "volatility": "volatility",
    }
    # Distinguish EU/US/Asia stocks if needed (not currently used for indices)
    return mapping.get(asset_type, "indices")


# TTL seconds by asset_type
_TTL: dict[str, int] = {
    "crypto": 300,
    "index": 900,
    "stock": 900,
    "etf": 900,
    "forex": 900,
    "commodity": 900,
    "bond": 900,
    "volatility": 300,
}


class ProviderRouter:
    """Selects providers, manages cache, handles fallback and cross-validation."""

    def __init__(self) -> None:
        self._config = _load_config()
        self._catalog = _build_asset_catalog(self._config)
        self._routing = self._config.get("routing", {})
        self._cache = MarketCache()
        self._providers: dict[str, MarketDataProvider] = {
            "stooq": StooqProvider(),
            "yahoo": YahooFinanceProvider(),
            "finnhub": FinnhubProvider(),
            "alphavantage": AlphaVantageProvider(),
            "fmp": FMPProvider(),
        }

    @property
    def catalog(self) -> list[AssetConfig]:
        return self._catalog

    def get_quote(self, asset: AssetConfig) -> MarketQuoteInternal:
        ttl = _TTL.get(asset.asset_type, 900)

        # 1. Check cache
        cached_row = self._cache.get_quote(asset.internal_symbol)
        if cached_row and self._is_cache_fresh(cached_row, ttl):
            return self._row_to_internal(cached_row, asset)

        # 2. Try providers in routing order
        route_key = _route_key(asset.asset_type, asset.category)
        provider_names: list[str] = self._routing.get(route_key, ["yahoo"])

        last_error: Optional[str] = None
        for pname in provider_names:
            provider = self._providers.get(pname)
            if not provider or not provider.enabled:
                continue

            provider_symbol = asset.provider_symbols.get(pname, "")
            if not provider_symbol:
                continue  # no mapping for this provider

            if not provider.supports(asset.asset_type, provider_symbol):
                continue

            is_fb = pname in ("yahoo",) or pname not in ("stooq", "finnhub")
            try:
                quote = provider.get_quote(
                    internal_symbol=asset.internal_symbol,
                    provider_symbol=provider_symbol,
                    name=asset.name,
                    asset_type=asset.asset_type,
                    category=asset.category,
                    currency=asset.currency,
                    is_fallback=is_fb,
                )
                if quote.freshness_status == "error" or quote.price is None:
                    last_error = quote.warning
                    continue  # try next provider

                # Cross-validate if cached and prices differ >1%
                if cached_row and cached_row.get("price") and quote.price:
                    old_price = float(cached_row["price"])
                    diff_pct = abs(quote.price - old_price) / old_price * 100
                    if diff_pct > 1.0:
                        logger.info(
                            "provider_mismatch %s: old=%.4f new=%.4f diff=%.2f%%",
                            asset.internal_symbol, old_price, quote.price, diff_pct,
                        )
                        if not quote.warning:
                            quote.warning = (
                                f"Precio cambió {diff_pct:.1f}% respecto a dato anterior"
                            )
                        if diff_pct > 5.0:
                            quote.confidence_score = min(quote.confidence_score, 0.6)

                self._cache.put_quote(quote)
                self._cache.log_fetch(
                    provider=pname,
                    internal_symbol=asset.internal_symbol,
                    provider_symbol=provider_symbol,
                    asset_type=asset.asset_type,
                    cache_hit=False,
                    freshness_status=quote.freshness_status,
                    fallback_used=is_fb,
                )
                return quote

            except Exception as exc:
                logger.warning("Router: provider %s failed for %s: %s", pname, asset.internal_symbol, exc)
                last_error = str(exc)
                continue

        # 3. All providers failed — return stale cache or error
        if cached_row:
            stale = self._row_to_internal(cached_row, asset)
            stale.is_stale = True
            stale.freshness_status = "stale"
            stale.warning = f"Dato cacheado (todos los proveedores fallaron). Último: {last_error or 'error desconocido'}"
            return stale

        return MarketQuoteInternal(
            internal_symbol=asset.internal_symbol,
            provider_symbol=asset.provider_symbols.get("yahoo", asset.internal_symbol),
            name=asset.name,
            asset_type=asset.asset_type,
            category=asset.category,
            price=None,
            currency=asset.currency,
            change_absolute=None,
            change_percent=None,
            source="none",
            source_type="error",
            fetched_at=datetime.now(timezone.utc),
            market_time=None,
            market_status="unknown",
            freshness_status="error",
            delay_minutes=0,
            is_stale=False,
            is_fallback=False,
            confidence_score=0.0,
            warning=f"Sin datos disponibles. Último error: {last_error or 'desconocido'}",
            sparkline=[],
        )

    def _is_cache_fresh(self, row: dict, ttl: int) -> bool:
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
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age < ttl

    def _row_to_internal(self, row: dict, asset: AssetConfig) -> MarketQuoteInternal:
        """Convert a DuckDB cache row dict back to MarketQuoteInternal."""
        fetched_raw = row.get("fetched_at")
        fetched_at = (
            datetime.fromisoformat(str(fetched_raw))
            if fetched_raw else datetime.now(timezone.utc)
        )
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        market_time_raw = row.get("market_time")
        market_time: Optional[datetime] = None
        if market_time_raw:
            try:
                market_time = datetime.fromisoformat(str(market_time_raw))
                if market_time.tzinfo is None:
                    market_time = market_time.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        return MarketQuoteInternal(
            internal_symbol=asset.internal_symbol,
            provider_symbol=row.get("provider_symbol", ""),
            name=row.get("name", asset.name),
            asset_type=row.get("asset_type", asset.asset_type),
            category=row.get("category", asset.category),
            price=row.get("price"),
            currency=row.get("currency", asset.currency),
            change_absolute=row.get("change_absolute"),
            change_percent=row.get("change_percent"),
            source=row.get("source", "cache"),
            source_type=row.get("source_type", "cache"),
            fetched_at=fetched_at,
            market_time=market_time,
            market_status=row.get("market_status", "unknown"),
            freshness_status=row.get("freshness_status", "unknown"),
            delay_minutes=int(row.get("delay_minutes", 0)),
            is_stale=bool(row.get("is_stale", False)),
            is_fallback=bool(row.get("is_fallback", False)),
            confidence_score=float(row.get("confidence_score", 0.0)),
            warning=row.get("warning"),
            sparkline=row.get("sparkline") or [],
        )


# Module-level singleton and background refresh machinery
_router: Optional[ProviderRouter] = None
_router_lock = threading.Lock()
_refresh_lock = threading.Lock()


def get_router() -> ProviderRouter:
    global _router
    if _router is None:
        with _router_lock:
            if _router is None:
                _router = ProviderRouter()
    return _router


def _refresh_all(router: ProviderRouter) -> None:
    if not _refresh_lock.acquire(blocking=False):
        return
    try:
        for asset in router.catalog:
            router.get_quote(asset)
    finally:
        _refresh_lock.release()


_last_refresh: float = 0.0
_MIN_REFRESH_INTERVAL = 10.0  # seconds


def get_quotes(category: Optional[str] = None) -> list[dict]:
    """Public API: return quotes for all assets, optionally filtered by category.

    Drives background refresh when the global cache is stale.
    """
    global _last_refresh
    router = get_router()

    # Trigger background refresh if enough time has passed
    now = time.monotonic()
    if now - _last_refresh > _MIN_REFRESH_INTERVAL and not _refresh_lock.locked():
        _last_refresh = now
        cached = router._cache.get_all_quotes(category)
        if cached:
            # We have something cached — refresh in background
            threading.Thread(target=_refresh_all, args=(router,), daemon=True).start()
        else:
            # First call — block until we have at least some data
            _refresh_all(router)

    # Return from DuckDB cache (may include stale data)
    rows = router._cache.get_all_quotes(category)
    if not rows:
        # Fallback: blocking fetch if cache is still empty
        _refresh_all(router)
        rows = router._cache.get_all_quotes(category)

    return [_quote_row_to_api_dict(r) for r in rows]


def _quote_row_to_api_dict(row: dict) -> dict:
    """Convert cache row to the dict shape expected by QuoteOut."""
    return {
        "symbol": row.get("internal_symbol", ""),
        "name": row.get("name", ""),
        "category": row.get("category", ""),
        "price": row.get("price"),
        "change_pct": row.get("change_percent"),
        "change_absolute": row.get("change_absolute"),
        "currency": row.get("currency", ""),
        "sparkline": row.get("sparkline") or [],
        "last_updated": (
            row["fetched_at"].isoformat()
            if isinstance(row.get("fetched_at"), datetime)
            else str(row.get("fetched_at", ""))
        ),
        "market_open": row.get("market_status") == "open",
        "freshness_status": row.get("freshness_status", "unknown"),
        "source": row.get("source", "unknown"),
        "is_fallback": bool(row.get("is_fallback", False)),
        "is_stale": bool(row.get("is_stale", False)),
        "warning": row.get("warning"),
        "confidence_score": float(row.get("confidence_score", 0.0)),
    }
