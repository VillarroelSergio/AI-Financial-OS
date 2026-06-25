from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


def _cached_row(date_str: str) -> dict:
    return {
        "cached_at": datetime.fromisoformat(f"{date_str}T10:00:00+00:00"),
        "price": 100.0,
    }


def _make_service():
    from app.modules.investments.market_data.eod_service import EodMarketService
    return EodMarketService()


def test_cache_hit_same_day_skips_network():
    """Si el caché tiene datos de hoy, no se llama al router."""
    service = _make_service()
    today = datetime.now(timezone.utc).date().isoformat()

    mock_router = MagicMock()
    mock_asset = MagicMock()
    mock_asset.internal_symbol = "IBEX35"
    mock_router.catalog = [mock_asset]

    with patch("app.modules.investments.market_data.eod_service.get_router", return_value=mock_router):
        with patch.object(service._cache, "get_quote", return_value=_cached_row(today)):
            service.ensure_today()

    mock_router.get_quote.assert_not_called()


def test_cache_miss_fetches_with_eod_only():
    """Sin caché, llama al router con force_refresh=True y eod_only=True."""
    service = _make_service()

    mock_router = MagicMock()
    mock_asset = MagicMock()
    mock_asset.internal_symbol = "IBEX35"
    mock_router.catalog = [mock_asset]

    with patch("app.modules.investments.market_data.eod_service.get_router", return_value=mock_router):
        with patch.object(service._cache, "get_quote", return_value=None):
            service.ensure_today()

    mock_router.get_quote.assert_called_once_with(mock_asset, force_refresh=True, eod_only=True)


def test_stale_cache_from_yesterday_fetches():
    """Datos de ayer deben refrescarse."""
    service = _make_service()

    mock_router = MagicMock()
    mock_asset = MagicMock()
    mock_asset.internal_symbol = "SP500"
    mock_router.catalog = [mock_asset]

    with patch("app.modules.investments.market_data.eod_service.get_router", return_value=mock_router):
        with patch.object(service._cache, "get_quote", return_value=_cached_row("2020-01-01")):
            service.ensure_today()

    mock_router.get_quote.assert_called_once()


def test_provider_failure_does_not_abort_remaining_assets():
    """Fallo en un activo no impide procesar los demás."""
    service = _make_service()

    mock_router = MagicMock()
    asset_a = MagicMock(); asset_a.internal_symbol = "IBEX35"
    asset_b = MagicMock(); asset_b.internal_symbol = "SP500"
    mock_router.catalog = [asset_a, asset_b]
    mock_router.get_quote.side_effect = [RuntimeError("timeout"), MagicMock()]

    with patch("app.modules.investments.market_data.eod_service.get_router", return_value=mock_router):
        with patch.object(service._cache, "get_quote", return_value=None):
            service.ensure_today()  # no debe lanzar excepción

    assert mock_router.get_quote.call_count == 2


def test_concurrent_calls_run_only_once():
    """Llamadas concurrentes no lanzan fetches duplicados."""
    import threading
    import time

    service = _make_service()
    call_count = 0

    def slow_fetch(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        time.sleep(0.05)
        return MagicMock()

    mock_router = MagicMock()
    mock_asset = MagicMock(); mock_asset.internal_symbol = "IBEX35"
    mock_router.catalog = [mock_asset]
    mock_router.get_quote.side_effect = slow_fetch

    with patch("app.modules.investments.market_data.eod_service.get_router", return_value=mock_router):
        with patch.object(service._cache, "get_quote", return_value=None):
            t1 = threading.Thread(target=service.ensure_today)
            t2 = threading.Thread(target=service.ensure_today)
            t1.start(); t2.start()
            t1.join(); t2.join()

    assert call_count == 1


def test_provider_router_eod_only_filters_to_stooq():
    """Con eod_only=True, solo Stooq entra en el fetch pool."""
    from app.modules.investments.market_data.router import ProviderRouter, AssetConfig

    router = ProviderRouter()
    asset = AssetConfig(
        internal_symbol="IBEX35",
        name="IBEX 35",
        category="indices_eu",
        asset_type="index",
        currency="EUR",
        provider_symbols={"stooq": "^ibex", "yahoo": "^IBEX", "twelvedata": "IBEX35"},
    )

    called_providers: list[str] = []
    original_get_quote = router._providers["stooq"].get_quote

    def tracking_stooq(*args, **kwargs):
        called_providers.append("stooq")
        return original_get_quote(*args, **kwargs)

    for name in ["alphavantage", "finnhub", "fmp", "twelvedata", "yahoo"]:
        router._providers[name].get_quote = lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError(f"{name} should not be called in eod_only mode")
        )
    router._providers["stooq"].get_quote = tracking_stooq

    router.get_quote(asset, force_refresh=True, eod_only=True)
    assert called_providers == ["stooq"]
