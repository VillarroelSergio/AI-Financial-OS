"""ProviderRouter — parallel fetch + ConsensusEngine + Yahoo last resort.

Algorithm per asset:
  1. Check DuckDB cache. Return immediately if fresh (within TTL).
  2. Fetch all configured providers in parallel (ThreadPoolExecutor, 5s timeout).
     - Skip providers without symbol mapping for this asset.
     - Skip budget-aware providers if RequestBudget.can_request() is False.
     - Yahoo is only added to the pool if valid_provider_count == 0 after all others.
  3. Run ConsensusEngine.resolve() on collected quotes.
  4. Store consensus result in cache, return.
  5. If all providers fail AND cache stale: return stale cache with stale_cache_used warning.
"""
from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from app.modules.market_data.budget import get_budget, RequestBudget
from app.modules.market_data.cache import MarketCache
from app.modules.market_data.consensus import ConsensusEngine
from app.modules.market_data.providers import (
    AlphaVantageProvider,
    FinnhubProvider,
    FMPProvider,
    MarketDataProvider,
    MarketQuoteInternal,
    StooqProvider,
    TwelveDataProvider,
    YahooFinanceProvider,
)

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config" / "market_data_config.yaml"
_PROVIDER_FETCH_TIMEOUT = 5.0  # seconds per provider


@dataclass
class AssetConfig:
    """Full asset descriptor loaded from market_data_config.yaml."""
    internal_symbol: str
    name: str
    category: str
    asset_type: str
    currency: str
    provider_symbols: dict[str, str]


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
            provider_symbols={k: v for k, v in meta.get("providers", {}).items() if v},
        ))
    return catalog


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
    if asset_type == "stock" and "europe" in category:
        return "stocks_europe"
    return mapping.get(asset_type, "indices")


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
    """Parallel fetch + ConsensusEngine routing."""

    def __init__(self) -> None:
        self._config = _load_config()
        self._catalog = _build_asset_catalog(self._config)
        self._routing = self._config.get("routing", {})
        self._cache = MarketCache()
        self._consensus = ConsensusEngine()
        self._budget: RequestBudget = get_budget()
        self._providers: dict[str, MarketDataProvider] = {
            "stooq": StooqProvider(),
            "yahoo": YahooFinanceProvider(),
            "finnhub": FinnhubProvider(),
            "alphavantage": AlphaVantageProvider(),
            "fmp": FMPProvider(),
            "twelvedata": TwelveDataProvider(),
        }

    @property
    def catalog(self) -> list[AssetConfig]:
        return self._catalog

    def get_quote(self, asset: AssetConfig) -> MarketQuoteInternal:
        ttl = _TTL.get(asset.asset_type, 900)

        # 1. Cache check
        cached_row = self._cache.get_quote(asset.internal_symbol)
        if cached_row and self._is_cache_fresh(cached_row, ttl):
            return self._row_to_internal(cached_row, asset)

        # 2. Build provider pool (excluding Yahoo)
        route_key = _route_key(asset.asset_type, asset.category)
        route = self._routing.get(route_key, {})

        primary_name: str = route.get("primary", "stooq")
        validators: list[str] = route.get("validators", [])
        budget_aware: list[str] = route.get("budget_aware", [])
        last_resort: str = route.get("last_resort", "yahoo")

        all_providers = [primary_name] + [v for v in validators if v != primary_name]
        # Add budget_aware providers if not already listed and if budget allows
        for ba in budget_aware:
            if ba not in all_providers:
                all_providers.append(ba)

        fetch_pool = []
        for pname in all_providers:
            if pname == last_resort:
                continue  # Yahoo guard — added only if needed
            provider = self._providers.get(pname)
            if not provider or not provider.enabled:
                continue
            sym = asset.provider_symbols.get(pname, "")
            if not sym:
                continue
            if not provider.supports(asset.asset_type, sym):
                continue
            if pname in budget_aware and not self._budget.can_request(pname):
                logger.debug("Skipping %s for %s: budget_exhausted", pname, asset.internal_symbol)
                continue
            fetch_pool.append((pname, provider, sym))

        # 3. Parallel fetch
        quotes: list[MarketQuoteInternal] = []
        if fetch_pool:
            with ThreadPoolExecutor(max_workers=len(fetch_pool)) as executor:
                futures = {
                    executor.submit(
                        provider.get_quote,
                        asset.internal_symbol, sym, asset.name,
                        asset.asset_type, asset.category, asset.currency,
                        is_fallback=(pname != primary_name),
                    ): pname
                    for pname, provider, sym in fetch_pool
                }
                for future in as_completed(futures, timeout=_PROVIDER_FETCH_TIMEOUT + 1):
                    pname = futures[future]
                    try:
                        q = future.result(timeout=_PROVIDER_FETCH_TIMEOUT)
                        quotes.append(q)
                        self._cache.log_fetch(
                            provider=pname,
                            internal_symbol=asset.internal_symbol,
                            provider_symbol=asset.provider_symbols.get(pname, ""),
                            asset_type=asset.asset_type,
                            cache_hit=False,
                            freshness_status=q.freshness_status,
                            fallback_used=(pname != primary_name),
                        )
                    except Exception as exc:
                        logger.warning("Router: %s failed for %s: %s", pname, asset.internal_symbol, exc)

        # 4. Yahoo last resort — only if no valid price found
        valid_count = sum(1 for q in quotes if q.price is not None and q.freshness_status != "error")
        if valid_count == 0:
            yahoo_provider = self._providers.get(last_resort)
            yahoo_sym = asset.provider_symbols.get(last_resort, "")
            if yahoo_provider and yahoo_provider.enabled and yahoo_sym:
                try:
                    yq = yahoo_provider.get_quote(
                        asset.internal_symbol, yahoo_sym, asset.name,
                        asset.asset_type, asset.category, asset.currency,
                        is_fallback=True,
                    )
                    if yq.price is not None:
                        yq.warning = "yahoo_last_resort"
                    quotes.append(yq)
                    self._cache.log_fetch(
                        provider=last_resort,
                        internal_symbol=asset.internal_symbol,
                        provider_symbol=yahoo_sym,
                        asset_type=asset.asset_type,
                        cache_hit=False,
                        freshness_status=yq.freshness_status,
                        fallback_used=True,
                    )
                except Exception as exc:
                    logger.warning("Router: yahoo last resort failed for %s: %s", asset.internal_symbol, exc)

        # 5. ConsensusEngine resolution
        result = self._consensus.resolve(quotes, asset.asset_type, primary_name)

        # 6. Log decision
        logger.debug(
            "consensus_decision symbol=%s source=%s method=%s confidence=%.2f "
            "valid=%d/%d outliers=%s warnings=%s reason=%s",
            asset.internal_symbol, result.selected_source, result.consensus_method,
            result.confidence_score, result.valid_provider_count, result.provider_count,
            result.outliers, result.warnings, result.reason,
        )

        if result.price is None:
            # All failed — return stale cache if available
            if cached_row:
                stale = self._row_to_internal(cached_row, asset)
                stale.is_stale = True
                stale.freshness_status = "stale"
                stale.warning = "stale_cache_used"
                return stale
            # Build error quote
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
                warning="; ".join(result.warnings) or "Sin datos disponibles",
                sparkline=[],
            )

        # 7. Build final MarketQuoteInternal from consensus result
        # Take sparkline and change fields from the selected-source quote or primary
        source_quote = next(
            (q for q in quotes if q.source == result.selected_source),
            next((q for q in quotes if q.price is not None), quotes[0] if quotes else None),
        )
        sparkline = source_quote.sparkline if source_quote else []
        change_absolute = source_quote.change_absolute if source_quote else None
        change_percent = source_quote.change_percent if source_quote else None
        market_time = source_quote.market_time if source_quote else None
        market_status = source_quote.market_status if source_quote else "unknown"

        yahoo_last_resort_used = any(q.warning == "yahoo_last_resort" for q in quotes)
        all_warnings = list(result.warnings)
        if yahoo_last_resort_used and "yahoo_last_resort" not in all_warnings:
            all_warnings.append("yahoo_last_resort")
        warning_str = "; ".join(all_warnings) if all_warnings else None

        final_quote = MarketQuoteInternal(
            internal_symbol=asset.internal_symbol,
            provider_symbol=asset.provider_symbols.get(result.selected_source, asset.internal_symbol),
            name=asset.name,
            asset_type=asset.asset_type,
            category=asset.category,
            price=result.price,
            currency=asset.currency,
            change_absolute=change_absolute,
            change_percent=change_percent,
            source=result.selected_source,
            source_type=result.source_type,
            fetched_at=datetime.now(timezone.utc),
            market_time=market_time,
            market_status=market_status,
            freshness_status=result.freshness_status,
            delay_minutes=15,
            is_stale=False,
            is_fallback=(result.selected_source != primary_name),
            confidence_score=result.confidence_score,
            warning=warning_str,
            sparkline=sparkline,
        )

        self._cache.put_quote(final_quote)
        return final_quote

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
        return (datetime.now(timezone.utc) - cached_at).total_seconds() < ttl

    def _row_to_internal(self, row: dict, asset: AssetConfig) -> MarketQuoteInternal:
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
