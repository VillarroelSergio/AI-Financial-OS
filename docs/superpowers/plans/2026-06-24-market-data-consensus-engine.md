# Market Data Consensus Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace sequential fallback routing with parallel fetch + ConsensusEngine that picks the most accurate price across multiple free-tier providers, with Yahoo as last resort only.

**Architecture:** Each asset is fetched in parallel from all configured providers. `ConsensusEngine` resolves discrepancies via median/weighted-confidence logic (D+B+C strategy). `RequestBudget` protects rate-limited providers. Yahoo is consulted only when all others fail.

**Tech Stack:** Python 3.11+, yfinance, requests, DuckDB, `concurrent.futures.ThreadPoolExecutor`, uv (package manager), pytest

## Global Constraints

- No paid providers. No premium plans. All API keys must be free-tier only.
- API keys must never be committed — live in `backend/.env` only.
- `MarketQuoteInternal` dataclass must not gain new required fields.
- `/api/markets/quotes` response schema (`QuoteOut`) must remain unchanged.
- All 35 existing tests must pass after every task.
- Run tests with: `uv run pytest backend/app/tests/ -v`
- Working directory for all commands: `d:/FinancialAgent/AI-Financial-OS/backend`
- Branch: `feat/multi-provider-market-data`

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Modify | `app/modules/market_data/config/market_data_config.yaml` | Add `outlier_thresholds`, `provider_weights`, `yahoo.role`, TwelveData symbols and routing |
| Create | `app/modules/market_data/budget.py` | `RequestBudget` — daily per-provider request counter |
| Create | `app/modules/market_data/providers/twelvedata.py` | `TwelveDataProvider` |
| Modify | `app/modules/market_data/providers/__init__.py` | Export `TwelveDataProvider` |
| Create | `app/modules/market_data/consensus.py` | `ConsensusEngine` + `ConsensusResult` |
| Modify | `app/modules/market_data/router.py` | Parallel fetch + consensus integration + Yahoo guard |
| Modify | `app/tests/test_market_data_service.py` | Add consensus + budget + twelvedata tests |

---

## Task 1: YAML config — thresholds, weights, TwelveData routing

**Files:**
- Modify: `app/modules/market_data/config/market_data_config.yaml`

**Interfaces:**
- Produces: `outlier_thresholds` dict, `provider_weights` dict, `yahoo.role`, updated `routing` sections, `twelvedata` provider entry, TwelveData symbol mappings

- [ ] **Step 1: Add `outlier_thresholds`, `provider_weights`, and `yahoo.role` to the YAML**

Open `app/modules/market_data/config/market_data_config.yaml` and add the following sections immediately after the `providers:` block (before `routing:`):

```yaml
##############################################################################
# Outlier detection thresholds per asset_type (fraction, not percent)
# A provider price is discarded if it deviates > threshold from median.
##############################################################################
outlier_thresholds:
  index:      0.01    # 1%
  stock:      0.02    # 2%
  forex:      0.005   # 0.5%
  crypto:     0.05    # 5%
  commodity:  0.03    # 3%
  bond:       0.01    # 1%
  volatility: 0.05    # 5%

##############################################################################
# Provider base weights per asset_type (used by ConsensusEngine)
# Higher = more trusted for that asset type.
##############################################################################
provider_weights:
  stooq:
    index: 0.9
    stock: 0.5
    bond: 0.8
    volatility: 0.8
    forex: 0.4
    crypto: 0.0
    commodity: 0.5
  finnhub:
    index: 0.7
    stock: 0.9
    forex: 0.6
    crypto: 0.85
    commodity: 0.3
    bond: 0.3
    volatility: 0.3
  twelvedata:
    index: 0.8
    stock: 0.75
    forex: 0.9
    crypto: 0.7
    commodity: 0.8
    bond: 0.5
    volatility: 0.5
  alphavantage:
    index: 0.6
    stock: 0.65
    forex: 0.7
    crypto: 0.6
    commodity: 0.4
    bond: 0.3
    volatility: 0.3
  fmp:
    index: 0.5
    stock: 0.7
    forex: 0.3
    crypto: 0.3
    commodity: 0.3
    bond: 0.3
    volatility: 0.2
  yahoo:
    index: 0.3
    stock: 0.3
    forex: 0.3
    crypto: 0.3
    commodity: 0.3
    bond: 0.3
    volatility: 0.3

##############################################################################
# Request budget limits (conservative daily caps for free-tier APIs)
##############################################################################
request_budget:
  alphavantage:
    daily_limit: 400     # free tier is 500; keep 100 margin
  twelvedata:
    daily_limit: 700     # free tier is 800; keep 100 margin
  fmp:
    daily_limit: 200     # free tier is 250; keep 50 margin
```

- [ ] **Step 2: Update `providers:` block — add `twelvedata`, update `yahoo` role**

In the `providers:` section, add `twelvedata` and update the `yahoo` entry:

```yaml
  twelvedata:
    enabled: true
    priority: 2
    requires_api_key: true
    api_key_env: TWELVEDATA_API_KEY
    free_tier_only: true
    rate_limit_per_minute: 8
    rate_limit_per_day: 800
    description: "Índices, forex, acciones, crypto, commodities. Free tier 800 req/día."

  yahoo:
    enabled: true
    priority: 99
    requires_api_key: false
    role: last_resort
    diagnostic_mode: false
    description: "Último recurso. Solo si todos los demás proveedores fallan."
```

- [ ] **Step 3: Update `routing:` section to reflect new primary providers**

Replace the entire `routing:` section with:

```yaml
routing:
  indices:
    primary: stooq
    validators: [twelvedata, finnhub]
    budget_aware: [alphavantage]
    last_resort: yahoo

  stocks_us:
    primary: finnhub
    validators: [twelvedata, fmp]
    budget_aware: [alphavantage]
    last_resort: yahoo

  stocks_europe:
    primary: stooq
    validators: [twelvedata, fmp]
    budget_aware: []
    last_resort: yahoo

  forex:
    primary: twelvedata
    validators: [finnhub, alphavantage]
    budget_aware: [alphavantage]
    last_resort: yahoo

  crypto:
    primary: finnhub
    validators: [twelvedata, alphavantage]
    budget_aware: [alphavantage]
    last_resort: yahoo

  commodity:
    primary: twelvedata
    validators: []
    budget_aware: []
    last_resort: yahoo

  bond:
    primary: stooq
    validators: []
    budget_aware: []
    last_resort: yahoo

  volatility:
    primary: stooq
    validators: []
    budget_aware: []
    last_resort: yahoo

  historical_daily:
    primary: alphavantage
    validators: [fmp, yahoo]
    budget_aware: [alphavantage]
    last_resort: yahoo

  fundamentals:
    primary: fmp
    validators: [finnhub, alphavantage]
    budget_aware: [alphavantage]
    last_resort: yahoo
```

- [ ] **Step 4: Add TwelveData symbol mappings**

For each asset in `symbol_mappings:`, add a `twelvedata:` entry under `providers:`. TwelveData uses the same symbols as Yahoo for most assets but with slight differences for forex. Add these mappings to the relevant assets:

```yaml
# Indices (add to each index asset under providers:)
# ^IBEX → twelvedata: "IBEX35"   (or omit if not available on free tier)
# ^GSPC → twelvedata: "SPX"
# ^NDX  → twelvedata: "NDX"
# ^DJI  → twelvedata: "DJI"
# ^RUT  → twelvedata: "RUT"
# ^N225 → twelvedata: "N225"
# ^HSI  → twelvedata: "HSI"
# ^GDAXI → twelvedata: "DAX"
# ^FCHI  → twelvedata: "CAC40"
# ^FTSE  → twelvedata: "FTSE100"

# Forex (TwelveData uses EUR/USD format)
# EURUSD=X → twelvedata: "EUR/USD"
# EURGBP=X → twelvedata: "EUR/GBP"
# EURJPY=X → twelvedata: "EUR/JPY"
# GBPUSD=X → twelvedata: "GBP/USD"
# JPY=X    → twelvedata: "USD/JPY"
# CHF=X    → twelvedata: "USD/CHF"

# Crypto (TwelveData uses BTC/USD format)
# BTC-USD → twelvedata: "BTC/USD"
# ETH-USD → twelvedata: "ETH/USD"
# BNB-USD → twelvedata: "BNB/USD"
# SOL-USD → twelvedata: "SOL/USD"

# Commodities
# GC=F → twelvedata: "XAU/USD"
# SI=F → twelvedata: "XAG/USD"
# CL=F → twelvedata: "WTI/USD"
# BZ=F → twelvedata: "BRENT/USD"
# NG=F → twelvedata: "NATURAL_GAS/USD"
```

Add the actual `twelvedata: "SYMBOL"` lines into each asset's `providers:` block in the YAML.

- [ ] **Step 5: Verify YAML parses correctly**

```bash
cd d:/FinancialAgent/AI-Financial-OS/backend
uv run python -c "
import yaml
from pathlib import Path
cfg = yaml.safe_load(Path('app/modules/market_data/config/market_data_config.yaml').read_text())
print('outlier_thresholds:', cfg.get('outlier_thresholds'))
print('provider_weights keys:', list(cfg.get('provider_weights', {}).keys()))
print('routing index primary:', cfg.get('routing', {}).get('indices', {}).get('primary'))
print('yahoo role:', cfg.get('providers', {}).get('yahoo', {}).get('role'))
print('OK')
"
```

Expected output:
```
outlier_thresholds: {'index': 0.01, 'stock': 0.02, 'forex': 0.005, ...}
provider_weights keys: ['stooq', 'finnhub', 'twelvedata', 'alphavantage', 'fmp', 'yahoo']
routing index primary: stooq
yahoo role: last_resort
OK
```

- [ ] **Step 6: Run existing tests — must all pass**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: 35 passed (routing YAML structure changed but router not yet updated — tests mock at provider level so they still pass).

- [ ] **Step 7: Commit**

```bash
git add app/modules/market_data/config/market_data_config.yaml
git commit -m "config(markets): add consensus thresholds, provider weights, TwelveData routing"
```

---

## Task 2: RequestBudget (`budget.py`)

**Files:**
- Create: `app/modules/market_data/budget.py`
- Modify: `app/tests/test_market_data_service.py`

**Interfaces:**
- Consumes: `market_provider_logs` table in DuckDB (already exists in `cache.py`)
- Produces:
  - `RequestBudget` class with `can_request(provider: str) -> bool`, `record_request(provider: str) -> None`, `get_remaining(provider: str) -> int`
  - Module-level singleton: `get_budget() -> RequestBudget`

- [ ] **Step 1: Write failing tests**

Add to `app/tests/test_market_data_service.py`:

```python
# ── RequestBudget tests ──────────────────────────────────────────────────────

from unittest.mock import patch, MagicMock
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
```

- [ ] **Step 2: Run to verify tests fail**

```bash
uv run pytest app/tests/test_market_data_service.py::TestRequestBudget -v
```

Expected: 5 errors — `ModuleNotFoundError: No module named 'app.modules.market_data.budget'`

- [ ] **Step 3: Create `budget.py`**

Create `app/modules/market_data/budget.py`:

```python
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
```

- [ ] **Step 4: Run budget tests — must pass**

```bash
uv run pytest app/tests/test_market_data_service.py::TestRequestBudget -v
```

Expected: 5 passed

- [ ] **Step 5: Run all tests — must still pass**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: all previous tests + 5 new = passing

- [ ] **Step 6: Commit**

```bash
git add app/modules/market_data/budget.py app/tests/test_market_data_service.py
git commit -m "feat(markets): add RequestBudget — daily per-provider rate cap"
```

---

## Task 3: TwelveDataProvider

**Files:**
- Create: `app/modules/market_data/providers/twelvedata.py`
- Modify: `app/modules/market_data/providers/__init__.py`

**Interfaces:**
- Consumes: `MarketDataProvider`, `MarketQuoteInternal`, `_error_quote` from `base.py`; `RequestBudget` from `budget.py`
- Produces: `TwelveDataProvider` class with `supports()`, `get_quote()`

- [ ] **Step 1: Write failing tests**

Add to `app/tests/test_market_data_service.py`:

```python
# ── TwelveDataProvider tests ─────────────────────────────────────────────────

from unittest.mock import patch, MagicMock
import responses as responses_lib


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
```

- [ ] **Step 2: Run to verify tests fail**

```bash
uv run pytest app/tests/test_market_data_service.py::TestTwelveDataProvider -v
```

Expected: 5 errors — `ModuleNotFoundError`

- [ ] **Step 3: Create `twelvedata.py`**

Create `app/modules/market_data/providers/twelvedata.py`:

```python
"""TwelveData provider — free tier, requires API key (TWELVEDATA_API_KEY).

Free tier: 800 req/day, 8 req/min.
Supports: indices, stocks (US + EU), forex, crypto, commodities.
Does NOT support: fundamentals.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import requests

from .base import MarketDataProvider, MarketQuoteInternal

logger = logging.getLogger(__name__)

_TWELVEDATA_BASE = "https://api.twelvedata.com"
_REQUEST_TIMEOUT = 10

_SUPPORTED_ASSET_TYPES: frozenset[str] = frozenset([
    "index", "stock", "etf", "forex", "crypto", "commodity", "bond", "volatility"
])


class TwelveDataProvider(MarketDataProvider):
    name = "twelvedata"
    requires_api_key = True

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.environ.get("TWELVEDATA_API_KEY") or ""
        self.enabled: bool = bool(self.api_key)

    def supports(self, asset_type: str, symbol: str) -> bool:
        return self.enabled and asset_type in _SUPPORTED_ASSET_TYPES

    def get_quote(
        self,
        internal_symbol: str,
        provider_symbol: str,
        name: str,
        asset_type: str,
        category: str,
        currency: str,
        is_fallback: bool = False,
    ) -> MarketQuoteInternal:
        if not self.enabled:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "TwelveData no configurado (TWELVEDATA_API_KEY no definida)", is_fallback,
            )

        try:
            resp = requests.get(
                f"{_TWELVEDATA_BASE}/price",
                params={"symbol": provider_symbol, "apikey": self.api_key},
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 429:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "rate_limited", is_fallback,
                )

            resp.raise_for_status()
            data = resp.json()

            # TwelveData /price returns {"price": "150.00"} or {"code": 400, "message": "..."}
            if "code" in data and data["code"] != 200:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    f"provider_error: {data.get('message', 'unknown')}", is_fallback,
                )

            raw_price = data.get("price")
            if raw_price is None:
                return self._error_quote(
                    internal_symbol, provider_symbol, name, asset_type, category, currency,
                    "provider_error: price field missing", is_fallback,
                )

            price = float(raw_price)

            # Fetch previous close for change calculation via /quote endpoint
            prev_close: Optional[float] = None
            market_time: Optional[datetime] = None
            market_open: Optional[bool] = None
            try:
                quote_resp = requests.get(
                    f"{_TWELVEDATA_BASE}/quote",
                    params={"symbol": provider_symbol, "apikey": self.api_key},
                    timeout=_REQUEST_TIMEOUT,
                )
                if quote_resp.status_code == 200:
                    qd = quote_resp.json()
                    close_raw = qd.get("close") or qd.get("previous_close")
                    if close_raw:
                        prev_close = float(close_raw)
                    dt_raw = qd.get("datetime")
                    if dt_raw:
                        try:
                            market_time = datetime.fromisoformat(dt_raw).replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass
                    market_open = qd.get("is_market_open")
            except Exception:
                pass  # prev_close remains None — change fields will be None

            change_absolute: Optional[float] = None
            change_percent: Optional[float] = None
            if prev_close and prev_close != 0:
                change_absolute = round(price - prev_close, 6)
                change_percent = round((price - prev_close) / prev_close * 100, 4)

            freshness = "unknown"
            if market_time:
                age_min = (datetime.now(timezone.utc) - market_time).total_seconds() / 60
                if age_min < 5:
                    freshness = "live"
                elif age_min < 30:
                    freshness = "fresh"
                elif age_min < 120:
                    freshness = "delayed"
                else:
                    freshness = "eod"
            elif price is not None:
                freshness = "delayed"

            market_status = (
                "open" if market_open is True
                else "closed" if market_open is False
                else "unknown"
            )

            return MarketQuoteInternal(
                internal_symbol=internal_symbol,
                provider_symbol=provider_symbol,
                name=name,
                asset_type=asset_type,
                category=category,
                price=price,
                currency=currency,
                change_absolute=change_absolute,
                change_percent=change_percent,
                source=self.name,
                source_type="delayed",
                fetched_at=datetime.now(timezone.utc),
                market_time=market_time,
                market_status=market_status,
                freshness_status=freshness,
                delay_minutes=15,
                is_stale=False,
                is_fallback=is_fallback,
                confidence_score=0.80,
                warning=None,
                sparkline=[],
            )

        except requests.exceptions.Timeout:
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                "provider_timeout", is_fallback,
            )
        except Exception as exc:
            logger.warning("TwelveDataProvider error for %s: %s", provider_symbol, exc)
            return self._error_quote(
                internal_symbol, provider_symbol, name, asset_type, category, currency,
                f"provider_error: {exc}", is_fallback,
            )
```

- [ ] **Step 4: Update `providers/__init__.py`**

```python
from .alphavantage import AlphaVantageProvider
from .base import (
    AssetType,
    CompanyProfile,
    FreshnessStatus,
    Fundamentals,
    MarketCandle,
    MarketDataProvider,
    MarketQuoteInternal,
)
from .finnhub import FinnhubProvider
from .fmp import FMPProvider
from .stooq import StooqProvider
from .twelvedata import TwelveDataProvider
from .yahoo import YahooFinanceProvider

__all__ = [
    "MarketDataProvider",
    "MarketQuoteInternal",
    "MarketCandle",
    "CompanyProfile",
    "Fundamentals",
    "FreshnessStatus",
    "AssetType",
    "StooqProvider",
    "YahooFinanceProvider",
    "AlphaVantageProvider",
    "FinnhubProvider",
    "FMPProvider",
    "TwelveDataProvider",
]
```

- [ ] **Step 5: Run TwelveData tests — must pass**

```bash
uv run pytest app/tests/test_market_data_service.py::TestTwelveDataProvider -v
```

Expected: 5 passed

- [ ] **Step 6: Run all tests**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: all passing

- [ ] **Step 7: Add `TWELVEDATA_API_KEY` to `backend/.env`**

Add the following line to `backend/.env` (the file is in `.gitignore` — never commit it):

```
TWELVEDATA_API_KEY=<your_free_tier_key_from_twelvedata.com>
```

Register at https://twelvedata.com — free account gives 800 req/day.

- [ ] **Step 8: Commit**

```bash
git add app/modules/market_data/providers/twelvedata.py app/modules/market_data/providers/__init__.py app/tests/test_market_data_service.py
git commit -m "feat(markets): add TwelveDataProvider — forex/indices/crypto primary source"
```

---

## Task 4: ConsensusEngine (`consensus.py`)

**Files:**
- Create: `app/modules/market_data/consensus.py`
- Modify: `app/tests/test_market_data_service.py`

**Interfaces:**
- Consumes: `MarketQuoteInternal` from `providers/base.py`; `outlier_thresholds` and `provider_weights` from YAML config
- Produces:
  - `ConsensusResult` dataclass
  - `ConsensusEngine` class with `resolve(quotes: list[MarketQuoteInternal], asset_type: str, primary_provider: str) -> ConsensusResult`

- [ ] **Step 1: Write failing tests**

Add to `app/tests/test_market_data_service.py`:

```python
# ── ConsensusEngine tests ────────────────────────────────────────────────────

from datetime import datetime, timezone
from app.modules.market_data.consensus import ConsensusEngine, ConsensusResult
from app.modules.market_data.providers.base import MarketQuoteInternal


def _make_quote(source: str, price: float, freshness: str = "delayed",
                market_time: datetime = None, is_fallback: bool = False) -> MarketQuoteInternal:
    return MarketQuoteInternal(
        internal_symbol="^GSPC",
        provider_symbol="SPX",
        name="S&P 500",
        asset_type="index",
        category="indices_us",
        price=price,
        currency="USD",
        change_absolute=None,
        change_percent=None,
        source=source,
        source_type="delayed",
        fetched_at=datetime.now(timezone.utc),
        market_time=market_time,
        market_status="unknown",
        freshness_status=freshness,
        delay_minutes=15,
        is_stale=False,
        is_fallback=is_fallback,
        confidence_score=0.8,
        warning=None,
        sparkline=[],
    )


def _make_error_quote(source: str) -> MarketQuoteInternal:
    return MarketQuoteInternal(
        internal_symbol="^GSPC", provider_symbol="SPX", name="S&P 500",
        asset_type="index", category="indices_us", price=None, currency="USD",
        change_absolute=None, change_percent=None, source=source,
        source_type="error", fetched_at=datetime.now(timezone.utc),
        market_time=None, market_status="unknown", freshness_status="error",
        delay_minutes=0, is_stale=False, is_fallback=False,
        confidence_score=0.0, warning="error", sparkline=[],
    )


class TestConsensusEngine:
    def setup_method(self):
        self.engine = ConsensusEngine()

    def test_primary_wins_when_within_threshold(self):
        # primary (stooq) at 5000, validators at 5001 and 5002 — all within 1%
        quotes = [
            _make_quote("stooq", 5000.0),
            _make_quote("twelvedata", 5001.0),
            _make_quote("finnhub", 5002.0),
        ]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert result.consensus_method == "primary"
        assert result.selected_source == "stooq"
        assert result.price == 5000.0
        assert result.confidence_score > 0.5
        assert "provider_mismatch" not in result.warnings

    def test_median_used_when_primary_deviates(self):
        # primary (stooq) deviates >1% from median
        quotes = [
            _make_quote("stooq", 5100.0),     # outlier
            _make_quote("twelvedata", 5000.0),
            _make_quote("finnhub", 5001.0),
        ]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert result.consensus_method == "median"
        assert result.selected_source == "consensus_median"
        assert abs(result.price - 5000.5) < 1.0  # median of 5000 and 5001
        assert "provider_mismatch" in result.warnings

    def test_outlier_discarded(self):
        # One provider grossly wrong — must be discarded
        quotes = [
            _make_quote("stooq", 5000.0),
            _make_quote("twelvedata", 5001.0),
            _make_quote("finnhub", 9999.0),  # outlier
        ]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert "finnhub" in result.outliers
        assert result.price < 6000  # outlier not affecting price

    def test_single_provider_lowers_confidence(self):
        quotes = [_make_quote("stooq", 5000.0)]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert result.consensus_method == "single"
        assert result.confidence_score <= 0.6
        assert "unverified_single_provider" in result.warnings

    def test_no_valid_providers_returns_error(self):
        quotes = [_make_error_quote("stooq"), _make_error_quote("twelvedata")]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert result.consensus_method == "error"
        assert result.price is None
        assert result.confidence_score == 0.0

    def test_two_providers_no_outlier_detection(self):
        # With only 2 providers, no outlier removal — compare directly
        quotes = [
            _make_quote("stooq", 5000.0),
            _make_quote("twelvedata", 5002.0),  # 0.04% diff — within 1%
        ]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert result.consensus_method == "primary"
        assert result.price == 5000.0
        assert len(result.outliers) == 0

    def test_confidence_score_higher_with_live_data(self):
        now = datetime.now(timezone.utc)
        quotes_live = [
            _make_quote("stooq", 5000.0, freshness="live", market_time=now),
            _make_quote("twelvedata", 5001.0, freshness="live", market_time=now),
        ]
        quotes_eod = [
            _make_quote("stooq", 5000.0, freshness="eod"),
            _make_quote("twelvedata", 5001.0, freshness="eod"),
        ]
        result_live = self.engine.resolve(quotes_live, "index", "stooq")
        result_eod = self.engine.resolve(quotes_eod, "index", "stooq")
        assert result_live.confidence_score > result_eod.confidence_score

    def test_result_contains_all_log_fields(self):
        quotes = [
            _make_quote("stooq", 5000.0),
            _make_quote("twelvedata", 5001.0),
        ]
        result = self.engine.resolve(quotes, "index", "stooq")
        assert isinstance(result.selected_source, str)
        assert isinstance(result.consensus_method, str)
        assert isinstance(result.provider_count, int)
        assert isinstance(result.valid_provider_count, int)
        assert isinstance(result.outliers, list)
        assert isinstance(result.discarded_providers, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.reason, str)
```

- [ ] **Step 2: Run to verify tests fail**

```bash
uv run pytest app/tests/test_market_data_service.py::TestConsensusEngine -v
```

Expected: errors — `ModuleNotFoundError: No module named 'app.modules.market_data.consensus'`

- [ ] **Step 3: Create `consensus.py`**

Create `app/modules/market_data/consensus.py`:

```python
"""ConsensusEngine — resolves price from multiple provider quotes.

Strategy: D (primary + validation) + B (median for discrepancies) + C (weighted confidence).

Decision flow:
  0 valid  → error
  1 valid  → unverified_single_provider, confidence *= 0.6
  ≥2 valid → median (if ≥3: remove outliers first), primary vs median check,
             weighted confidence score
"""
from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from app.modules.market_data.providers.base import MarketQuoteInternal

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config" / "market_data_config.yaml"

# Threshold for "primary agrees with median" check (fixed, not per-asset)
_PRIMARY_AGREE_THRESHOLD = 0.01  # 1%

_FRESHNESS_FACTOR: dict[str, float] = {
    "live": 1.0,
    "fresh": 0.9,
    "delayed": 0.8,
    "eod": 0.6,
    "closed": 0.6,
    "unknown": 0.5,
    "stale": 0.3,
    "error": 0.0,
}


@dataclass
class ConsensusResult:
    price: Optional[float]
    confidence_score: float
    selected_source: str
    consensus_method: str          # "primary" | "median" | "single" | "error"
    consensus_price: Optional[float]
    provider_count: int
    valid_provider_count: int
    outliers: list[str] = field(default_factory=list)
    discarded_providers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reason: str = ""
    freshness_status: str = "unknown"
    source_type: str = "unknown"


class ConsensusEngine:
    """Resolves the best price from a list of provider quotes."""

    def __init__(self) -> None:
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
        self._outlier_thresholds: dict[str, float] = cfg.get("outlier_thresholds", {})
        self._provider_weights: dict[str, dict[str, float]] = cfg.get("provider_weights", {})

    def resolve(
        self,
        quotes: list[MarketQuoteInternal],
        asset_type: str,
        primary_provider: str,
    ) -> ConsensusResult:
        provider_count = len(quotes)
        valid = [q for q in quotes if q.price is not None and q.freshness_status != "error"]
        valid_provider_count = len(valid)

        # Case 0: no valid data
        if valid_provider_count == 0:
            return ConsensusResult(
                price=None,
                confidence_score=0.0,
                selected_source="none",
                consensus_method="error",
                consensus_price=None,
                provider_count=provider_count,
                valid_provider_count=0,
                warnings=["provider_error"],
                reason="No providers returned valid price data",
            )

        # Case 1: single valid provider
        if valid_provider_count == 1:
            q = valid[0]
            base_conf = self._base_weight(q.source, asset_type)
            return ConsensusResult(
                price=q.price,
                confidence_score=min(base_conf * 0.6, 0.6),
                selected_source=q.source,
                consensus_method="single",
                consensus_price=q.price,
                provider_count=provider_count,
                valid_provider_count=1,
                warnings=["unverified_single_provider"],
                reason=f"Only {q.source} returned valid data; result unverified",
                freshness_status=q.freshness_status,
                source_type=q.source_type,
            )

        # Case 2+: multiple valid providers
        outliers: list[str] = []
        discarded: list[str] = []
        warnings: list[str] = []

        prices = [q.price for q in valid]

        if valid_provider_count >= 3:
            threshold = self._outlier_thresholds.get(asset_type, 0.02)
            median_all = statistics.median(prices)
            clean = []
            for q in valid:
                deviation = abs(q.price - median_all) / median_all if median_all else 0
                if deviation > threshold:
                    outliers.append(q.source)
                    discarded.append(q.source)
                else:
                    clean.append(q)
            if outliers:
                warnings.append("outlier_detected")
            valid = clean if clean else valid  # don't discard all
            prices = [q.price for q in valid]

        consensus_price = statistics.median(prices)

        # Check primary provider
        primary_quote: Optional[MarketQuoteInternal] = next(
            (q for q in valid if q.source == primary_provider), None
        )

        if primary_quote is not None:
            deviation = abs(primary_quote.price - consensus_price) / consensus_price if consensus_price else 0
            if deviation <= _PRIMARY_AGREE_THRESHOLD:
                selected_price = primary_quote.price
                selected_source = primary_provider
                method = "primary"
                reason = (
                    f"Primary ({primary_provider}) agrees with median "
                    f"(diff={deviation*100:.2f}%)"
                )
            else:
                selected_price = consensus_price
                selected_source = "consensus_median"
                method = "median"
                warnings.append("provider_mismatch")
                reason = (
                    f"Primary ({primary_provider}) deviates {deviation*100:.2f}% from median; "
                    f"using median of {[q.source for q in valid]}"
                )
        else:
            selected_price = consensus_price
            selected_source = "consensus_median"
            method = "median"
            reason = f"Primary provider {primary_provider} not in valid set; using median"

        confidence = self._weighted_confidence(valid, asset_type, primary_provider)

        # Pick representative freshness from best available quote
        freshness = max(
            (q.freshness_status for q in valid),
            key=lambda s: _FRESHNESS_FACTOR.get(s, 0),
        )

        return ConsensusResult(
            price=selected_price,
            confidence_score=confidence,
            selected_source=selected_source,
            consensus_method=method,
            consensus_price=consensus_price,
            provider_count=provider_count,
            valid_provider_count=len(valid),
            outliers=outliers,
            discarded_providers=discarded,
            warnings=warnings,
            reason=reason,
            freshness_status=freshness,
            source_type="consensus" if method == "median" else (primary_quote.source_type if primary_quote else "unknown"),
        )

    def _base_weight(self, provider: str, asset_type: str) -> float:
        return self._provider_weights.get(provider, {}).get(asset_type, 0.5)

    def _weighted_confidence(
        self,
        quotes: list[MarketQuoteInternal],
        asset_type: str,
        primary_provider: str,
    ) -> float:
        total_base = 0.0
        weighted_sum = 0.0
        for q in quotes:
            base = self._base_weight(q.source, asset_type)
            freshness = _FRESHNESS_FACTOR.get(q.freshness_status, 0.5)
            market_time_bonus = 0.1 if q.market_time else 0.0
            primary_bonus = 1.2 if q.source == primary_provider else 1.0
            fallback_penalty = 0.5 if q.is_fallback else 1.0
            weight = base * freshness * primary_bonus * fallback_penalty + market_time_bonus
            weighted_sum += weight
            total_base += base
        if total_base == 0:
            return 0.0
        return min(weighted_sum / total_base, 1.0)
```

- [ ] **Step 4: Run consensus tests — must pass**

```bash
uv run pytest app/tests/test_market_data_service.py::TestConsensusEngine -v
```

Expected: 8 passed

- [ ] **Step 5: Run all tests**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: all passing

- [ ] **Step 6: Commit**

```bash
git add app/modules/market_data/consensus.py app/tests/test_market_data_service.py
git commit -m "feat(markets): ConsensusEngine — parallel D+B+C price resolution"
```

---

## Task 5: ProviderRouter refactor — parallel fetch + consensus integration

**Files:**
- Modify: `app/modules/market_data/router.py`
- Modify: `app/tests/test_market_data_service.py`

**Interfaces:**
- Consumes:
  - `ConsensusEngine.resolve(quotes, asset_type, primary_provider) -> ConsensusResult`
  - `RequestBudget.can_request(provider) -> bool` from `budget.get_budget()`
  - Updated routing YAML: `routing[route_key]` is now `{"primary": str, "validators": list, "budget_aware": list, "last_resort": str}`
- Produces: `get_quotes(category=None) -> list[dict]` — same public interface as before

- [ ] **Step 1: Write failing integration tests**

Add to `app/tests/test_market_data_service.py`:

```python
# ── Router parallel fetch + consensus integration tests ──────────────────────

from unittest.mock import patch, MagicMock


class TestRouterParallelFetch:
    def _mock_provider(self, name: str, price: float) -> MagicMock:
        p = MagicMock()
        p.name = name
        p.enabled = True
        p.supports.return_value = True
        q = _make_quote(name, price)
        p.get_quote.return_value = q
        return p

    def _mock_error_provider(self, name: str) -> MagicMock:
        p = MagicMock()
        p.name = name
        p.enabled = True
        p.supports.return_value = True
        p.get_quote.return_value = _make_error_quote(name)
        return p

    def test_yahoo_not_called_when_others_succeed(self):
        from app.modules.market_data.router import ProviderRouter
        from app.modules.market_data.providers.base import MarketQuoteInternal

        router = ProviderRouter.__new__(ProviderRouter)
        router._config = {
            "routing": {"indices": {"primary": "stooq", "validators": ["twelvedata"], "budget_aware": [], "last_resort": "yahoo"}},
            "outlier_thresholds": {"index": 0.01},
            "provider_weights": {"stooq": {"index": 0.9}, "twelvedata": {"index": 0.8}, "yahoo": {"index": 0.3}},
            "request_budget": {},
        }
        from app.modules.market_data.router import AssetConfig
        from app.modules.market_data.cache import MarketCache
        from app.modules.market_data.consensus import ConsensusEngine
        from app.modules.market_data.budget import RequestBudget

        router._catalog = []
        router._routing = router._config["routing"]
        router._cache = MagicMock(spec=MarketCache)
        router._cache.get_quote.return_value = None
        router._consensus = ConsensusEngine.__new__(ConsensusEngine)
        import yaml
        from pathlib import Path
        cfg = yaml.safe_load(Path("app/modules/market_data/config/market_data_config.yaml").read_text())
        router._consensus._outlier_thresholds = cfg["outlier_thresholds"]
        router._consensus._provider_weights = cfg["provider_weights"]
        router._budget = RequestBudget(limits={})

        yahoo_mock = self._mock_provider("yahoo", 5000.0)
        stooq_mock = self._mock_provider("stooq", 5000.0)
        twelvedata_mock = self._mock_provider("twelvedata", 5001.0)
        router._providers = {
            "stooq": stooq_mock,
            "twelvedata": twelvedata_mock,
            "yahoo": yahoo_mock,
        }

        asset = AssetConfig(
            internal_symbol="^GSPC",
            name="S&P 500",
            category="indices_us",
            asset_type="index",
            currency="USD",
            provider_symbols={"stooq": "^spx", "twelvedata": "SPX", "yahoo": "^GSPC"},
        )

        result = router.get_quote(asset)
        assert result.price is not None
        yahoo_mock.get_quote.assert_not_called()

    def test_yahoo_called_as_last_resort_when_all_fail(self):
        from app.modules.market_data.router import ProviderRouter, AssetConfig
        from app.modules.market_data.cache import MarketCache
        from app.modules.market_data.consensus import ConsensusEngine
        from app.modules.market_data.budget import RequestBudget

        router = ProviderRouter.__new__(ProviderRouter)
        router._config = {
            "routing": {"indices": {"primary": "stooq", "validators": ["twelvedata"], "budget_aware": [], "last_resort": "yahoo"}},
            "outlier_thresholds": {"index": 0.01},
            "provider_weights": {"stooq": {"index": 0.9}, "twelvedata": {"index": 0.8}, "yahoo": {"index": 0.3}},
            "request_budget": {},
        }
        router._catalog = []
        router._routing = router._config["routing"]
        router._cache = MagicMock(spec=MarketCache)
        router._cache.get_quote.return_value = None
        router._consensus = ConsensusEngine.__new__(ConsensusEngine)
        import yaml
        from pathlib import Path
        cfg = yaml.safe_load(Path("app/modules/market_data/config/market_data_config.yaml").read_text())
        router._consensus._outlier_thresholds = cfg["outlier_thresholds"]
        router._consensus._provider_weights = cfg["provider_weights"]
        router._budget = RequestBudget(limits={})

        yahoo_mock = self._mock_provider("yahoo", 5000.0)
        stooq_mock = self._mock_error_provider("stooq")
        twelvedata_mock = self._mock_error_provider("twelvedata")
        router._providers = {
            "stooq": stooq_mock,
            "twelvedata": twelvedata_mock,
            "yahoo": yahoo_mock,
        }

        asset = AssetConfig(
            internal_symbol="^GSPC",
            name="S&P 500",
            category="indices_us",
            asset_type="index",
            currency="USD",
            provider_symbols={"stooq": "^spx", "twelvedata": "SPX", "yahoo": "^GSPC"},
        )

        result = router.get_quote(asset)
        yahoo_mock.get_quote.assert_called_once()
        assert "yahoo_last_resort" in (result.warning or "")
```

- [ ] **Step 2: Run to verify tests fail**

```bash
uv run pytest app/tests/test_market_data_service.py::TestRouterParallelFetch -v
```

Expected: failures — router still uses old sequential logic

- [ ] **Step 3: Refactor `router.py`**

Replace the `ProviderRouter` class and `_load_config` / `_build_asset_catalog` functions in `app/modules/market_data/router.py` with the following. Keep all module-level singletons (`get_router`, `get_quotes`, `_quote_row_to_api_dict`) unchanged.

```python
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

        warning_str = "; ".join(result.warnings) if result.warnings else None

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
```

Keep the bottom of `router.py` (from `# Module-level singleton` onwards) unchanged — `get_router`, `_refresh_all`, `get_quotes`, `_quote_row_to_api_dict` remain identical.

- [ ] **Step 4: Run integration tests — must pass**

```bash
uv run pytest app/tests/test_market_data_service.py::TestRouterParallelFetch -v
```

Expected: 2 passed

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: all passing

- [ ] **Step 6: Smoke test against live endpoint**

Start the backend and call the quotes endpoint:

```bash
# Terminal 1
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2
curl -s http://localhost:8000/api/markets/quotes | python -m json.tool | head -60
```

Expected: JSON array with quotes. Each quote has `source`, `confidence_score`, `warning` fields. Yahoo should NOT appear as source unless all others failed.

- [ ] **Step 7: Commit**

```bash
git add app/modules/market_data/router.py app/tests/test_market_data_service.py
git commit -m "feat(markets): parallel fetch + ConsensusEngine + Yahoo last resort in ProviderRouter"
```

---

## Task 6: Wire TWELVEDATA_API_KEY into settings and verify end-to-end

**Files:**
- Modify: `app/core/config.py`
- Verify: `backend/.env`

**Interfaces:**
- Consumes: `TWELVEDATA_API_KEY` env var
- Produces: `settings.TWELVEDATA_API_KEY` available system-wide (TwelveDataProvider reads directly from `os.environ`, but settings consistency is required)

- [ ] **Step 1: Add `TWELVEDATA_API_KEY` to `config.py`**

Open `app/core/config.py` and add alongside the existing API key fields:

```python
TWELVEDATA_API_KEY: str = ""
```

- [ ] **Step 2: Verify `.env` has the key**

Open `backend/.env` and confirm the line exists:

```
TWELVEDATA_API_KEY=<your_key_here>
```

If missing, add it. Get a free key at https://twelvedata.com (no credit card required).

- [ ] **Step 3: Run all tests to confirm nothing broken**

```bash
uv run pytest app/tests/test_market_data_service.py -v
```

Expected: all passing

- [ ] **Step 4: Final live smoke test — check provider sources in response**

```bash
curl -s http://localhost:8000/api/markets/quotes | python -c "
import json, sys
data = json.load(sys.stdin)
sources = set(q['source'] for q in data)
yahoo_count = sum(1 for q in data if q['source'] == 'yahoo')
print(f'Total quotes: {len(data)}')
print(f'Sources used: {sources}')
print(f'Yahoo as source: {yahoo_count}')
print(f'Avg confidence: {sum(q[\"confidence_score\"] for q in data)/len(data):.2f}')
"
```

Expected output (approximate):
```
Total quotes: 36
Sources used: {'stooq', 'twelvedata', 'finnhub', 'consensus_median', ...}
Yahoo as source: 0   ← or very low
Avg confidence: 0.65+
```

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py
git commit -m "config(markets): wire TWELVEDATA_API_KEY into settings"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| TwelveDataProvider | Task 3 |
| RequestBudget | Task 2 |
| ConsensusEngine | Task 4 |
| Parallel fetch in ProviderRouter | Task 5 |
| Yahoo last resort + diagnostic_mode config | Task 1 (YAML) + Task 5 (guard logic) |
| Outlier thresholds per asset_type | Task 1 (YAML) + Task 4 (engine) |
| Provider weights per asset_type | Task 1 (YAML) + Task 4 (engine) |
| Normalized warning codes | Task 4 (ConsensusEngine) + Task 5 (router) |
| Structured decision log | Task 5 (logger.debug block) |
| Primary provider per asset_type routing | Task 1 (YAML) + Task 5 (router reads `primary` key) |
| Budget limits for AV, TwelveData, FMP | Task 1 (YAML) + Task 2 (budget.py) |
| `unverified_single_provider` warning | Task 4 (ConsensusEngine single-provider case) |
| `yahoo_last_resort` warning | Task 5 (Yahoo guard sets `yq.warning`) |
| All 35 existing tests pass | Verified in every task |
| TWELVEDATA_API_KEY in settings | Task 6 |

**Placeholder scan:** None found — all code blocks are complete implementations.

**Type consistency:**
- `ConsensusResult.warnings` is `list[str]` — used consistently in Tasks 4 and 5.
- `AssetConfig` dataclass defined once in `router.py`, referenced in router tests by importing from `app.modules.market_data.router`.
- `ConsensusEngine.resolve(quotes, asset_type, primary_provider)` — signature consistent across Task 4 definition and Task 5 call site.
- `RequestBudget.can_request(provider: str) -> bool` — consistent across Task 2 definition and Task 5 call site.
