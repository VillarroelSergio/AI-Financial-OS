"""Tests for market_data service — Fase 4 Market Watch."""
from unittest.mock import MagicMock, patch

import pytest

from app.modules.market_data.schemas import QuoteOut
import app.modules.market_data.service as _svc
from app.modules.market_data.service import ASSET_CATALOG, get_quotes


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset module-level cache before each test so tests are independent."""
    _svc._cache["quotes"] = []
    _svc._cache["updated_at"] = None
    # Release lock if somehow held
    if _svc._refresh_lock.locked():
        try:
            _svc._refresh_lock.release()
        except RuntimeError:
            pass
    yield


# ---------------------------------------------------------------------------
# Catalog structure
# ---------------------------------------------------------------------------

def test_asset_catalog_has_36_assets():
    assert len(ASSET_CATALOG) == 36


def test_asset_catalog_category_counts():
    from collections import Counter
    counts = Counter(a.category for a in ASSET_CATALOG)
    assert counts["indices_eu"] == 6
    assert counts["indices_us"] == 4
    assert counts["indices_asia"] == 4
    assert counts["crypto"] == 4
    assert counts["fx"] == 6
    assert counts["bonds"] == 5
    assert counts["commodities"] == 6
    assert counts["volatility"] == 1


# ---------------------------------------------------------------------------
# get_quotes structure
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "symbol", "name", "category", "price", "change_pct",
    "currency", "sparkline", "last_updated", "market_open",
}


def _make_mock_ticker(price: float = 100.0, prev_close: float = 99.0):
    """Return a mock yfinance.Ticker with controllable fast_info."""
    ticker = MagicMock()
    ticker.fast_info.last_price = price
    ticker.fast_info.previous_close = prev_close
    ticker.fast_info.market_state = "REGULAR"
    hist = MagicMock()
    hist.empty = True
    ticker.history.return_value = hist
    return ticker


def test_get_quotes_structure():
    with patch("app.modules.market_data.service.yf.Ticker", return_value=_make_mock_ticker()):
        quotes = get_quotes()

    assert len(quotes) == 36
    for q in quotes:
        assert REQUIRED_KEYS == set(q.keys()), f"Missing/extra keys in {q['symbol']}"
        # Validate round-trips through QuoteOut
        QuoteOut(**q)


def test_get_quotes_filter_by_category():
    with patch("app.modules.market_data.service.yf.Ticker", return_value=_make_mock_ticker()):
        quotes = get_quotes("crypto")

    assert len(quotes) == 4
    for q in quotes:
        assert q["category"] == "crypto"


# ---------------------------------------------------------------------------
# Error handling: yfinance failure → null price
# ---------------------------------------------------------------------------

def test_get_quotes_yfinance_failure_returns_null_price():
    """When yfinance raises for a ticker, that quote has price=None and sparkline=[]."""
    failing_symbol = "BTC-USD"

    def ticker_factory(symbol):
        if symbol == failing_symbol:
            raise Exception("network error")
        return _make_mock_ticker()

    with patch("app.modules.market_data.service.yf.Ticker", side_effect=ticker_factory):
        quotes = get_quotes()

    btc = next(q for q in quotes if q["symbol"] == failing_symbol)
    assert btc["price"] is None
    assert btc["change_pct"] is None
    assert btc["sparkline"] == []
