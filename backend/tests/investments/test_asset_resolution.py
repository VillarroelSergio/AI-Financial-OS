"""resolve_asset debe reconocer tanto los nombres del registro conocido como
tickers arbitrarios via el fallback de yfinance (bug: antes solo miraba el
registro de 19 nombres y rechazaba tickers reales como AAPL o IBE.MC)."""
from unittest.mock import patch

from app.modules.investments.asset_resolution import TickerCandidate, resolve_asset


def test_resolve_asset_known_name():
    resolution = resolve_asset("iberdrola")
    assert resolution.status == "resolved"
    assert resolution.selected.ticker == "IBE.MC"


def test_resolve_asset_unknown_ticker_uses_yfinance_fallback():
    fake_candidate = TickerCandidate(
        ticker="AAPL", yfinance_symbol="AAPL", name="Apple Inc.",
        exchange="NASDAQ", currency="USD", confidence=0.8,
    )
    with patch(
        "app.modules.investments.asset_resolution.search_assets",
        return_value=[fake_candidate],
    ):
        resolution = resolve_asset("AAPL")
    assert resolution.status == "resolved"
    assert resolution.selected.ticker == "AAPL"


def test_resolve_asset_unavailable_when_nothing_found():
    with patch("app.modules.investments.asset_resolution.search_assets", return_value=[]):
        resolution = resolve_asset("xyz-no-existe-123")
    assert resolution.status == "unavailable"
    assert resolution.selected is None
