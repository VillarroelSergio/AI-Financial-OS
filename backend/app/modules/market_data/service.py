"""Market data service — thin adapter between routes and ProviderRouter.

The old monolithic service (single yfinance, in-memory cache) is replaced
by the multi-provider ProviderRouter backed by DuckDB cache.

Public API surface is preserved:
    get_quotes(category: str | None = None) -> list[dict]
"""
from app.modules.market_data.router import get_quotes  # noqa: F401 — re-exported

# ASSET_CATALOG is now owned by the router (loaded from market_data_config.yaml).
# Keep a reference here for tests that import it.
def _get_catalog():
    from app.modules.market_data.router import get_router
    return get_router().catalog

# Expose for backward-compat in tests
@property
def ASSET_CATALOG():
    return _get_catalog()
