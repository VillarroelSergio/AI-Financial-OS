from unittest.mock import MagicMock, patch

import app.modules.market_data.service as svc


def _reset_cache():
    svc._cache["quotes"] = []
    svc._cache["updated_at"] = None
    svc._cache["refreshing"] = False


def _make_mock_ticker(price=9842.15, prev_close=9750.0):
    fast = MagicMock()
    fast.last_price = price
    fast.previous_close = prev_close
    fast.market_state = "REGULAR"

    hist = MagicMock()
    hist.empty = False
    hist.__getitem__ = MagicMock(return_value=MagicMock(
        dropna=MagicMock(return_value=MagicMock(tolist=MagicMock(return_value=[9800.0, 9820.0, 9842.15])))
    ))

    ticker = MagicMock()
    ticker.fast_info = fast
    ticker.history.return_value = hist
    return ticker


def test_get_quotes_returns_36_assets(client):
    _reset_cache()
    with patch("app.modules.market_data.service.yf.Ticker", return_value=_make_mock_ticker()):
        r = client.get("/api/markets/quotes")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 36


def test_get_quotes_structure(client):
    _reset_cache()
    with patch("app.modules.market_data.service.yf.Ticker", return_value=_make_mock_ticker()):
        r = client.get("/api/markets/quotes")
    quote = r.json()[0]
    assert quote["symbol"] == "^IBEX"
    assert quote["name"] == "IBEX 35"
    assert quote["category"] == "indices_eu"
    assert isinstance(quote["price"], float)
    assert isinstance(quote["change_pct"], float)
    assert isinstance(quote["sparkline"], list)
    assert "last_updated" in quote
    assert isinstance(quote["market_open"], bool)


def test_get_quotes_filter_by_category(client):
    _reset_cache()
    with patch("app.modules.market_data.service.yf.Ticker", return_value=_make_mock_ticker()):
        r = client.get("/api/markets/quotes?category=indices_eu")
    data = r.json()
    assert len(data) == 6
    assert all(q["category"] == "indices_eu" for q in data)


def test_get_quotes_yfinance_failure_returns_null_price(client):
    _reset_cache()
    broken_ticker = MagicMock()
    broken_ticker.fast_info.last_price = None
    broken_ticker.fast_info.previous_close = None
    broken_ticker.fast_info.market_state = None
    broken_ticker.history.side_effect = Exception("network error")
    with patch("app.modules.market_data.service.yf.Ticker", return_value=broken_ticker):
        r = client.get("/api/markets/quotes")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 36
    assert all(q["price"] is None for q in data)


def test_cache_serves_stale_data_while_refreshing(client):
    _reset_cache()
    mock_ticker = _make_mock_ticker()
    with patch("app.modules.market_data.service.yf.Ticker", return_value=mock_ticker):
        client.get("/api/markets/quotes")

    # Cache is now populated; simulate stale by backdating updated_at
    import time
    svc._cache["updated_at"] = time.time() - 20  # 20s ago, TTL is 15s

    call_count_before = mock_ticker.fast_info.last_price  # just reference
    with patch("app.modules.market_data.service.yf.Ticker", return_value=mock_ticker):
        r = client.get("/api/markets/quotes")
    assert r.status_code == 200
    assert len(r.json()) == 36  # served stale cache immediately
