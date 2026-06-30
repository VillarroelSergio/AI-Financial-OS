# Portfolio Price Coverage Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Portfolio Price Coverage Audit that resolves tickers for 19 known assets, queries live prices via Market Intelligence adapters (Finnhub → Alpha Vantage → yfinance), and presents a coverage report in the Investments UI.

**Architecture:** A lightweight `EquityQuoteService` wraps existing MI adapters to fetch quotes for any ticker. An `AssetResolutionService` maps asset names to canonical tickers using a known-assets dict. A `PriceCoverageAuditService` orchestrates both, classifies each asset as OK/PARTIAL/AMBIGUOUS/UNAVAILABLE/MANUAL/ERROR, and returns a structured report. Three new endpoints are added under `/api/investments/price-coverage/`. The frontend adds a `PriceCoveragePage` accessible from `InvestmentsPage`.

**Tech Stack:** Python 3.11 + FastAPI + yfinance + requests (backend); React 18 + TypeScript + Tailwind + shadcn/ui (frontend); pytest with mocks (tests).

## Global Constraints

- No hardcoded prices — only ticker/exchange/currency resolution is hardcoded in the known-assets dict
- No invented tickers — if asset is not in known dict and not resolvable, status = UNAVAILABLE
- No scraping, no bank automation, no cloud data exfiltration
- All data stays local
- Do not break existing Market Intelligence module or investments routes
- Backend tests run with: `cd backend && uv run pytest`
- Frontend type check: `cd apps/desktop && npx tsc --noEmit`
- Existing `client` fixture in `backend/app/tests/conftest.py` creates an isolated SQLite DB per test

---

## File Map

**Create:**
- `backend/app/modules/market_intelligence/ingestion/equity_quote_service.py`
- `backend/app/modules/investments/asset_resolution.py`
- `backend/app/modules/investments/price_coverage_audit.py`
- `backend/app/modules/investments/price_coverage_routes.py`
- `backend/app/tests/test_price_coverage.py`
- `apps/desktop/src/lib/types/price-coverage.ts`
- `apps/desktop/src/lib/api/price-coverage.ts`
- `apps/desktop/src/lib/hooks/usePriceCoverage.ts`
- `apps/desktop/src/features/investments/price-coverage/PriceCoverageStatusBadge.tsx`
- `apps/desktop/src/features/investments/price-coverage/PriceCoverageSummaryCards.tsx`
- `apps/desktop/src/features/investments/price-coverage/PriceCoverageTable.tsx`
- `apps/desktop/src/features/investments/price-coverage/PriceCoveragePage.tsx`

**Modify:**
- `backend/app/main.py` — register price_coverage_routes
- `apps/desktop/src/App.tsx` — add route `/investments/price-coverage`
- `apps/desktop/src/features/investments/InvestmentsPage.tsx` — add "Cobertura de precios" button

---

### Task 1: EquityQuoteService

**Files:**
- Create: `backend/app/modules/market_intelligence/ingestion/equity_quote_service.py`
- Test: `backend/app/tests/test_price_coverage.py` (initial setup, tested inline in Task 5)

**Interfaces:**
- Produces: `get_equity_quote(ticker: str, yfinance_symbol: str, expected_currency: str) -> EquityQuoteResult`
- `EquityQuoteResult` dataclass with fields: `ticker`, `price`, `currency`, `provider`, `retrieved_at`, `from_cache`, `success`, `error`

- [ ] **Step 1: Create the file**

```python
# backend/app/modules/market_intelligence/ingestion/equity_quote_service.py
"""Lightweight equity quote fetcher over existing MI adapters."""
from __future__ import annotations

import requests
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from app.modules.market_intelligence.ingestion.config import get_api_key


@dataclass
class EquityQuoteResult:
    ticker: str
    price: float
    currency: str
    provider: str
    retrieved_at: datetime
    from_cache: bool = False
    success: bool = True
    error: Optional[str] = None


def _try_finnhub(ticker: str, expected_currency: str) -> Optional[EquityQuoteResult]:
    api_key = get_api_key("Finnhub") or get_api_key("FINNHUB")
    if not api_key:
        return None
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = float(data.get("c") or 0.0)
        if price <= 0:
            return None
        return EquityQuoteResult(
            ticker=ticker,
            price=price,
            currency=expected_currency,
            provider="finnhub",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def _try_alpha_vantage(ticker: str, expected_currency: str) -> Optional[EquityQuoteResult]:
    api_key = get_api_key("Alpha Vantage") or get_api_key("ALPHA_VANTAGE")
    if not api_key:
        return None
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price_str = data.get("Global Quote", {}).get("05. price", "0")
        price = float(price_str or 0)
        if price <= 0:
            return None
        return EquityQuoteResult(
            ticker=ticker,
            price=price,
            currency=expected_currency,
            provider="alpha_vantage",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def _try_yfinance(yfinance_symbol: str) -> Optional[EquityQuoteResult]:
    try:
        t = yf.Ticker(yfinance_symbol)
        info = t.fast_info
        price = info.last_price
        if price is None or price <= 0:
            return None
        currency = (getattr(info, "currency", None) or "USD").upper()
        return EquityQuoteResult(
            ticker=yfinance_symbol,
            price=float(price),
            currency=currency,
            provider="yfinance",
            retrieved_at=datetime.now(timezone.utc),
        )
    except Exception:
        return None


def get_equity_quote(
    ticker: str,
    yfinance_symbol: str,
    expected_currency: str = "USD",
) -> EquityQuoteResult:
    """Fetch equity quote. Tries Finnhub → Alpha Vantage → yfinance."""
    result = (
        _try_finnhub(ticker, expected_currency)
        or _try_alpha_vantage(ticker, expected_currency)
        or _try_yfinance(yfinance_symbol)
    )
    if result:
        return result
    return EquityQuoteResult(
        ticker=ticker,
        price=0.0,
        currency="",
        provider="none",
        retrieved_at=datetime.now(timezone.utc),
        success=False,
        error="All providers failed or returned zero price",
    )
```

- [ ] **Step 2: Verify import works**

```bash
cd backend && uv run python -c "from app.modules.market_intelligence.ingestion.equity_quote_service import get_equity_quote, EquityQuoteResult; print('OK')"
```

Expected: `OK`

---

### Task 2: AssetResolutionService

**Files:**
- Create: `backend/app/modules/investments/asset_resolution.py`

**Interfaces:**
- Produces: `resolve_asset(asset_name: str) -> AssetResolution`
- `TickerCandidate` dataclass: `ticker`, `yfinance_symbol`, `name`, `exchange`, `currency`, `asset_type`, `confidence`
- `AssetResolution` dataclass: `asset_name`, `candidates`, `selected`, `status` (`resolved` | `ambiguous` | `manual` | `unavailable`)

- [ ] **Step 1: Create the file**

```python
# backend/app/modules/investments/asset_resolution.py
"""Maps asset names to canonical tickers for the 19 known portfolio assets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TickerCandidate:
    ticker: str
    yfinance_symbol: str
    name: str
    exchange: str
    currency: str
    asset_type: str = "equity"
    confidence: float = 1.0


@dataclass
class AssetResolution:
    asset_name: str
    candidates: list[TickerCandidate]
    selected: Optional[TickerCandidate]
    status: str  # resolved | ambiguous | manual | unavailable


# Known asset registry — tickers hardcoded for resolution only, never prices
_KNOWN: dict[str, TickerCandidate] = {
    "banco bilbao vizcaya argentaria": TickerCandidate(
        ticker="BBVA", yfinance_symbol="BBVA.MC",
        name="Banco Bilbao Vizcaya Argentaria SA",
        exchange="BME", currency="EUR",
    ),
    "bbva": TickerCandidate(
        ticker="BBVA", yfinance_symbol="BBVA.MC",
        name="Banco Bilbao Vizcaya Argentaria SA",
        exchange="BME", currency="EUR",
    ),
    "apple": TickerCandidate(
        ticker="AAPL", yfinance_symbol="AAPL",
        name="Apple Inc.", exchange="NASDAQ", currency="USD",
    ),
    "iberdrola": TickerCandidate(
        ticker="IBE.MC", yfinance_symbol="IBE.MC",
        name="Iberdrola SA", exchange="BME", currency="EUR",
    ),
    "asml": TickerCandidate(
        ticker="ASML", yfinance_symbol="ASML.AS",
        name="ASML Holding NV", exchange="AMS", currency="EUR",
    ),
    "caterpillar": TickerCandidate(
        ticker="CAT", yfinance_symbol="CAT",
        name="Caterpillar Inc.", exchange="NYSE", currency="USD",
    ),
    "alphabet": TickerCandidate(
        ticker="GOOGL", yfinance_symbol="GOOGL",
        name="Alphabet Inc. (A)", exchange="NASDAQ", currency="USD",
    ),
    "waste management": TickerCandidate(
        ticker="WM", yfinance_symbol="WM",
        name="Waste Management Inc.", exchange="NYSE", currency="USD",
    ),
    "tsmc": TickerCandidate(
        ticker="TSM", yfinance_symbol="TSM",
        name="Taiwan Semiconductor Mfg Co. (ADR)",
        exchange="NYSE", currency="USD",
    ),
    "johnson & johnson": TickerCandidate(
        ticker="JNJ", yfinance_symbol="JNJ",
        name="Johnson & Johnson", exchange="NYSE", currency="USD",
    ),
    "johnson and johnson": TickerCandidate(
        ticker="JNJ", yfinance_symbol="JNJ",
        name="Johnson & Johnson", exchange="NYSE", currency="USD",
    ),
    "lockheed martin": TickerCandidate(
        ticker="LMT", yfinance_symbol="LMT",
        name="Lockheed Martin Corp.", exchange="NYSE", currency="USD",
    ),
    "nvidia": TickerCandidate(
        ticker="NVDA", yfinance_symbol="NVDA",
        name="NVIDIA Corp.", exchange="NASDAQ", currency="USD",
    ),
    "spacex": TickerCandidate(
        ticker="SPCX", yfinance_symbol="SPCX",
        name="SpaceX", exchange="NASDAQ", currency="USD",
    ),
    "amazon": TickerCandidate(
        ticker="AMZN", yfinance_symbol="AMZN",
        name="Amazon.com Inc.", exchange="NASDAQ", currency="USD",
    ),
    "amazon.com": TickerCandidate(
        ticker="AMZN", yfinance_symbol="AMZN",
        name="Amazon.com Inc.", exchange="NASDAQ", currency="USD",
    ),
    "rocket lab": TickerCandidate(
        ticker="RKLB", yfinance_symbol="RKLB",
        name="Rocket Lab USA Inc.", exchange="NASDAQ", currency="USD",
    ),
    "rtx": TickerCandidate(
        ticker="RTX", yfinance_symbol="RTX",
        name="RTX Corporation", exchange="NYSE", currency="USD",
    ),
    "rtx corporation": TickerCandidate(
        ticker="RTX", yfinance_symbol="RTX",
        name="RTX Corporation", exchange="NYSE", currency="USD",
    ),
    "berkshire hathaway": TickerCandidate(
        ticker="BRK-B", yfinance_symbol="BRK-B",
        name="Berkshire Hathaway Inc. (B)", exchange="NYSE", currency="USD",
    ),
    "visa": TickerCandidate(
        ticker="V", yfinance_symbol="V",
        name="Visa Inc.", exchange="NYSE", currency="USD",
    ),
    "microsoft": TickerCandidate(
        ticker="MSFT", yfinance_symbol="MSFT",
        name="Microsoft Corp.", exchange="NASDAQ", currency="USD",
    ),
    "droneshield": TickerCandidate(
        ticker="DRO.AX", yfinance_symbol="DRO.AX",
        name="DroneShield Ltd.", exchange="ASX", currency="AUD",
    ),
}


def _normalize(name: str) -> str:
    return name.lower().strip()


def resolve_asset(asset_name: str) -> AssetResolution:
    """Resolve an asset name to a ticker candidate."""
    key = _normalize(asset_name)

    # Exact match
    if key in _KNOWN:
        candidate = _KNOWN[key]
        return AssetResolution(
            asset_name=asset_name,
            candidates=[candidate],
            selected=candidate,
            status="resolved",
        )

    # Partial match (key is substring of known key or vice versa)
    matches = [
        c for k, c in _KNOWN.items()
        if key in k or k in k  # only substring in known key direction
    ]
    # Deduplicate by ticker
    seen: set[str] = set()
    unique: list[TickerCandidate] = []
    for m in matches:
        if m.ticker not in seen:
            seen.add(m.ticker)
            unique.append(m)

    # Actually fix the partial match logic:
    unique = []
    seen = set()
    for k, c in _KNOWN.items():
        if key in k and c.ticker not in seen:
            seen.add(c.ticker)
            unique.append(c)

    if len(unique) == 1:
        return AssetResolution(
            asset_name=asset_name,
            candidates=unique,
            selected=unique[0],
            status="resolved",
        )
    if len(unique) > 1:
        return AssetResolution(
            asset_name=asset_name,
            candidates=unique,
            selected=None,
            status="ambiguous",
        )

    return AssetResolution(
        asset_name=asset_name,
        candidates=[],
        selected=None,
        status="unavailable",
    )
```

- [ ] **Step 2: Verify import works**

```bash
cd backend && uv run python -c "
from app.modules.investments.asset_resolution import resolve_asset
r = resolve_asset('Apple')
print(r.status, r.selected.ticker)
"
```

Expected: `resolved AAPL`

---

### Task 3: PriceCoverageAuditService

**Files:**
- Create: `backend/app/modules/investments/price_coverage_audit.py`

**Interfaces:**
- Consumes: `resolve_asset` from `asset_resolution.py`; `get_equity_quote` from `equity_quote_service.py`
- Produces: `audit_asset(asset_name: str) -> CoverageAssetResult`; `run_audit(assets: list[str]) -> AuditReport`; `DEFAULT_ASSETS: list[str]`

- [ ] **Step 1: Create the file**

```python
# backend/app/modules/investments/price_coverage_audit.py
"""Orchestrates asset resolution + equity quote fetching to classify price coverage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.market_intelligence.ingestion.equity_quote_service import get_equity_quote

FRESHNESS_OK_HOURS = 24
FRESHNESS_PARTIAL_HOURS = 72

DEFAULT_ASSETS: list[str] = [
    "Banco Bilbao Vizcaya Argentaria",
    "Apple",
    "Iberdrola",
    "ASML",
    "Caterpillar",
    "Alphabet",
    "Waste Management",
    "TSMC",
    "Johnson & Johnson",
    "Lockheed Martin",
    "NVIDIA",
    "SpaceX",
    "Amazon",
    "Rocket Lab",
    "RTX Corporation",
    "Berkshire Hathaway",
    "Visa",
    "Microsoft",
    "DroneShield",
]


@dataclass
class CoverageAssetResult:
    asset_name: str
    selected_ticker: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    provider: Optional[str]
    price: Optional[float]
    price_currency: Optional[str]
    requires_fx_conversion: bool
    last_update: Optional[datetime]
    freshness_hours: Optional[float]
    from_cache: bool
    status: str  # OK | PARTIAL | AMBIGUOUS | UNAVAILABLE | MANUAL | ERROR
    confidence: float
    notes: list[str] = field(default_factory=list)


@dataclass
class AuditSummary:
    total: int = 0
    ok: int = 0
    partial: int = 0
    ambiguous: int = 0
    manual: int = 0
    unavailable: int = 0
    error: int = 0


@dataclass
class AuditReport:
    generated_at: datetime
    summary: AuditSummary
    assets: list[CoverageAssetResult]


def _classify(
    resolution_status: str,
    quote_success: bool,
    freshness_hours: Optional[float],
    requires_fx: bool,
    provider: Optional[str],
) -> tuple[str, list[str]]:
    notes: list[str] = []

    if resolution_status == "manual":
        return "MANUAL", []
    if resolution_status == "ambiguous":
        return "AMBIGUOUS", ["Múltiples tickers posibles. Requiere confirmación."]
    if resolution_status == "unavailable":
        return "UNAVAILABLE", ["No se encontró ticker para este activo."]
    if not quote_success:
        return "UNAVAILABLE", ["Ningún proveedor devolvió precio."]

    is_partial = False
    if freshness_hours is not None and freshness_hours > FRESHNESS_OK_HOURS:
        is_partial = True
        notes.append(f"Precio retrasado ({freshness_hours:.0f}h).")
    if requires_fx:
        is_partial = True
        notes.append("Precio en divisa extranjera (conversión FX no implementada).")
    if provider == "yfinance":
        is_partial = True
        notes.append("Precio obtenido via yfinance (proveedor secundario).")

    return ("PARTIAL" if is_partial else "OK"), notes


def audit_asset(asset_name: str) -> CoverageAssetResult:
    resolution = resolve_asset(asset_name)

    if resolution.status in ("manual", "unavailable") or resolution.selected is None:
        status = "MANUAL" if resolution.status == "manual" else "UNAVAILABLE"
        if resolution.status == "ambiguous":
            status = "AMBIGUOUS"
        return CoverageAssetResult(
            asset_name=asset_name,
            selected_ticker=None,
            exchange=None,
            currency=None,
            provider=None,
            price=None,
            price_currency=None,
            requires_fx_conversion=False,
            last_update=None,
            freshness_hours=None,
            from_cache=False,
            status=status,
            confidence=0.0,
            notes=["Múltiples tickers posibles. Requiere confirmación."]
            if resolution.status == "ambiguous"
            else [],
        )

    selected = resolution.selected

    try:
        quote = get_equity_quote(
            ticker=selected.ticker,
            yfinance_symbol=selected.yfinance_symbol,
            expected_currency=selected.currency,
        )
    except Exception:
        return CoverageAssetResult(
            asset_name=asset_name,
            selected_ticker=selected.ticker,
            exchange=selected.exchange,
            currency=selected.currency,
            provider=None,
            price=None,
            price_currency=None,
            requires_fx_conversion=False,
            last_update=None,
            freshness_hours=None,
            from_cache=False,
            status="ERROR",
            confidence=selected.confidence,
            notes=["Error técnico al consultar proveedor."],
        )

    now = datetime.now(timezone.utc)
    freshness_hours: Optional[float] = None
    if quote.retrieved_at:
        diff = now - quote.retrieved_at
        freshness_hours = diff.total_seconds() / 3600

    # FX required if portfolio currency (EUR) differs from price currency and price currency is not EUR
    requires_fx = quote.success and quote.currency not in ("EUR", "")

    status, notes = _classify(
        resolution_status=resolution.status,
        quote_success=quote.success,
        freshness_hours=freshness_hours,
        requires_fx=requires_fx,
        provider=quote.provider if quote.success else None,
    )

    return CoverageAssetResult(
        asset_name=asset_name,
        selected_ticker=selected.ticker,
        exchange=selected.exchange,
        currency=selected.currency,
        provider=quote.provider if quote.success else None,
        price=quote.price if quote.success else None,
        price_currency=quote.currency if quote.success else None,
        requires_fx_conversion=requires_fx,
        last_update=quote.retrieved_at if quote.success else None,
        freshness_hours=freshness_hours,
        from_cache=quote.from_cache,
        status=status,
        confidence=selected.confidence,
        notes=notes,
    )


def run_audit(assets: list[str]) -> AuditReport:
    results: list[CoverageAssetResult] = []
    summary = AuditSummary(total=len(assets))

    for name in assets:
        result = audit_asset(name)
        results.append(result)
        s = result.status.lower()
        if s == "ok":
            summary.ok += 1
        elif s == "partial":
            summary.partial += 1
        elif s == "ambiguous":
            summary.ambiguous += 1
        elif s == "manual":
            summary.manual += 1
        elif s == "unavailable":
            summary.unavailable += 1
        elif s == "error":
            summary.error += 1

    return AuditReport(
        generated_at=datetime.now(timezone.utc),
        summary=summary,
        assets=results,
    )
```

- [ ] **Step 2: Verify import works**

```bash
cd backend && uv run python -c "
from app.modules.investments.price_coverage_audit import run_audit, DEFAULT_ASSETS
print(f'{len(DEFAULT_ASSETS)} assets loaded')
"
```

Expected: `19 assets loaded`

---

### Task 4: Backend Endpoints

**Files:**
- Create: `backend/app/modules/investments/price_coverage_routes.py`
- Modify: `backend/app/main.py:16` (add import) and `:67` (add include_router)

**Interfaces:**
- Consumes: `resolve_asset`, `run_audit`, `DEFAULT_ASSETS`, all dataclasses from Tasks 2–3
- Produces: REST endpoints at `/api/investments/price-coverage/`

- [ ] **Step 1: Create the routes file**

```python
# backend/app/modules/investments/price_coverage_routes.py
"""Endpoints for Portfolio Price Coverage Audit."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.investments.price_coverage_audit import (
    DEFAULT_ASSETS,
    AuditReport,
    CoverageAssetResult,
    AuditSummary,
    run_audit,
)

router = APIRouter()


# ── Pydantic response schemas ─────────────────────────────────────────────────

class TickerCandidateOut(BaseModel):
    ticker: str
    yfinance_symbol: str
    name: str
    exchange: str
    currency: str
    asset_type: str
    confidence: float


class AssetResolutionOut(BaseModel):
    asset_name: str
    candidates: list[TickerCandidateOut]
    selected: Optional[TickerCandidateOut]
    status: str


class CoverageAssetOut(BaseModel):
    asset_name: str
    selected_ticker: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    provider: Optional[str]
    price: Optional[float]
    price_currency: Optional[str]
    requires_fx_conversion: bool
    last_update: Optional[datetime]
    freshness_hours: Optional[float]
    from_cache: bool
    status: str
    confidence: float
    notes: list[str]


class AuditSummaryOut(BaseModel):
    total: int
    ok: int
    partial: int
    ambiguous: int
    manual: int
    unavailable: int
    error: int


class AuditReportOut(BaseModel):
    generated_at: datetime
    summary: AuditSummaryOut
    assets: list[CoverageAssetOut]


class AuditRequestAsset(BaseModel):
    name: str


class AuditRequest(BaseModel):
    assets: list[AuditRequestAsset] = []
    force_refresh: bool = False


class ResolveRequest(BaseModel):
    asset_name: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/default-assets", response_model=list[str])
def get_default_assets() -> list[str]:
    return DEFAULT_ASSETS


@router.post("/audit", response_model=AuditReportOut)
def run_price_audit(body: AuditRequest) -> AuditReportOut:
    names = [a.name for a in body.assets] if body.assets else DEFAULT_ASSETS
    report = run_audit(names)
    return AuditReportOut(
        generated_at=report.generated_at,
        summary=AuditSummaryOut(**report.summary.__dict__),
        assets=[CoverageAssetOut(**r.__dict__) for r in report.assets],
    )


@router.post("/resolve", response_model=AssetResolutionOut)
def resolve_asset_endpoint(body: ResolveRequest) -> AssetResolutionOut:
    resolution = resolve_asset(body.asset_name)
    return AssetResolutionOut(
        asset_name=resolution.asset_name,
        candidates=[TickerCandidateOut(**c.__dict__) for c in resolution.candidates],
        selected=TickerCandidateOut(**resolution.selected.__dict__)
        if resolution.selected
        else None,
        status=resolution.status,
    )
```

- [ ] **Step 2: Register the router in main.py**

In `backend/app/main.py`, after line 16 (the market_intelligence import), add:

```python
from app.modules.investments.price_coverage_routes import router as price_coverage_router
```

After line 67 (`app.include_router(investments_router, ...)`), add:

```python
app.include_router(
    price_coverage_router,
    prefix="/api/investments/price-coverage",
    tags=["investments"],
)
```

- [ ] **Step 3: Smoke-test the endpoints**

```bash
cd backend && uv run uvicorn app.main:app --port 8010 &
sleep 3
curl -s http://127.0.0.1:8010/api/investments/price-coverage/default-assets | python -m json.tool | head -5
curl -s -X POST http://127.0.0.1:8010/api/investments/price-coverage/resolve \
  -H "Content-Type: application/json" \
  -d '{"asset_name": "Apple"}' | python -m json.tool
```

Expected: list of 19 strings; resolve returns `{"status": "resolved", "selected": {"ticker": "AAPL", ...}}`

Kill the background server after testing: `pkill -f "uvicorn app.main"` (or press Ctrl+C if running interactively).

---

### Task 5: Backend Tests

**Files:**
- Create: `backend/app/tests/test_price_coverage.py`

**Interfaces:**
- Consumes: `client` fixture from `conftest.py`; `resolve_asset` from `asset_resolution.py`; `audit_asset`, `run_audit` from `price_coverage_audit.py`; `get_equity_quote` from `equity_quote_service.py`

- [ ] **Step 1: Write tests**

```python
# backend/app/tests/test_price_coverage.py
"""Tests for Portfolio Price Coverage Audit.

All external providers (Finnhub, Alpha Vantage, yfinance) are mocked.
No internet access required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.investments.price_coverage_audit import (
    DEFAULT_ASSETS,
    audit_asset,
    run_audit,
)
from app.modules.market_intelligence.ingestion.equity_quote_service import EquityQuoteResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_quote(price: float = 150.0, currency: str = "USD", provider: str = "finnhub") -> EquityQuoteResult:
    return EquityQuoteResult(
        ticker="TEST",
        price=price,
        currency=currency,
        provider=provider,
        retrieved_at=datetime.now(timezone.utc),
        success=True,
    )


def _mock_failed_quote() -> EquityQuoteResult:
    return EquityQuoteResult(
        ticker="TEST",
        price=0.0,
        currency="",
        provider="none",
        retrieved_at=datetime.now(timezone.utc),
        success=False,
        error="All providers failed",
    )


# ── Asset Resolution ──────────────────────────────────────────────────────────

def test_resolve_apple():
    r = resolve_asset("Apple")
    assert r.status == "resolved"
    assert r.selected is not None
    assert r.selected.ticker == "AAPL"
    assert r.selected.exchange == "NASDAQ"
    assert r.selected.currency == "USD"


def test_resolve_iberdrola():
    r = resolve_asset("Iberdrola")
    assert r.status == "resolved"
    assert r.selected.ticker == "IBE.MC"
    assert r.selected.exchange == "BME"
    assert r.selected.currency == "EUR"


def test_resolve_bbva():
    r = resolve_asset("Banco Bilbao Vizcaya Argentaria")
    assert r.status == "resolved"
    assert r.selected.ticker == "BBVA"
    assert r.selected.yfinance_symbol == "BBVA.MC"
    assert r.selected.exchange == "BME"
    assert r.selected.currency == "EUR"


def test_resolve_asml():
    r = resolve_asset("ASML")
    assert r.status == "resolved"
    assert r.selected.ticker == "ASML"
    assert r.selected.yfinance_symbol == "ASML.AS"
    assert r.selected.exchange == "AMS"
    assert r.selected.currency == "EUR"


def test_resolve_spacex():
    r = resolve_asset("SpaceX")
    assert r.status == "resolved"
    assert r.selected.ticker == "SPCX"
    assert r.selected.exchange == "NASDAQ"


def test_resolve_droneshield():
    r = resolve_asset("DroneShield")
    assert r.status == "resolved"
    assert r.selected.ticker == "DRO.AX"
    assert r.selected.exchange == "ASX"
    assert r.selected.currency == "AUD"


def test_resolve_unknown():
    r = resolve_asset("Empresa Inventada XYZ")
    assert r.status == "unavailable"
    assert r.selected is None


# ── Coverage Audit ────────────────────────────────────────────────────────────

QUOTE_PATH = "app.modules.investments.price_coverage_audit.get_equity_quote"


def test_audit_ok_when_provider_returns_price():
    with patch(QUOTE_PATH, return_value=_mock_quote(150.0, "USD", "finnhub")):
        result = audit_asset("Apple")
    assert result.status == "OK"
    assert result.selected_ticker == "AAPL"
    assert result.price == 150.0
    assert result.provider == "finnhub"


def test_audit_partial_when_yfinance_used():
    with patch(QUOTE_PATH, return_value=_mock_quote(150.0, "USD", "yfinance")):
        result = audit_asset("Apple")
    assert result.status == "PARTIAL"
    assert any("yfinance" in n for n in result.notes)


def test_audit_partial_when_fx_required():
    # DroneShield is AUD → requires_fx_conversion should trigger PARTIAL
    with patch(QUOTE_PATH, return_value=_mock_quote(1.2, "AUD", "finnhub")):
        result = audit_asset("DroneShield")
    # AUD != EUR → requires_fx_conversion = True → PARTIAL
    assert result.status == "PARTIAL"
    assert result.requires_fx_conversion is True


def test_audit_unavailable_when_all_providers_fail():
    with patch(QUOTE_PATH, return_value=_mock_failed_quote()):
        result = audit_asset("Apple")
    assert result.status == "UNAVAILABLE"
    assert result.price is None
    assert result.provider is None


def test_audit_error_when_provider_raises():
    with patch(QUOTE_PATH, side_effect=RuntimeError("connection timeout")):
        result = audit_asset("Apple")
    assert result.status == "ERROR"
    assert result.price is None


def test_audit_unavailable_when_asset_not_known():
    result = audit_asset("Empresa Inventada XYZ")
    assert result.status == "UNAVAILABLE"


def test_run_audit_summary_totals():
    ok_quote = _mock_quote(100.0, "USD", "finnhub")
    fail_quote = _mock_failed_quote()
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return ok_quote
        return fail_quote

    with patch(QUOTE_PATH, side_effect=side_effect):
        report = run_audit(["Apple", "Microsoft"])

    assert report.summary.total == 2
    assert report.summary.ok + report.summary.partial + report.summary.unavailable == 2
    assert len(report.assets) == 2


def test_run_audit_does_not_raise_on_provider_failure():
    with patch(QUOTE_PATH, side_effect=RuntimeError("timeout")):
        report = run_audit(["Apple", "Microsoft"])
    # Should not raise; all assets should be ERROR
    assert all(r.status == "ERROR" for r in report.assets)


def test_default_assets_count():
    assert len(DEFAULT_ASSETS) == 19


# ── API Endpoints ─────────────────────────────────────────────────────────────

def test_get_default_assets(client):
    r = client.get("/api/investments/price-coverage/default-assets")
    assert r.status_code == 200
    assets = r.json()
    assert len(assets) == 19
    assert "Apple" in assets


def test_resolve_endpoint(client):
    r = client.post(
        "/api/investments/price-coverage/resolve",
        json={"asset_name": "Apple"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["selected"]["ticker"] == "AAPL"


def test_resolve_endpoint_unknown(client):
    r = client.post(
        "/api/investments/price-coverage/resolve",
        json={"asset_name": "Empresa Fantasma"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "unavailable"
    assert data["selected"] is None


def test_audit_endpoint_summary(client):
    ok_quote = _mock_quote(200.0, "USD", "finnhub")
    with patch(QUOTE_PATH, return_value=ok_quote):
        r = client.post(
            "/api/investments/price-coverage/audit",
            json={"assets": [{"name": "Apple"}, {"name": "Microsoft"}], "force_refresh": False},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 2
    assert "generated_at" in data
    assert len(data["assets"]) == 2


def test_audit_endpoint_empty_body_uses_defaults(client):
    ok_quote = _mock_quote(100.0, "USD", "finnhub")
    with patch(QUOTE_PATH, return_value=ok_quote):
        r = client.post(
            "/api/investments/price-coverage/audit",
            json={},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 19
```

- [ ] **Step 2: Run the tests**

```bash
cd backend && uv run pytest app/tests/test_price_coverage.py -v
```

Expected: all tests pass. If `run_audit_does_not_raise_on_provider_failure` fails, it means exceptions in `audit_asset` aren't caught — fix the try/except in `price_coverage_audit.py:audit_asset`.

- [ ] **Step 3: Run full test suite to check for regressions**

```bash
cd backend && uv run pytest -x -q
```

Expected: all existing tests still pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/market_intelligence/ingestion/equity_quote_service.py \
        backend/app/modules/investments/asset_resolution.py \
        backend/app/modules/investments/price_coverage_audit.py \
        backend/app/modules/investments/price_coverage_routes.py \
        backend/app/tests/test_price_coverage.py \
        backend/app/main.py
git commit -m "feat: add Portfolio Price Coverage Audit backend (asset resolution, equity quote service, audit service, endpoints, tests)"
```

---

### Task 6: Frontend Types and API Client

**Files:**
- Create: `apps/desktop/src/lib/types/price-coverage.ts`
- Create: `apps/desktop/src/lib/api/price-coverage.ts`
- Create: `apps/desktop/src/lib/hooks/usePriceCoverage.ts`

**Interfaces:**
- Produces: `AuditReport`, `CoverageAsset`, `AuditSummary` types; `getDefaultAssets()`, `runAudit()`, `resolveAsset()` API functions; `usePriceCoverage()` hook

- [ ] **Step 1: Create types file**

```typescript
// apps/desktop/src/lib/types/price-coverage.ts

export type CoverageStatus =
  | "OK"
  | "PARTIAL"
  | "AMBIGUOUS"
  | "UNAVAILABLE"
  | "MANUAL"
  | "ERROR";

export interface TickerCandidate {
  ticker: string;
  yfinance_symbol: string;
  name: string;
  exchange: string;
  currency: string;
  asset_type: string;
  confidence: number;
}

export interface AssetResolutionResponse {
  asset_name: string;
  candidates: TickerCandidate[];
  selected: TickerCandidate | null;
  status: string;
}

export interface CoverageAsset {
  asset_name: string;
  selected_ticker: string | null;
  exchange: string | null;
  currency: string | null;
  provider: string | null;
  price: number | null;
  price_currency: string | null;
  requires_fx_conversion: boolean;
  last_update: string | null;
  freshness_hours: number | null;
  from_cache: boolean;
  status: CoverageStatus;
  confidence: number;
  notes: string[];
}

export interface AuditSummary {
  total: number;
  ok: number;
  partial: number;
  ambiguous: number;
  manual: number;
  unavailable: number;
  error: number;
}

export interface AuditReport {
  generated_at: string;
  summary: AuditSummary;
  assets: CoverageAsset[];
}
```

- [ ] **Step 2: Create API client file**

```typescript
// apps/desktop/src/lib/api/price-coverage.ts

import type { AuditReport, AssetResolutionResponse } from "@/lib/types/price-coverage";
import { api } from "./client";

export const getDefaultAssets = () =>
  api.get<string[]>("/api/investments/price-coverage/default-assets");

export const runAudit = (assets: { name: string }[] = [], forceRefresh = false) =>
  api.post<AuditReport>("/api/investments/price-coverage/audit", {
    assets,
    force_refresh: forceRefresh,
  });

export const resolveAsset = (assetName: string) =>
  api.post<AssetResolutionResponse>("/api/investments/price-coverage/resolve", {
    asset_name: assetName,
  });
```

- [ ] **Step 3: Create hook file**

```typescript
// apps/desktop/src/lib/hooks/usePriceCoverage.ts

import { useCallback, useState } from "react";
import { runAudit, resolveAsset } from "@/lib/api/price-coverage";
import type { AuditReport, AssetResolutionResponse } from "@/lib/types/price-coverage";

export function usePriceCoverage() {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audit = useCallback(async (assets: { name: string }[] = []) => {
    setLoading(true);
    setError(null);
    try {
      const result = await runAudit(assets);
      setReport(result);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al auditar cobertura");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { report, loading, error, audit };
}

export function useAssetResolve() {
  const [resolution, setResolution] = useState<AssetResolutionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const resolve = useCallback(async (assetName: string) => {
    setLoading(true);
    try {
      const result = await resolveAsset(assetName);
      setResolution(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  return { resolution, loading, resolve };
}
```

- [ ] **Step 4: Type-check**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: no errors.

---

### Task 7: Frontend Components

**Files:**
- Create: `apps/desktop/src/features/investments/price-coverage/PriceCoverageStatusBadge.tsx`
- Create: `apps/desktop/src/features/investments/price-coverage/PriceCoverageSummaryCards.tsx`
- Create: `apps/desktop/src/features/investments/price-coverage/PriceCoverageTable.tsx`
- Create: `apps/desktop/src/features/investments/price-coverage/PriceCoveragePage.tsx`

**Interfaces:**
- Consumes: `CoverageStatus`, `CoverageAsset`, `AuditSummary`, `AuditReport` from `price-coverage.ts`; `usePriceCoverage` hook

- [ ] **Step 1: Create PriceCoverageStatusBadge**

```tsx
// apps/desktop/src/features/investments/price-coverage/PriceCoverageStatusBadge.tsx

import type { CoverageStatus } from "@/lib/types/price-coverage";

const CONFIG: Record<CoverageStatus, { label: string; className: string }> = {
  OK: { label: "OK", className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25" },
  PARTIAL: { label: "Parcial", className: "bg-amber-500/15 text-amber-400 border border-amber-500/25" },
  AMBIGUOUS: { label: "Ambiguo", className: "bg-blue-500/15 text-blue-400 border border-blue-500/25" },
  UNAVAILABLE: { label: "Sin cobertura", className: "bg-red-500/15 text-red-400 border border-red-500/25" },
  MANUAL: { label: "Manual", className: "bg-stone-500/15 text-stone-400 border border-stone-500/25" },
  ERROR: { label: "Error", className: "bg-red-700/20 text-red-300 border border-red-700/30" },
};

export default function PriceCoverageStatusBadge({ status }: { status: CoverageStatus }) {
  const { label, className } = CONFIG[status] ?? CONFIG.ERROR;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${className}`}>
      {label}
    </span>
  );
}
```

- [ ] **Step 2: Create PriceCoverageSummaryCards**

```tsx
// apps/desktop/src/features/investments/price-coverage/PriceCoverageSummaryCards.tsx

import type { AuditSummary } from "@/lib/types/price-coverage";

interface CardProps {
  label: string;
  value: number;
  highlight?: string;
}

function Card({ label, value, highlight = "text-on-dark" }: CardProps) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-surface-deep border border-hairline-dark px-5 py-4 min-w-[110px]">
      <span className={`text-2xl font-bold ${highlight}`}>{value}</span>
      <span className="text-xs text-mute">{label}</span>
    </div>
  );
}

export default function PriceCoverageSummaryCards({ summary }: { summary: AuditSummary }) {
  const needsReview = summary.partial + summary.ambiguous + summary.error;
  return (
    <div className="flex flex-wrap gap-3">
      <Card label="Total activos" value={summary.total} />
      <Card label="OK" value={summary.ok} highlight="text-emerald-400" />
      <Card label="Revisar" value={needsReview} highlight={needsReview > 0 ? "text-amber-400" : "text-on-dark"} />
      <Card label="Manual" value={summary.manual} highlight="text-stone-400" />
      <Card label="Sin cobertura" value={summary.unavailable} highlight={summary.unavailable > 0 ? "text-red-400" : "text-on-dark"} />
    </div>
  );
}
```

- [ ] **Step 3: Create PriceCoverageTable**

```tsx
// apps/desktop/src/features/investments/price-coverage/PriceCoverageTable.tsx

import type { CoverageAsset } from "@/lib/types/price-coverage";
import PriceCoverageStatusBadge from "./PriceCoverageStatusBadge";

function formatPrice(price: number | null, currency: string | null): string {
  if (price === null || price === 0) return "—";
  return `${price.toFixed(2)} ${currency ?? ""}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-ES", {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}

interface Props {
  assets: CoverageAsset[];
  onRetry: (assetName: string) => void;
}

export default function PriceCoverageTable({ assets, onRetry }: Props) {
  if (assets.length === 0) {
    return (
      <p className="text-mute text-sm py-8 text-center">
        Pulsa "Auditar" para comprobar la cobertura de precios.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-hairline-dark">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-hairline-dark bg-surface-deep">
            {["Activo", "Ticker", "Mercado", "Divisa", "Proveedor", "Precio", "Estado", "Última act.", ""].map((h) => (
              <th key={h} className="px-4 py-3 text-[11px] font-medium text-mute uppercase tracking-wide whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr
              key={asset.asset_name}
              className="border-b border-hairline-dark last:border-0 hover:bg-white/[.02] transition-colors"
            >
              <td className="px-4 py-3 font-medium text-on-dark whitespace-nowrap">{asset.asset_name}</td>
              <td className="px-4 py-3 text-stone font-mono text-xs">{asset.selected_ticker ?? "—"}</td>
              <td className="px-4 py-3 text-stone">{asset.exchange ?? "—"}</td>
              <td className="px-4 py-3 text-stone">{asset.currency ?? "—"}</td>
              <td className="px-4 py-3 text-stone capitalize">{asset.provider ?? "—"}</td>
              <td className="px-4 py-3 text-on-dark font-mono">{formatPrice(asset.price, asset.price_currency)}</td>
              <td className="px-4 py-3">
                <PriceCoverageStatusBadge status={asset.status} />
              </td>
              <td className="px-4 py-3 text-stone text-xs">{formatDate(asset.last_update)}</td>
              <td className="px-4 py-3">
                {(asset.status === "UNAVAILABLE" || asset.status === "ERROR" || asset.status === "PARTIAL") && (
                  <button
                    onClick={() => onRetry(asset.asset_name)}
                    className="text-xs text-primary-bright hover:underline"
                  >
                    Reintentar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Create PriceCoveragePage**

```tsx
// apps/desktop/src/features/investments/price-coverage/PriceCoveragePage.tsx

import { useCallback, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import Spinner from "@/components/ui/Spinner";
import { usePriceCoverage } from "@/lib/hooks/usePriceCoverage";
import PriceCoverageSummaryCards from "./PriceCoverageSummaryCards";
import PriceCoverageTable from "./PriceCoverageTable";

export default function PriceCoveragePage() {
  const { report, loading, error, audit } = usePriceCoverage();

  // Load on mount with default assets
  useEffect(() => {
    audit();
  }, [audit]);

  const handleRetry = useCallback(
    (assetName: string) => {
      audit([{ name: assetName }]);
    },
    [audit]
  );

  const handleAuditAll = () => audit();

  return (
    <div className="flex flex-col gap-6 p-6 max-w-screen-xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-on-dark">Cobertura de precios</h1>
          <p className="text-sm text-mute mt-1">
            Comprueba si tus acciones pueden actualizarse automáticamente con los proveedores actuales.
          </p>
        </div>
        <button
          onClick={handleAuditAll}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Auditar
        </button>
      </div>

      {/* Summary */}
      {report && <PriceCoverageSummaryCards summary={report.summary} />}

      {/* Loading */}
      {loading && !report && (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Table */}
      {report && (
        <PriceCoverageTable
          assets={report.assets}
          onRetry={handleRetry}
        />
      )}

      {/* Generated at */}
      {report && (
        <p className="text-xs text-mute">
          Generado el{" "}
          {new Date(report.generated_at).toLocaleString("es-ES", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Type-check**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: no errors. Fix any type mismatches before proceeding.

---

### Task 8: Frontend Routing and Navigation

**Files:**
- Modify: `apps/desktop/src/App.tsx`
- Modify: `apps/desktop/src/features/investments/InvestmentsPage.tsx`

**Interfaces:**
- Consumes: `PriceCoveragePage` component

- [ ] **Step 1: Add route in App.tsx**

In `apps/desktop/src/App.tsx`, add the import at the top:

```tsx
import PriceCoveragePage from "@/features/investments/price-coverage/PriceCoveragePage";
```

Inside the `<Route path="investments" element={<InvestmentsPage />}>` block — or after it as a sibling — add:

```tsx
<Route path="investments/price-coverage" element={<PriceCoveragePage />} />
```

The full routes block after modification:

```tsx
<Route path="/" element={<RootLayout />}>
  <Route index element={<OverviewPage />} />
  <Route path="spending" element={<SpendingPage />} />
  <Route path="transactions" element={<TransactionsPage />} />
  <Route path="accounts" element={<AccountsPage />} />
  <Route path="imports" element={<ImportsPage />} />
  <Route path="investments" element={<InvestmentsPage />} />
  <Route path="investments/price-coverage" element={<PriceCoveragePage />} />
  <Route path="economy" element={<EconomyPage />} />
  <Route path="markets" element={<MarketsPage />} />
  <Route path="goals" element={<GoalsPage />} />
  <Route path="insights" element={<InsightsPage />} />
  <Route path="assistant" element={<AssistantPage />} />
  <Route path="settings" element={<SettingsPage />} />
</Route>
```

- [ ] **Step 2: Add navigation link in InvestmentsPage.tsx**

In `apps/desktop/src/features/investments/InvestmentsPage.tsx`, add the import at the top:

```tsx
import { useNavigate } from "react-router-dom";
```

Inside `InvestmentsPage`, after the existing state declarations, add:

```tsx
const navigate = useNavigate();
```

Find the section that renders the header buttons (near the `RefreshCw` button for price refresh). Add a new button alongside it:

```tsx
<button
  onClick={() => navigate("/investments/price-coverage")}
  className="flex items-center gap-2 px-3 py-2 rounded-lg border border-hairline-dark text-stone hover:text-on-dark hover:bg-white/[.035] text-sm transition-colors"
>
  Cobertura de precios
</button>
```

- [ ] **Step 3: Type-check**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/lib/types/price-coverage.ts \
        apps/desktop/src/lib/api/price-coverage.ts \
        apps/desktop/src/lib/hooks/usePriceCoverage.ts \
        apps/desktop/src/features/investments/price-coverage/ \
        apps/desktop/src/App.tsx \
        apps/desktop/src/features/investments/InvestmentsPage.tsx
git commit -m "feat: add PriceCoverage UI (page, table, summary cards, status badge, routing)"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Task |
|---|---|
| 1. Asset Resolution Service | Task 2 |
| 2. Price Coverage Audit Service | Task 3 |
| 3. Coverage statuses (OK/PARTIAL/AMBIGUOUS/UNAVAILABLE/MANUAL/ERROR) | Task 3 (`_classify`) |
| 4. Integration with MI providers (Finnhub, AlphaVantage, yfinance fallback) | Task 1 |
| 5. Fallback chain | Task 1 (`get_equity_quote` try chain) |
| 6. FX detection (`requires_fx_conversion`) | Task 3 (`audit_asset`) |
| 7. Endpoints (default-assets, audit, resolve) | Task 4 |
| 8. Frontend page and table | Task 7 |
| 9. UX Dark Premium | Task 7 |
| 10. Relation to Portfolio Import Assistant | Addressed via DEFAULT_ASSETS + AssetResolution |
| 11. Data model (no new tables, on-demand report) | No new migration needed |
| 12. Backend tests | Task 5 |
| 13. Frontend type check | Tasks 6–8 |
| 14. Docs update | Not in tasks — add as separate manual step if needed |

**Placeholder scan:** None found.

**Type consistency:**
- `EquityQuoteResult` defined in Task 1, consumed in Task 3 ✓
- `TickerCandidate`, `AssetResolution` defined in Task 2, consumed in Tasks 3–4 ✓
- `CoverageAssetResult`, `AuditReport`, `AuditSummary` defined in Task 3, consumed in Task 4 ✓
- `CoverageAsset`, `AuditReport`, `AuditSummary` TypeScript types defined in Task 6, consumed in Tasks 7–8 ✓
- `usePriceCoverage` defined in Task 6, consumed in Task 7 ✓
- `PriceCoveragePage` defined in Task 7, consumed in Task 8 ✓
