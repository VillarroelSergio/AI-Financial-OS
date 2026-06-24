"""Tests for market data — Fase 4.5 Multi-Provider Architecture."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.modules.market_data.providers.base import MarketQuoteInternal
from app.modules.market_data.providers.stooq import StooqProvider
from app.modules.market_data.providers.yahoo import YahooFinanceProvider
from app.modules.market_data.providers.alphavantage import AlphaVantageProvider
from app.modules.market_data.providers.finnhub import FinnhubProvider
from app.modules.market_data.providers.fmp import FMPProvider
from app.modules.market_data.router import ProviderRouter, _quote_row_to_api_dict
from app.modules.market_data.schemas import QuoteOut


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_quote(
    symbol: str = "^IBEX",
    price: float = 9800.0,
    change_pct: float = 0.5,
    source: str = "stooq",
    freshness: str = "eod",
    is_fallback: bool = False,
    warning: str | None = None,
) -> MarketQuoteInternal:
    return MarketQuoteInternal(
        internal_symbol=symbol,
        provider_symbol=symbol.lower(),
        name="Test Asset",
        asset_type="index",
        category="indices_eu",
        price=price,
        currency="EUR",
        change_absolute=price * change_pct / 100 if price is not None else None,
        change_percent=change_pct,
        source=source,
        source_type="eod",
        fetched_at=datetime.now(timezone.utc),
        market_time=None,
        market_status="closed",
        freshness_status=freshness,
        delay_minutes=0,
        is_stale=False,
        is_fallback=is_fallback,
        confidence_score=0.85,
        warning=warning,
        sparkline=[9750.0, 9780.0, 9800.0],
    )


# ─── 1. Stooq CSV parsing ────────────────────────────────────────────────────

class TestStooqProvider:
    def test_supports_index(self):
        p = StooqProvider()
        assert p.supports("index", "^ibex")

    def test_supports_forex(self):
        p = StooqProvider()
        assert p.supports("forex", "eurusd")

    def test_does_not_support_stock(self):
        p = StooqProvider()
        assert not p.supports("stock", "AAPL")

    def test_requires_no_api_key(self):
        assert not StooqProvider.requires_api_key

    def test_get_quote_network_failure_returns_error(self):
        p = StooqProvider()
        with patch("app.modules.market_data.providers.stooq.requests.get", side_effect=Exception("network error")):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.freshness_status == "error"
        assert result.price is None
        assert "Stooq" in (result.warning or "")

    def test_get_quote_timeout_returns_error(self):
        import requests as req
        p = StooqProvider()
        with patch("app.modules.market_data.providers.stooq.requests.get", side_effect=req.exceptions.Timeout):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.freshness_status == "error"
        assert "timeout" in (result.warning or "").lower()

    def test_get_quote_empty_response_returns_error(self):
        p = StooqProvider()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Date,Open,High,Low,Close,Volume\n"  # header only, no data
        with patch("app.modules.market_data.providers.stooq.requests.get", return_value=mock_resp):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.freshness_status == "error"

    def test_get_quote_valid_csv_parses_correctly(self):
        p = StooqProvider()
        csv_data = (
            "Date,Open,High,Low,Close,Volume\n"
            "2024-01-14,9800.0,9850.0,9780.0,9820.0,0\n"
            "2024-01-15,9820.0,9900.0,9810.0,9876.0,0\n"
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = csv_data
        with patch("app.modules.market_data.providers.stooq.requests.get", return_value=mock_resp):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.price == pytest.approx(9876.0)
        assert result.change_percent is not None
        assert len(result.sparkline) == 2
        assert result.source == "stooq"

    def test_get_quote_na_values_return_error(self):
        p = StooqProvider()
        csv_data = "Date,Open,High,Low,Close,Volume\n2024-01-15,N/A,N/A,N/A,N/A,0\n"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = csv_data
        with patch("app.modules.market_data.providers.stooq.requests.get", return_value=mock_resp):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.freshness_status == "error"


# ─── 2. Yahoo fallback ───────────────────────────────────────────────────────

class TestYahooFinanceProvider:
    def test_supports_any_asset_type(self):
        p = YahooFinanceProvider()
        for at in ("index", "stock", "forex", "crypto", "bond", "commodity"):
            assert p.supports(at, "ANY")

    def test_always_marks_is_fallback_true(self):
        mock_ticker = MagicMock()
        mock_ticker.fast_info.last_price = 100.0
        mock_ticker.fast_info.previous_close = 99.0
        mock_ticker.fast_info.market_state = "REGULAR"
        mock_ticker.history.return_value = MagicMock(empty=True)
        p = YahooFinanceProvider()
        with patch("app.modules.market_data.providers.yahoo.yf.Ticker", return_value=mock_ticker):
            result = p.get_quote("^IBEX", "^IBEX", "IBEX 35", "index", "indices_eu", "EUR")
        # Yahoo is now primary source; is_fallback depends on router position, not provider default
        assert result.is_fallback is False

    def test_freshness_is_never_live(self):
        mock_ticker = MagicMock()
        mock_ticker.fast_info.last_price = 100.0
        mock_ticker.fast_info.previous_close = 99.0
        mock_ticker.fast_info.market_state = "REGULAR"
        mock_ticker.history.return_value = MagicMock(empty=True)
        p = YahooFinanceProvider()
        with patch("app.modules.market_data.providers.yahoo.yf.Ticker", return_value=mock_ticker):
            result = p.get_quote("^IBEX", "^IBEX", "IBEX 35", "index", "indices_eu", "EUR")
        assert result.freshness_status != "live", "Yahoo must never claim 'live' freshness"

    def test_yahoo_failure_returns_error_quote(self):
        p = YahooFinanceProvider()
        with patch("app.modules.market_data.providers.yahoo.yf.Ticker", side_effect=Exception("net err")):
            result = p.get_quote("X", "X", "X", "index", "indices_eu", "EUR")
        assert result.freshness_status == "error"
        assert result.price is None


# ─── 3. Optional providers without API key ───────────────────────────────────

class TestOptionalProvidersWithoutApiKey:
    def test_alphavantage_disabled_without_key(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        p = AlphaVantageProvider()
        assert not p.enabled

    def test_alphavantage_supports_nothing_when_disabled(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        p = AlphaVantageProvider()
        assert not p.supports("stock", "AAPL")

    def test_alphavantage_returns_error_quote_when_disabled(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        p = AlphaVantageProvider()
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")
        assert result.freshness_status == "error"
        assert result.price is None

    def test_finnhub_disabled_without_key(self, monkeypatch):
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        p = FinnhubProvider()
        assert not p.enabled

    def test_finnhub_returns_error_quote_when_disabled(self, monkeypatch):
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        p = FinnhubProvider()
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")
        assert result.freshness_status == "error"

    def test_fmp_disabled_without_key(self, monkeypatch):
        monkeypatch.delenv("FMP_API_KEY", raising=False)
        p = FMPProvider()
        assert not p.enabled

    def test_fmp_returns_error_quote_when_disabled(self, monkeypatch):
        monkeypatch.delenv("FMP_API_KEY", raising=False)
        p = FMPProvider()
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")
        assert result.freshness_status == "error"


# ─── 4. Provider routing ─────────────────────────────────────────────────────

class TestProviderRouting:
    def _make_router_with_mock_providers(
        self, stooq_result=None, yahoo_result=None
    ) -> ProviderRouter:
        router = ProviderRouter.__new__(ProviderRouter)
        routing = {
            "indices": ["stooq", "yahoo"],
            "forex": ["stooq", "yahoo"],
            "crypto": ["yahoo"],
            "commodity": ["stooq", "yahoo"],
            "bond": ["stooq", "yahoo"],
            "volatility": ["stooq", "yahoo"],
            "stocks_us": ["yahoo"],
        }
        router._config = {"routing": routing}
        router._routing = routing
        router._catalog = []
        from app.modules.market_data.cache import MarketCache
        router._cache = MagicMock(spec=MarketCache)
        router._cache.get_quote.return_value = None  # no cache by default

        mock_stooq = MagicMock()
        mock_stooq.enabled = True
        mock_stooq.name = "stooq"
        mock_stooq.supports.return_value = True
        mock_stooq.get_quote.return_value = stooq_result or _make_quote(source="stooq")

        mock_yahoo = MagicMock()
        mock_yahoo.enabled = True
        mock_yahoo.name = "yahoo"
        mock_yahoo.supports.return_value = True
        mock_yahoo.get_quote.return_value = yahoo_result or _make_quote(
            source="yahoo", is_fallback=True
        )

        router._providers = {"stooq": mock_stooq, "yahoo": mock_yahoo}
        return router

    def _make_asset(self, asset_type: str = "index") -> "AssetConfig":
        from app.modules.market_data.router import AssetConfig
        return AssetConfig(
            internal_symbol="^IBEX",
            name="IBEX 35",
            category="indices_eu",
            asset_type=asset_type,
            currency="EUR",
            provider_symbols={"stooq": "^ibex", "yahoo": "^IBEX"},
        )

    def test_index_uses_stooq_first(self):
        router = self._make_router_with_mock_providers()
        asset = self._make_asset("index")
        result = router.get_quote(asset)
        assert result.source == "stooq"
        router._providers["stooq"].get_quote.assert_called_once()

    def test_falls_back_to_yahoo_when_stooq_fails(self):
        error_quote = _make_quote(source="stooq", freshness="error", price=None)
        error_quote.price = None
        error_quote.freshness_status = "error"
        router = self._make_router_with_mock_providers(stooq_result=error_quote)
        router._providers["stooq"].get_quote.return_value = error_quote
        asset = self._make_asset("index")
        result = router.get_quote(asset)
        assert result.source == "yahoo"

    def test_stale_cache_returned_when_all_providers_fail(self):
        router = self._make_router_with_mock_providers()
        # Make cache return a stale row
        stale_row = {
            "internal_symbol": "^IBEX", "name": "IBEX 35", "category": "indices_eu",
            "asset_type": "index", "price": 9800.0, "change_absolute": 10.0,
            "change_percent": 0.1, "currency": "EUR", "source": "stooq",
            "source_type": "eod", "freshness_status": "eod", "delay_minutes": 0,
            "is_stale": False, "is_fallback": False, "confidence_score": 0.85,
            "warning": None, "sparkline": [], "market_status": "closed",
            "market_time": None, "provider_symbol": "^ibex",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "cached_at": "2000-01-01T00:00:00",  # very old → stale
        }
        router._cache.get_quote.return_value = stale_row
        # Make all providers fail
        error_q = _make_quote(freshness="error", price=None)
        error_q.price = None
        error_q.freshness_status = "error"
        router._providers["stooq"].get_quote.return_value = error_q
        router._providers["yahoo"].get_quote.return_value = error_q

        asset = self._make_asset("index")
        result = router.get_quote(asset)
        assert result.is_stale is True
        assert result.freshness_status == "stale"
        assert result.price == 9800.0


# ─── 5. Cache TTL ────────────────────────────────────────────────────────────

class TestCacheTTL:
    def test_fresh_cache_is_returned_without_calling_provider(self):
        from app.modules.market_data.router import ProviderRouter, AssetConfig
        router = ProviderRouter.__new__(ProviderRouter)
        router._config = {"routing": {"indices": ["stooq", "yahoo"]}}
        router._catalog = []

        fresh_row = {
            "internal_symbol": "^IBEX", "name": "IBEX 35", "category": "indices_eu",
            "asset_type": "index", "price": 9800.0, "change_absolute": 10.0,
            "change_percent": 0.1, "currency": "EUR", "source": "stooq",
            "source_type": "eod", "freshness_status": "eod", "delay_minutes": 0,
            "is_stale": False, "is_fallback": False, "confidence_score": 0.85,
            "warning": None, "sparkline": [], "market_status": "closed",
            "market_time": None, "provider_symbol": "^ibex",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "cached_at": datetime.now(timezone.utc).isoformat(),  # just now → fresh
        }
        from app.modules.market_data.cache import MarketCache
        router._cache = MagicMock(spec=MarketCache)
        router._cache.get_quote.return_value = fresh_row
        router._providers = {}

        asset = AssetConfig(
            internal_symbol="^IBEX", name="IBEX 35", category="indices_eu",
            asset_type="index", currency="EUR",
            provider_symbols={"stooq": "^ibex", "yahoo": "^IBEX"},
        )
        result = router.get_quote(asset)
        assert result.price == 9800.0
        # providers were never called
        assert router._providers == {}


# ─── 6. Freshness status rules ───────────────────────────────────────────────

class TestFreshnessStatus:
    def test_yahoo_never_returns_live(self):
        mock_ticker = MagicMock()
        mock_ticker.fast_info.last_price = 100.0
        mock_ticker.fast_info.previous_close = 99.0
        mock_ticker.fast_info.market_state = "REGULAR"
        mock_ticker.history.return_value = MagicMock(empty=True)
        p = YahooFinanceProvider()
        with patch("app.modules.market_data.providers.yahoo.yf.Ticker", return_value=mock_ticker):
            result = p.get_quote("X", "X", "X", "index", "indices_eu", "EUR")
        assert result.freshness_status not in ("live",)

    def test_stooq_returns_eod_for_old_data(self):
        p = StooqProvider()
        csv_data = (
            "Date,Open,High,Low,Close,Volume\n"
            "2024-01-10,9800.0,9850.0,9780.0,9820.0,0\n"
            "2024-01-11,9820.0,9900.0,9810.0,9876.0,0\n"
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = csv_data
        with patch("app.modules.market_data.providers.stooq.requests.get", return_value=mock_resp):
            result = p.get_quote("^IBEX", "^ibex", "IBEX 35", "index", "indices_eu", "EUR")
        # Old data → eod
        assert result.freshness_status == "eod"


# ─── 7. QuoteOut schema validation ───────────────────────────────────────────

class TestQuoteOutSchema:
    def test_quote_out_has_all_required_fields(self):
        row = {
            "symbol": "^IBEX", "name": "IBEX 35", "category": "indices_eu",
            "price": 9800.0, "change_pct": 0.5, "change_absolute": 49.0,
            "currency": "EUR", "sparkline": [9750.0, 9800.0],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "market_open": False,
            "freshness_status": "eod", "source": "stooq",
            "is_fallback": False, "is_stale": False,
            "warning": None, "confidence_score": 0.85,
        }
        q = QuoteOut(**row)
        assert q.symbol == "^IBEX"
        assert q.freshness_status == "eod"
        assert q.source == "stooq"
        assert q.is_fallback is False

    def test_quote_to_api_dict_shape(self):
        row = {
            "internal_symbol": "^IBEX", "name": "IBEX 35", "category": "indices_eu",
            "asset_type": "index", "price": 9800.0, "change_absolute": 49.0,
            "change_percent": 0.5, "currency": "EUR", "source": "stooq",
            "source_type": "eod", "freshness_status": "eod",
            "delay_minutes": 0, "is_stale": False, "is_fallback": False,
            "confidence_score": 0.85, "warning": None, "sparkline": [],
            "market_status": "closed", "market_time": None, "provider_symbol": "^ibex",
            "fetched_at": datetime.now(timezone.utc),
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        d = _quote_row_to_api_dict(row)
        # Validate it fits QuoteOut schema
        QuoteOut(**d)
        assert d["freshness_status"] == "eod"
        assert d["source"] == "stooq"


# ─── 8. Symbol mapping coverage ──────────────────────────────────────────────

class TestSymbolMappings:
    def test_all_36_assets_present_in_catalog(self):
        router = ProviderRouter()
        assert len(router.catalog) == 36

    def test_all_assets_have_yahoo_mapping(self):
        router = ProviderRouter()
        for asset in router.catalog:
            assert "yahoo" in asset.provider_symbols, (
                f"{asset.internal_symbol} missing yahoo mapping"
            )

    def test_index_assets_have_stooq_mapping(self):
        router = ProviderRouter()
        index_assets = [a for a in router.catalog if a.asset_type == "index"]
        for asset in index_assets:
            assert "stooq" in asset.provider_symbols, (
                f"Index {asset.internal_symbol} missing stooq mapping"
            )

    def test_no_manual_csv_provider_in_catalog(self):
        """ManualCsvProvider must never exist — data comes exclusively from web providers."""
        router = ProviderRouter()
        for pname in router._providers:
            assert "csv" not in pname.lower(), (
                f"Provider '{pname}' looks like a manual CSV importer — not allowed"
            )

    def test_category_counts(self):
        from collections import Counter
        router = ProviderRouter()
        counts = Counter(a.category for a in router.catalog)
        assert counts["indices_eu"] == 6
        assert counts["indices_us"] == 4
        assert counts["indices_asia"] == 4
        assert counts["crypto"] == 4
        assert counts["fx"] == 6
        assert counts["bonds"] == 5
        assert counts["commodities"] == 6
        assert counts["volatility"] == 1


# ─── 9. Rate limit handling ──────────────────────────────────────────────────

class TestRateLimiting:
    def test_alphavantage_rate_limit_returns_error(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "testkey")
        p = AlphaVantageProvider()
        # Exhaust the rate limit
        import time
        import app.modules.market_data.providers.alphavantage as av_mod
        now = time.monotonic()
        av_mod._call_times[:] = [now] * 100  # fill with recent timestamps
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")
        assert result.freshness_status == "error"
        assert "rate" in (result.warning or "").lower() or "límite" in (result.warning or "").lower()
        # Clean up
        av_mod._call_times.clear()

    def test_finnhub_rate_limit_returns_error(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "testkey")
        p = FinnhubProvider()
        import time
        import app.modules.market_data.providers.finnhub as fh_mod
        now = time.monotonic()
        fh_mod._call_times[:] = [now] * 100
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")
        assert result.freshness_status == "error"
        fh_mod._call_times.clear()


# ─── 10. RequestBudget tests ────────────────────────────────────────────────────

from app.modules.market_data.budget import RequestBudget


class TestRequestBudget:
    def test_can_request_when_under_limit(self):
        budget = RequestBudget(limits={"alphavantage": 400})
        with patch.object(budget, "_count_today", return_value=100):
            assert budget.can_request("alphavantage") is True

    def test_cannot_request_when_at_limit(self):
        budget = RequestBudget(limits={"alphavantage": 400})
        with patch.object(budget, "_count_today", return_value=400):
            assert budget.can_request("alphavantage") is False

    def test_can_request_for_unlimited_provider(self):
        budget = RequestBudget(limits={"alphavantage": 400})
        # stooq has no limit — always allowed
        assert budget.can_request("stooq") is True

    def test_get_remaining(self):
        budget = RequestBudget(limits={"twelvedata": 700})
        with patch.object(budget, "_count_today", return_value=250):
            assert budget.get_remaining("twelvedata") == 450

    def test_get_remaining_unlimited_provider(self):
        budget = RequestBudget(limits={})
        assert budget.get_remaining("yahoo") == 9999


# ── TwelveDataProvider tests ─────────────────────────────────────────────────

from unittest.mock import patch, MagicMock


class TestTwelveDataProvider:
    def _make_provider(self) -> "TwelveDataProvider":
        from app.modules.market_data.providers.twelvedata import TwelveDataProvider
        p = TwelveDataProvider.__new__(TwelveDataProvider)
        p.api_key = "test_key"
        p.enabled = True
        return p

    def test_supports_all_asset_types(self):
        from app.modules.market_data.providers.twelvedata import TwelveDataProvider
        p = TwelveDataProvider.__new__(TwelveDataProvider)
        p.api_key = "key"
        p.enabled = True
        for at in ["index", "stock", "forex", "crypto", "commodity", "bond", "volatility"]:
            assert p.supports(at, "ANY") is True

    def test_does_not_support_fundamentals(self):
        from app.modules.market_data.providers.twelvedata import TwelveDataProvider
        p = TwelveDataProvider.__new__(TwelveDataProvider)
        p.api_key = "key"
        p.enabled = True
        assert p.supports("fundamentals", "AAPL") is False

    @patch("app.modules.market_data.providers.twelvedata.requests.get")
    def test_get_quote_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "price": "150.00",
            "close": "148.50",
            "datetime": "2026-06-24 15:30:00",
            "exchange": "NYSE",
            "is_market_open": True,
        }
        mock_get.return_value = mock_resp

        p = self._make_provider()
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")

        assert result.price == 150.0
        assert result.change_absolute == round(150.0 - 148.5, 6)
        assert result.freshness_status != "error"
        assert result.source == "twelvedata"

    @patch("app.modules.market_data.providers.twelvedata.requests.get")
    def test_get_quote_returns_error_on_no_price(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"price": None}
        mock_get.return_value = mock_resp

        p = self._make_provider()
        result = p.get_quote("AAPL", "AAPL", "Apple", "stock", "stocks_us", "USD")

        assert result.price is None
        assert result.freshness_status == "error"

    @patch("app.modules.market_data.providers.twelvedata.requests.get")
    def test_get_quote_timeout_returns_error(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout()

        p = self._make_provider()
        result = p.get_quote("SPX", "SPX", "S&P 500", "index", "indices_us", "USD")

        assert result.price is None
        assert "timeout" in (result.warning or "").lower()
