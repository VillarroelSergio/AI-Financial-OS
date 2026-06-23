# Market Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar la pantalla Market Watch con 36 activos de mercado actualizándose automáticamente cada 5 segundos con experiencia visual tipo Trade Republic.

**Architecture:** Backend con caché en memoria (TTL 15s) sobre yfinance — el frontend hace polling cada 5s y siempre recibe respuesta inmediata; yfinance se llama en background cuando el caché expira. Frontend React con `useInterval` pausable, animaciones flash en cambios de precio, sparklines intraday con Recharts y tabs de categoría pill-button.

**Tech Stack:** FastAPI + yfinance (ya instalado) · React + TypeScript + Recharts + Tailwind · SQLite no requerido (sin modelos nuevos)

## Global Constraints

- UI en español: "Mercados", "En vivo", "Mat. Primas", "Volatilidad", "Actualizado hace Xs"
- Design System Dark Premium: canvas-dark `#000000`, surface-elevated `#16181a`, hairline-dark `rgba(255,255,255,0.12)`
- accent-teal `#00a87e` para positivo, accent-danger `#e23b4a` para negativo
- Badges: `badge-semantic` — `caption rounded-full px-[10px] py-[3px]` con fondo semitransparente
- Cards: `rounded-lg border border-hairline-dark bg-surface-elevated`
- Todos los textos y labels en español
- Errores FastAPI: `{"detail": {"error": {"code": "...", "message": "...", "details": {}}}}` (patrón existente)
- `price: null` si yfinance falla para un ticker — nunca bloquear el resto
- Polling: 5 segundos en frontend; caché backend TTL: 15 segundos
- Recharts para sparklines — no mezclar librerías de gráficas
- 5 estados en todos los componentes con datos: loading/empty/error/partial/success

---

## Estructura de archivos

**Backend (crear/modificar):**
- Create: `backend/app/modules/market_data/schemas.py`
- Replace: `backend/app/modules/market_data/routes.py` (scaffold vacío)
- Create: `backend/app/modules/market_data/service.py`
- Create: `backend/app/tests/test_market_data.py`

**Frontend (crear/modificar):**
- Modify: `apps/desktop/src/lib/types/index.ts` — añadir `MarketQuote`
- Create: `apps/desktop/src/lib/api/markets.ts`
- Modify: `apps/desktop/src/lib/api/mock-data.ts` — añadir mock quotes
- Create: `apps/desktop/src/lib/hooks/useMarkets.ts`
- Create: `apps/desktop/src/features/markets/components/LiveIndicator.tsx`
- Create: `apps/desktop/src/features/markets/components/MiniSparkline.tsx`
- Create: `apps/desktop/src/features/markets/components/QuoteRow.tsx`
- Create: `apps/desktop/src/features/markets/components/CategoryTabs.tsx`
- Replace: `apps/desktop/src/features/markets/MarketsPage.tsx`
- Modify: `tools/ux-snapshot/snapshot-routes.ts`

---

## Task 1: Backend — Schemas + Service

**Files:**
- Create: `backend/app/modules/market_data/schemas.py`
- Create: `backend/app/modules/market_data/service.py`

**Interfaces:**
- Produces: `QuoteOut` Pydantic model · `ASSET_CATALOG` list · `get_quotes(category)` → `list[dict]`

- [ ] **Step 1: Crear schemas.py**

```python
# backend/app/modules/market_data/schemas.py
from pydantic import BaseModel


class QuoteOut(BaseModel):
    symbol: str
    name: str
    category: str
    price: float | None
    change_pct: float | None
    currency: str
    sparkline: list[float]
    last_updated: str
    market_open: bool
```

- [ ] **Step 2: Crear service.py con ASSET_CATALOG**

```python
# backend/app/modules/market_data/service.py
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf

from app.modules.market_data.schemas import QuoteOut


@dataclass
class AssetConfig:
    symbol: str
    name: str
    category: str
    currency: str


ASSET_CATALOG: list[AssetConfig] = [
    # Europa
    AssetConfig("^IBEX", "IBEX 35", "indices_eu", "EUR"),
    AssetConfig("^STOXX50E", "Euro Stoxx 50", "indices_eu", "EUR"),
    AssetConfig("^STOXX", "STOXX Europe 600", "indices_eu", "EUR"),
    AssetConfig("^GDAXI", "DAX", "indices_eu", "EUR"),
    AssetConfig("^FCHI", "CAC 40", "indices_eu", "EUR"),
    AssetConfig("^FTSE", "FTSE 100", "indices_eu", "GBP"),
    # EEUU
    AssetConfig("^GSPC", "S&P 500", "indices_us", "USD"),
    AssetConfig("^NDX", "Nasdaq 100", "indices_us", "USD"),
    AssetConfig("^DJI", "Dow Jones", "indices_us", "USD"),
    AssetConfig("^RUT", "Russell 2000", "indices_us", "USD"),
    # Asia
    AssetConfig("^N225", "Nikkei 225", "indices_asia", "JPY"),
    AssetConfig("^HSI", "Hang Seng", "indices_asia", "HKD"),
    AssetConfig("000001.SS", "Shanghai Composite", "indices_asia", "CNY"),
    AssetConfig("^NSEI", "Nifty 50", "indices_asia", "INR"),
    # Cripto
    AssetConfig("BTC-USD", "Bitcoin", "crypto", "USD"),
    AssetConfig("ETH-USD", "Ethereum", "crypto", "USD"),
    AssetConfig("BNB-USD", "BNB", "crypto", "USD"),
    AssetConfig("SOL-USD", "Solana", "crypto", "USD"),
    # Divisas
    AssetConfig("EURUSD=X", "EUR/USD", "fx", "USD"),
    AssetConfig("EURGBP=X", "EUR/GBP", "fx", "GBP"),
    AssetConfig("EURJPY=X", "EUR/JPY", "fx", "JPY"),
    AssetConfig("GBPUSD=X", "GBP/USD", "fx", "USD"),
    AssetConfig("JPY=X", "USD/JPY", "fx", "JPY"),
    AssetConfig("CHF=X", "USD/CHF", "fx", "CHF"),
    # Bonos 10Y (tickers pueden fallar — precio null es aceptable, ver TD-07)
    AssetConfig("^TNX", "Treasury EEUU 10Y", "bonds", "USD"),
    AssetConfig("^TMBMKDE-10Y", "Bund Alemania 10Y", "bonds", "EUR"),
    AssetConfig("^TMBMKES-10Y", "Bono España 10Y", "bonds", "EUR"),
    AssetConfig("^TMBMKGB-10Y", "Gilt UK 10Y", "bonds", "GBP"),
    AssetConfig("^TMBMKIT-10Y", "BTP Italia 10Y", "bonds", "EUR"),
    # Materias primas
    AssetConfig("GC=F", "Oro", "commodities", "USD"),
    AssetConfig("SI=F", "Plata", "commodities", "USD"),
    AssetConfig("BZ=F", "Petróleo Brent", "commodities", "USD"),
    AssetConfig("CL=F", "Petróleo WTI", "commodities", "USD"),
    AssetConfig("NG=F", "Gas Natural", "commodities", "USD"),
    AssetConfig("HG=F", "Cobre", "commodities", "USD"),
    # Volatilidad
    AssetConfig("^VIX", "VIX", "volatility", "USD"),
]

_cache: dict = {"quotes": [], "updated_at": None, "refreshing": False}
CACHE_TTL = 15.0


def _fetch_quote(asset: AssetConfig) -> QuoteOut:
    try:
        ticker = yf.Ticker(asset.symbol)
        fast = ticker.fast_info
        price = fast.last_price
        prev_close = fast.previous_close
        change_pct = (
            float((price - prev_close) / prev_close * 100)
            if price is not None and prev_close and prev_close != 0
            else None
        )
        try:
            hist = ticker.history(period="1d", interval="5m")
            sparkline = [float(v) for v in hist["Close"].dropna().tolist()] if not hist.empty else []
        except Exception:
            sparkline = []
        try:
            market_state = getattr(fast, "market_state", None)
            market_open = market_state == "REGULAR" if market_state else True
        except Exception:
            market_open = True
        return QuoteOut(
            symbol=asset.symbol,
            name=asset.name,
            category=asset.category,
            price=float(price) if price is not None else None,
            change_pct=change_pct,
            currency=asset.currency,
            sparkline=sparkline,
            last_updated=datetime.now(timezone.utc).isoformat(),
            market_open=market_open,
        )
    except Exception:
        return QuoteOut(
            symbol=asset.symbol,
            name=asset.name,
            category=asset.category,
            price=None,
            change_pct=None,
            currency=asset.currency,
            sparkline=[],
            last_updated=datetime.now(timezone.utc).isoformat(),
            market_open=False,
        )


def _refresh_cache() -> None:
    if _cache["refreshing"]:
        return
    _cache["refreshing"] = True
    try:
        quotes = [_fetch_quote(asset) for asset in ASSET_CATALOG]
        _cache["quotes"] = [q.model_dump() for q in quotes]
        _cache["updated_at"] = time.time()
    finally:
        _cache["refreshing"] = False


def get_quotes(category: str | None = None) -> list[dict]:
    now = time.time()
    is_stale = _cache["updated_at"] is None or (now - _cache["updated_at"]) > CACHE_TTL

    if is_stale and not _cache["refreshing"]:
        if _cache["quotes"]:
            threading.Thread(target=_refresh_cache, daemon=True).start()
        else:
            _refresh_cache()

    quotes = _cache["quotes"]
    if category:
        quotes = [q for q in quotes if q["category"] == category]
    return quotes
```

- [ ] **Step 3: Verificar que el módulo importa sin errores**

```bash
cd backend && uv run python -c "from app.modules.market_data.service import get_quotes, ASSET_CATALOG; print(len(ASSET_CATALOG))"
```

Expected: `36`

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/market_data/schemas.py backend/app/modules/market_data/service.py
git commit -m "feat(markets): add QuoteOut schema and MarketDataService with in-memory cache"
```

---

## Task 2: Backend — Routes + Tests

**Files:**
- Replace: `backend/app/modules/market_data/routes.py`
- Create: `backend/app/tests/test_market_data.py`

**Interfaces:**
- Consumes: `get_quotes(category)` de `service.py` · `QuoteOut` de `schemas.py`
- Produces: `GET /api/markets/quotes` → `list[QuoteOut]` (ya registrado en `main.py` en prefix `/api/markets`)

- [ ] **Step 1: Escribir tests primero**

```python
# backend/app/tests/test_market_data.py
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
```

- [ ] **Step 2: Ejecutar tests — deben FALLAR**

```bash
cd backend && uv run pytest app/tests/test_market_data.py -v
```

Expected: `FAILED — router has no routes`

- [ ] **Step 3: Implementar routes.py**

```python
# backend/app/modules/market_data/routes.py
from fastapi import APIRouter

from app.modules.market_data.schemas import QuoteOut
from app.modules.market_data.service import get_quotes

router = APIRouter()


@router.get("/quotes", response_model=list[QuoteOut])
def list_quotes(category: str | None = None):
    return get_quotes(category)
```

- [ ] **Step 4: Ejecutar tests — deben PASAR**

```bash
cd backend && uv run pytest app/tests/test_market_data.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Ejecutar suite completa para verificar no hay regresiones**

```bash
cd backend && uv run pytest -v
```

Expected: todos los tests previos siguen pasando.

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/market_data/routes.py backend/app/tests/test_market_data.py
git commit -m "feat(markets): add GET /api/markets/quotes endpoint with category filter"
```

---

## Task 3: Frontend — Types + API Client + Mock Data

**Files:**
- Modify: `apps/desktop/src/lib/types/index.ts`
- Create: `apps/desktop/src/lib/api/markets.ts`
- Modify: `apps/desktop/src/lib/api/mock-data.ts`

**Interfaces:**
- Produces: `MarketQuote` type · `getQuotes(category?)` API function · `mockMarketQuotes` array

- [ ] **Step 1: Añadir tipo MarketQuote a types/index.ts**

Añadir al final del archivo `apps/desktop/src/lib/types/index.ts`:

```typescript
// Market Watch
export type MarketCategory =
  | "indices_eu"
  | "indices_us"
  | "indices_asia"
  | "crypto"
  | "fx"
  | "bonds"
  | "commodities"
  | "volatility";

export interface MarketQuote {
  symbol: string;
  name: string;
  category: MarketCategory;
  price: number | null;
  change_pct: number | null;
  currency: string;
  sparkline: number[];
  last_updated: string;
  market_open: boolean;
}
```

- [ ] **Step 2: Crear markets.ts API client**

```typescript
// apps/desktop/src/lib/api/markets.ts
import type { MarketQuote } from "@/lib/types";
import { api } from "./client";

export const getQuotes = (category?: string) =>
  api.get<MarketQuote[]>(
    `/api/markets/quotes${category ? `?category=${category}` : ""}`
  );
```

- [ ] **Step 3: Añadir mock data a mock-data.ts**

Primero añadir `MarketQuote` al import existente en la primera línea de `mock-data.ts`:

```typescript
import type { Account, Category, Transaction, DashboardOverview, HoldingEnriched, InvestmentAsset, InvestmentSummary, MarketQuote } from "@/lib/types";
```

Luego añadir antes de la función `getMockResponse`:

```typescript
// Sparkline sintético: tendencia con ruido
function makeSparkline(base: number, trend: number): number[] {
  return Array.from({ length: 20 }, (_, i) => {
    const noise = (Math.sin(i * 1.3) + Math.cos(i * 0.7)) * base * 0.003;
    return parseFloat((base + trend * i * 0.1 + noise).toFixed(4));
  });
}

export const mockMarketQuotes: MarketQuote[] = [
  // Europa
  { symbol: "^IBEX", name: "IBEX 35", category: "indices_eu", price: 12843.50, change_pct: 0.73, currency: "EUR", sparkline: makeSparkline(12750, 9.3), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^STOXX50E", name: "Euro Stoxx 50", category: "indices_eu", price: 5312.80, change_pct: 0.45, currency: "EUR", sparkline: makeSparkline(5289, 2.4), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^STOXX", name: "STOXX Europe 600", category: "indices_eu", price: 546.20, change_pct: 0.38, currency: "EUR", sparkline: makeSparkline(544, 0.2), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^GDAXI", name: "DAX", category: "indices_eu", price: 23156.40, change_pct: 0.52, currency: "EUR", sparkline: makeSparkline(23036, 12.0), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^FCHI", name: "CAC 40", category: "indices_eu", price: 7834.60, change_pct: 0.31, currency: "EUR", sparkline: makeSparkline(7810, 2.5), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^FTSE", name: "FTSE 100", category: "indices_eu", price: 8642.30, change_pct: -0.12, currency: "GBP", sparkline: makeSparkline(8660, -1.8), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  // EEUU
  { symbol: "^GSPC", name: "S&P 500", category: "indices_us", price: 5945.28, change_pct: 1.12, currency: "USD", sparkline: makeSparkline(5879, 6.6), last_updated: "2026-06-23T09:30:00Z", market_open: false },
  { symbol: "^NDX", name: "Nasdaq 100", category: "indices_us", price: 21432.60, change_pct: 1.38, currency: "USD", sparkline: makeSparkline(21138, 29.4), last_updated: "2026-06-23T09:30:00Z", market_open: false },
  { symbol: "^DJI", name: "Dow Jones", category: "indices_us", price: 43128.40, change_pct: 0.67, currency: "USD", sparkline: makeSparkline(42841, 28.7), last_updated: "2026-06-23T09:30:00Z", market_open: false },
  { symbol: "^RUT", name: "Russell 2000", category: "indices_us", price: 2184.75, change_pct: 0.94, currency: "USD", sparkline: makeSparkline(2164, 2.1), last_updated: "2026-06-23T09:30:00Z", market_open: false },
  // Asia
  { symbol: "^N225", name: "Nikkei 225", category: "indices_asia", price: 38420.50, change_pct: -0.45, currency: "JPY", sparkline: makeSparkline(38595, -17.5), last_updated: "2026-06-23T06:00:00Z", market_open: false },
  { symbol: "^HSI", name: "Hang Seng", category: "indices_asia", price: 23145.80, change_pct: 0.82, currency: "HKD", sparkline: makeSparkline(22957, 18.9), last_updated: "2026-06-23T08:00:00Z", market_open: false },
  { symbol: "000001.SS", name: "Shanghai Composite", category: "indices_asia", price: 3421.60, change_pct: 0.23, currency: "CNY", sparkline: makeSparkline(3413, 0.8), last_updated: "2026-06-23T07:30:00Z", market_open: false },
  { symbol: "^NSEI", name: "Nifty 50", category: "indices_asia", price: 24856.30, change_pct: 0.61, currency: "INR", sparkline: makeSparkline(24704, 15.2), last_updated: "2026-06-23T09:00:00Z", market_open: false },
  // Cripto
  { symbol: "BTC-USD", name: "Bitcoin", category: "crypto", price: 107234.50, change_pct: 2.14, currency: "USD", sparkline: makeSparkline(104980, 225.4), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "ETH-USD", name: "Ethereum", category: "crypto", price: 3842.60, change_pct: 1.87, currency: "USD", sparkline: makeSparkline(3771, 7.2), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "BNB-USD", name: "BNB", category: "crypto", price: 712.40, change_pct: 0.93, currency: "USD", sparkline: makeSparkline(705, 0.7), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "SOL-USD", name: "Solana", category: "crypto", price: 186.35, change_pct: 3.21, currency: "USD", sparkline: makeSparkline(180, 0.6), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  // Divisas
  { symbol: "EURUSD=X", name: "EUR/USD", category: "fx", price: 1.1342, change_pct: 0.18, currency: "USD", sparkline: makeSparkline(1.1322, 0.001), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "EURGBP=X", name: "EUR/GBP", category: "fx", price: 0.8423, change_pct: -0.09, currency: "GBP", sparkline: makeSparkline(0.8431, -0.0001), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "EURJPY=X", name: "EUR/JPY", category: "fx", price: 163.48, change_pct: 0.32, currency: "JPY", sparkline: makeSparkline(162.96, 0.052), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "GBPUSD=X", name: "GBP/USD", category: "fx", price: 1.3467, change_pct: 0.27, currency: "USD", sparkline: makeSparkline(1.3431, 0.0036), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "JPY=X", name: "USD/JPY", category: "fx", price: 144.12, change_pct: -0.14, currency: "JPY", sparkline: makeSparkline(144.32, -0.02), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "CHF=X", name: "USD/CHF", category: "fx", price: 0.8934, change_pct: -0.21, currency: "CHF", sparkline: makeSparkline(0.8953, -0.0002), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  // Bonos 10Y
  { symbol: "^TNX", name: "Treasury EEUU 10Y", category: "bonds", price: 4.32, change_pct: -0.46, currency: "USD", sparkline: makeSparkline(4.34, -0.002), last_updated: "2026-06-23T09:30:00Z", market_open: false },
  { symbol: "^TMBMKDE-10Y", name: "Bund Alemania 10Y", category: "bonds", price: 2.56, change_pct: -0.78, currency: "EUR", sparkline: makeSparkline(2.58, -0.002), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^TMBMKES-10Y", name: "Bono España 10Y", category: "bonds", price: 3.12, change_pct: -0.63, currency: "EUR", sparkline: makeSparkline(3.14, -0.002), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^TMBMKGB-10Y", name: "Gilt UK 10Y", category: "bonds", price: 4.68, change_pct: -0.21, currency: "GBP", sparkline: makeSparkline(4.69, -0.001), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "^TMBMKIT-10Y", name: "BTP Italia 10Y", category: "bonds", price: 3.87, change_pct: -0.51, currency: "EUR", sparkline: makeSparkline(3.89, -0.002), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  // Materias primas
  { symbol: "GC=F", name: "Oro", category: "commodities", price: 3324.80, change_pct: 0.54, currency: "USD", sparkline: makeSparkline(3307, 1.8), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "SI=F", name: "Plata", category: "commodities", price: 36.42, change_pct: 0.88, currency: "USD", sparkline: makeSparkline(36.10, 0.032), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "BZ=F", name: "Petróleo Brent", category: "commodities", price: 84.32, change_pct: -0.71, currency: "USD", sparkline: makeSparkline(84.92, -0.06), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "CL=F", name: "Petróleo WTI", category: "commodities", price: 81.15, change_pct: -0.83, currency: "USD", sparkline: makeSparkline(81.83, -0.068), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "NG=F", name: "Gas Natural", category: "commodities", price: 2.847, change_pct: 1.43, currency: "USD", sparkline: makeSparkline(2.807, 0.004), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  { symbol: "HG=F", name: "Cobre", category: "commodities", price: 4.732, change_pct: 0.66, currency: "USD", sparkline: makeSparkline(4.701, 0.0031), last_updated: "2026-06-23T09:30:00Z", market_open: true },
  // Volatilidad
  { symbol: "^VIX", name: "VIX", category: "volatility", price: 14.82, change_pct: -3.44, currency: "USD", sparkline: makeSparkline(15.35, -0.053), last_updated: "2026-06-23T09:30:00Z", market_open: false },
];
```

- [ ] **Step 4: Añadir case en getMockResponse**

Dentro de la función `getMockResponse` en `mock-data.ts`, añadir antes del `default`:

```typescript
case path.startsWith("/api/markets/quotes"):
  const catParam = path.includes("?category=")
    ? path.split("?category=")[1]
    : null;
  const quotes = catParam
    ? mockMarketQuotes.filter((q) => q.category === catParam)
    : mockMarketQuotes;
  return quotes as unknown as T;
```

**Nota:** el switch de `getMockResponse` usa `path` como expresión. Si el switch actual usa `path` directamente, añadir esta case. Si usa un patrón diferente (if/else), adaptar al patrón existente del archivo.

- [ ] **Step 5: Verificar TypeScript**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: 0 errores

- [ ] **Step 6: Commit**

```bash
git add apps/desktop/src/lib/types/index.ts apps/desktop/src/lib/api/markets.ts apps/desktop/src/lib/api/mock-data.ts
git commit -m "feat(markets): add MarketQuote type, API client and mock data"
```

---

## Task 4: Frontend — Hook useMarkets

**Files:**
- Create: `apps/desktop/src/lib/hooks/useMarkets.ts`

**Interfaces:**
- Consumes: `getQuotes` de `markets.ts` · `MarketQuote` de types
- Produces: `useMarkets(category?)` → `{ quotes, loading, error, lastUpdated, secondsSinceUpdate }`

- [ ] **Step 1: Crear useMarkets.ts**

```typescript
// apps/desktop/src/lib/hooks/useMarkets.ts
import { useCallback, useEffect, useRef, useState } from "react";
import { getQuotes } from "@/lib/api/markets";
import type { MarketQuote } from "@/lib/types";

function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback);
  useEffect(() => { savedCallback.current = callback; }, [callback]);
  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}

export function useMarkets(category?: string) {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const [paused, setPaused] = useState(false);

  const load = useCallback(async () => {
    if (paused) return;
    try {
      const data = await getQuotes(category);
      setQuotes(data);
      setLastUpdated(new Date());
      setSecondsSinceUpdate(0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
    } finally {
      setLoading(false);
    }
  }, [category, paused]);

  // Initial load
  useEffect(() => { load(); }, [load]);

  // Polling every 5s
  useInterval(load, 5000);

  // Tick secondsSinceUpdate every second
  useInterval(() => {
    if (lastUpdated) {
      setSecondsSinceUpdate(Math.floor((Date.now() - lastUpdated.getTime()) / 1000));
    }
  }, 1000);

  // Pause when tab is hidden
  useEffect(() => {
    const handleVisibility = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  return { quotes, loading, error, lastUpdated, secondsSinceUpdate };
}
```

- [ ] **Step 2: Verificar TypeScript**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: 0 errores

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/lib/hooks/useMarkets.ts
git commit -m "feat(markets): add useMarkets hook with 5s polling and visibility pause"
```

---

## Task 5: Frontend — Componentes UI

**Files:**
- Create: `apps/desktop/src/features/markets/components/LiveIndicator.tsx`
- Create: `apps/desktop/src/features/markets/components/MiniSparkline.tsx`
- Create: `apps/desktop/src/features/markets/components/QuoteRow.tsx`
- Create: `apps/desktop/src/features/markets/components/CategoryTabs.tsx`

**Interfaces:**
- Consumes: `MarketQuote`, `MarketCategory` de types
- Produces: 4 componentes listos para componer en MarketsPage

- [ ] **Step 1: Crear LiveIndicator.tsx**

```tsx
// apps/desktop/src/features/markets/components/LiveIndicator.tsx
interface Props {
  secondsSinceUpdate: number;
}

export default function LiveIndicator({ secondsSinceUpdate }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="inline-block w-1.5 h-1.5 rounded-full bg-accent-teal"
        style={{ animation: "live-pulse 2s ease-in-out infinite" }}
      />
      <span className="text-caption text-stone">
        En vivo · Actualizado hace {secondsSinceUpdate}s
      </span>
    </div>
  );
}
```

Añadir keyframe en el CSS global (`apps/desktop/src/index.css` o equivalente — verificar cuál existe):

```css
@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

@keyframes flash-up {
  0%   { background-color: rgba(0, 168, 126, 0.15); }
  100% { background-color: transparent; }
}

@keyframes flash-down {
  0%   { background-color: rgba(226, 59, 74, 0.15); }
  100% { background-color: transparent; }
}
```

- [ ] **Step 2: Crear MiniSparkline.tsx**

```tsx
// apps/desktop/src/features/markets/components/MiniSparkline.tsx
import { Line, LineChart, ResponsiveContainer } from "recharts";

interface Props {
  data: number[];
  positive: boolean;
}

export default function MiniSparkline({ data, positive }: Props) {
  if (!data.length) {
    return <div className="w-[60px] h-6 bg-surface-elevated rounded" />;
  }

  const color = positive ? "#00a87e" : "#e23b4a";
  const chartData = data.map((v) => ({ v }));

  return (
    <ResponsiveContainer width={60} height={24}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          dot={false}
          strokeWidth={1.5}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 3: Crear QuoteRow.tsx**

```tsx
// apps/desktop/src/features/markets/components/QuoteRow.tsx
import { useEffect, useRef, useState } from "react";
import type { MarketQuote } from "@/lib/types";
import MiniSparkline from "./MiniSparkline";

interface Props {
  quote: MarketQuote;
}

function formatPrice(price: number, currency: string): string {
  const decimals = price < 10 ? 4 : price < 1000 ? 2 : 2;
  return price.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function QuoteRow({ quote }: Props) {
  const prevPrice = useRef<number | null>(null);
  const [flashClass, setFlashClass] = useState("");

  useEffect(() => {
    if (
      prevPrice.current !== null &&
      quote.price !== null &&
      quote.price !== prevPrice.current
    ) {
      const cls = quote.price > prevPrice.current ? "flash-up" : "flash-down";
      setFlashClass(cls);
      const t = setTimeout(() => setFlashClass(""), 400);
      return () => clearTimeout(t);
    }
    prevPrice.current = quote.price ?? null;
  }, [quote.price]);

  const positive = (quote.change_pct ?? 0) >= 0;

  return (
    <div
      className={`flex items-center gap-4 px-6 py-3 ${flashClass}`}
      style={{ animation: flashClass ? `${flashClass} 300ms ease-out forwards` : undefined }}
    >
      <div className="flex-1 min-w-0">
        <p className="text-body-sm text-on-dark truncate">{quote.name}</p>
        <p className="text-caption text-stone">{quote.symbol}</p>
      </div>

      <MiniSparkline data={quote.sparkline} positive={positive} />

      <div className="text-right min-w-[100px]">
        {quote.price !== null ? (
          <p className="text-body-sm font-semibold text-on-dark tabular-nums">
            {formatPrice(quote.price, quote.currency)}
          </p>
        ) : (
          <p className="text-body-sm text-stone">—</p>
        )}
        <p className="text-caption text-stone">{quote.currency}</p>
      </div>

      <div className="min-w-[72px] text-right">
        {quote.change_pct !== null ? (
          <span
            className={`inline-flex items-center text-caption rounded-full px-[10px] py-[3px] ${
              positive
                ? "bg-accent-teal/15 text-accent-teal"
                : "bg-accent-danger/15 text-accent-danger"
            }`}
          >
            {positive ? "▲" : "▼"} {Math.abs(quote.change_pct).toFixed(2)}%
          </span>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Crear CategoryTabs.tsx**

```tsx
// apps/desktop/src/features/markets/components/CategoryTabs.tsx
import type { MarketCategory } from "@/lib/types";

const TABS: Array<{ value: MarketCategory | "all"; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "indices_eu", label: "Europa" },
  { value: "indices_us", label: "EEUU" },
  { value: "indices_asia", label: "Asia" },
  { value: "crypto", label: "Cripto" },
  { value: "fx", label: "Divisas" },
  { value: "bonds", label: "Bonos" },
  { value: "commodities", label: "Mat. Primas" },
  { value: "volatility", label: "Volatilidad" },
];

interface Props {
  active: MarketCategory | "all";
  onChange: (cat: MarketCategory | "all") => void;
}

export default function CategoryTabs({ active, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {TABS.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`text-button-sm rounded-full px-[14px] py-[6px] h-8 transition-colors duration-150 ${
            active === tab.value
              ? "bg-primary text-on-primary"
              : "bg-surface-elevated text-stone border border-hairline-dark hover:text-on-dark"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Verificar TypeScript**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: 0 errores

- [ ] **Step 6: Commit**

```bash
git add apps/desktop/src/features/markets/components/
git commit -m "feat(markets): add LiveIndicator, MiniSparkline, QuoteRow and CategoryTabs components"
```

---

## Task 6: Frontend — MarketsPage + UX Snapshots

**Files:**
- Replace: `apps/desktop/src/features/markets/MarketsPage.tsx`
- Modify: `tools/ux-snapshot/snapshot-routes.ts`

**Interfaces:**
- Consumes: `useMarkets` · `LiveIndicator` · `CategoryTabs` · `QuoteRow`
- Produces: pantalla completa `/markets`

- [ ] **Step 1: Verificar que la ruta /markets existe en el router**

Buscar en `apps/desktop/src/App.tsx` (o el archivo de rutas del proyecto):

```bash
grep -r "markets\|MarketsPage" apps/desktop/src/App.tsx
```

Si no existe la ruta, añadirla siguiendo el patrón de las demás rutas de la app.

- [ ] **Step 2: Implementar MarketsPage.tsx**

```tsx
// apps/desktop/src/features/markets/MarketsPage.tsx
import { useState } from "react";
import type { MarketCategory } from "@/lib/types";
import { useMarkets } from "@/lib/hooks/useMarkets";
import CategoryTabs from "./components/CategoryTabs";
import LiveIndicator from "./components/LiveIndicator";
import QuoteRow from "./components/QuoteRow";

const CATEGORY_LABELS: Record<string, string> = {
  indices_eu: "EUROPA",
  indices_us: "ESTADOS UNIDOS",
  indices_asia: "ASIA",
  crypto: "CRIPTOMONEDAS",
  fx: "DIVISAS",
  bonds: "BONOS 10 AÑOS",
  commodities: "MATERIAS PRIMAS",
  volatility: "VOLATILIDAD",
};

const CATEGORY_ORDER = [
  "indices_eu",
  "indices_us",
  "indices_asia",
  "crypto",
  "fx",
  "bonds",
  "commodities",
  "volatility",
] as const;

export default function MarketsPage() {
  const [activeCategory, setActiveCategory] = useState<MarketCategory | "all">("all");
  const { quotes, loading, error, secondsSinceUpdate } = useMarkets(
    activeCategory === "all" ? undefined : activeCategory
  );

  return (
    <div className="p-xxxl space-y-xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-heading-lg text-on-dark">Mercados</h1>
        <LiveIndicator secondsSinceUpdate={secondsSinceUpdate} />
      </div>

      {/* Category tabs */}
      <CategoryTabs active={activeCategory} onChange={setActiveCategory} />

      {/* Content */}
      {loading && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated divide-y divide-divider-soft">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-6 py-3">
              <div className="flex-1 space-y-1">
                <div className="h-3.5 w-32 rounded bg-surface-elevated opacity-40" style={{ animation: "pulse 1.2s ease-in-out infinite" }} />
                <div className="h-3 w-16 rounded bg-surface-elevated opacity-40" style={{ animation: "pulse 1.2s ease-in-out infinite" }} />
              </div>
              <div className="w-[60px] h-6 rounded bg-surface-elevated opacity-40" />
              <div className="h-4 w-20 rounded bg-surface-elevated opacity-40" />
              <div className="h-5 w-16 rounded-full bg-surface-elevated opacity-40" />
            </div>
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="rounded-lg border-l-[3px] border-l-accent-danger border border-hairline-dark bg-surface-elevated p-xl">
          <p className="text-body-md-bold text-on-dark">Error al cargar datos de mercado</p>
          <p className="text-body-sm text-on-dark-mute mt-1">{error}</p>
        </div>
      )}

      {!loading && !error && activeCategory === "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          {CATEGORY_ORDER.map((cat, catIdx) => {
            const catQuotes = quotes.filter((q) => q.category === cat);
            if (!catQuotes.length) return null;
            return (
              <div key={cat}>
                {catIdx > 0 && <div className="border-t border-divider-soft" />}
                <div className="px-6 pt-4 pb-1">
                  <span className="text-caption text-stone uppercase tracking-wider">
                    {CATEGORY_LABELS[cat]}
                  </span>
                </div>
                <div className="divide-y divide-divider-soft">
                  {catQuotes.map((q) => (
                    <QuoteRow key={q.symbol} quote={q} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && activeCategory !== "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden divide-y divide-divider-soft">
          {quotes.map((q) => (
            <QuoteRow key={q.symbol} quote={q} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Actualizar snapshot-routes.ts**

Añadir antes del cierre del array `snapshotRoutes`:

```typescript
  {
    path: "/markets",
    filename: "markets.png",
    screenName: "Markets",
    state: "mock_data",
    description: "Market Watch con 36 activos en 8 categorías, tab Todos",
    requiresInteraction: false,
  },
  {
    path: "/markets",
    filename: "markets-europa.png",
    screenName: "Markets Europa",
    state: "mock_data",
    description: "Market Watch filtrado por categoría Europa (6 índices)",
    requiresInteraction: false,
  },
```

- [ ] **Step 4: Verificar TypeScript**

```bash
cd apps/desktop && npx tsc --noEmit
```

Expected: 0 errores

- [ ] **Step 5: Verificar que la app arranca**

```bash
cd apps/desktop && npm run dev
```

Navegar a `http://localhost:1420` (o el puerto configurado), ir a la sección Mercados y verificar:
- Los 36 activos se muestran agrupados en la tab "Todos"
- Los tabs de categoría filtran correctamente
- El indicador "En vivo" pulsa en verde
- El contador "Actualizado hace Xs" incrementa cada segundo
- Las sparklines se muestran (verdes/rojas según change_pct)

- [ ] **Step 6: Commit**

```bash
git add apps/desktop/src/features/markets/MarketsPage.tsx tools/ux-snapshot/snapshot-routes.ts
git commit -m "feat(markets): implement MarketsPage with live polling, tabs and flash animations"
```

---

## Deuda técnica registrada

Al completar la implementación, añadir en `docs/02_ROADMAP.md` bajo la sección de Fase 4:

| # | Deuda | Impacto |
|---|-------|---------|
| TD-07 | Tickers de bonos europeos 10Y (`^TMBMK*`) pueden no estar en yfinance — fallback a `price: null` con "—" en UI | Bajo |
| TD-08 | Caché en memoria se pierde al reiniciar el servidor — primer request tras restart hace fetch síncrono | Bajo |
| TD-09 | Sin histórico de más de 1 día — sparkline solo muestra datos intraday del día actual | Medio |
