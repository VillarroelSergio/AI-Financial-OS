# EOD Market Data Simplification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify market data to end-of-day closing prices fetched once at app startup, removing the manual refresh button and all "live/fresh/delayed" UI states.

**Architecture:** A new `EodMarketService` calls `ProviderRouter` with `eod_only=True` on startup (background thread), using only Stooq (TTL 24h). The frontend shows a static "Cierre DD/MM/YYYY" badge. The existing ConsensusEngine and multi-provider infrastructure remain intact for Fase 6.

**Tech Stack:** Python 3.11, FastAPI, DuckDB (cache), React 18, TypeScript, Tailwind CSS, shadcn/ui.

## Global Constraints

- No provider de pago. Stooq y Yahoo son gratuitos sin API key.
- `freshness_status` solo puede ser `eod` o `stale` en modo EOD — nunca `live`, `fresh`, `delayed`.
- UI en español. Dark Premium theme. No añadir nuevas dependencias npm o pip.
- Todos los tests con `pytest`. Correr desde `backend/`: `python -m pytest app/tests/ -v`.

---

## File Map

| Acción | Archivo |
|--------|---------|
| CREAR | `backend/app/modules/investments/market_data/eod_service.py` |
| MODIFICAR | `backend/app/modules/investments/market_data/router.py` |
| MODIFICAR | `backend/app/main.py` |
| CREAR | `backend/app/tests/test_eod_service.py` |
| MODIFICAR | `apps/desktop/src/lib/hooks/useMarkets.ts` |
| CREAR | `apps/desktop/src/features/markets/components/EodBadge.tsx` |
| MODIFICAR | `apps/desktop/src/features/markets/MarketsPage.tsx` |

---

### Task 1: `EodMarketService` con tests

**Files:**
- Create: `backend/app/modules/investments/market_data/eod_service.py`
- Create: `backend/app/tests/test_eod_service.py`

**Interfaces:**
- Produces: `EodMarketService.ensure_today() -> None`, `get_eod_service() -> EodMarketService`
- Consumes: `get_router() -> ProviderRouter` (ya existe en `router.py`)

- [ ] **Step 1: Escribir los tests que fallarán**

Crear `backend/app/tests/test_eod_service.py`:

```python
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
```

- [ ] **Step 2: Verificar que fallan**

```
cd backend
python -m pytest app/tests/test_eod_service.py -v
```

Esperado: `ERROR` o `ImportError` (el módulo no existe).

- [ ] **Step 3: Implementar `EodMarketService`**

Crear `backend/app/modules/investments/market_data/eod_service.py`:

```python
"""EodMarketService — fetches EOD closing prices once per calendar day."""
from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timezone
from typing import Optional

from app.modules.investments.market_data.cache import MarketCache
from app.modules.investments.market_data.router import get_router

logger = logging.getLogger(__name__)

_ensure_lock = threading.Lock()


class EodMarketService:
    def __init__(self) -> None:
        self._cache = MarketCache()

    def ensure_today(self) -> None:
        """Fetch EOD data for all catalog assets not yet cached for today.

        Acquires a non-blocking lock so concurrent calls at startup are no-ops.
        Safe to call from a daemon thread.
        """
        if not _ensure_lock.acquire(blocking=False):
            logger.debug("EodMarketService.ensure_today: already running, skipping")
            return
        try:
            router = get_router()
            today = datetime.now(timezone.utc).date()
            for asset in router.catalog:
                cached = self._cache.get_quote(asset.internal_symbol)
                if cached and self._is_today(cached, today):
                    continue
                try:
                    router.get_quote(asset, force_refresh=True, eod_only=True)
                except Exception as exc:
                    logger.warning(
                        "EodMarketService: failed for %s: %s",
                        asset.internal_symbol, exc,
                    )
        finally:
            _ensure_lock.release()

    def _is_today(self, row: dict, today: date) -> bool:
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
        return cached_at.date() == today


_service: Optional[EodMarketService] = None
_service_lock = threading.Lock()


def get_eod_service() -> EodMarketService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = EodMarketService()
    return _service
```

- [ ] **Step 4: Verificar que los tests pasan**

```
cd backend
python -m pytest app/tests/test_eod_service.py -v
```

Esperado: 5 tests en verde (`PASSED`).

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/investments/market_data/eod_service.py \
        backend/app/tests/test_eod_service.py
git commit -m "feat(market): add EodMarketService — once-per-day EOD fetch"
```

---

### Task 2: Añadir `eod_only` al `ProviderRouter`

**Files:**
- Modify: `backend/app/modules/investments/market_data/router.py`

**Interfaces:**
- Modifica: `ProviderRouter.get_quote(asset, *, force_refresh=False, eod_only=False)`
- Cuando `eod_only=True`: TTL es 86400s (24h) y el fetch_pool se filtra a solo `stooq`.

- [ ] **Step 1: Añadir test de integración al fichero de tests existente**

Añadir al final de `backend/app/tests/test_eod_service.py`:

```python
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
```

- [ ] **Step 2: Verificar que el test falla**

```
cd backend
python -m pytest app/tests/test_eod_service.py::test_provider_router_eod_only_filters_to_stooq -v
```

Esperado: `TypeError` (get_quote no acepta `eod_only`).

- [ ] **Step 3: Modificar `ProviderRouter.get_quote`**

En `backend/app/modules/investments/market_data/router.py`, localizar la firma de `get_quote` (línea ~126) y aplicar los siguientes cambios:

**Cambio 1 — Firma:** reemplazar
```python
    def get_quote(
        self, asset: AssetConfig, *, force_refresh: bool = False
    ) -> MarketQuoteInternal:
        ttl = _TTL.get(asset.asset_type, 900)
```
por
```python
    def get_quote(
        self, asset: AssetConfig, *, force_refresh: bool = False, eod_only: bool = False
    ) -> MarketQuoteInternal:
        ttl = 86400 if eod_only else _TTL.get(asset.asset_type, 900)
```

**Cambio 2 — Filtrar fetch_pool a Stooq cuando eod_only:** añadir justo antes del comentario `# 3. Parallel fetch` (después de que se construye `fetch_pool`):

```python
        if eod_only:
            fetch_pool = [(p, prov, sym) for p, prov, sym in fetch_pool if p == "stooq"]
```

- [ ] **Step 4: Verificar que todos los tests pasan**

```
cd backend
python -m pytest app/tests/test_eod_service.py -v
```

Esperado: 6 tests en verde.

- [ ] **Step 5: Verificar que los tests de market_data existentes siguen verdes**

```
cd backend
python -m pytest app/tests/test_market_data.py app/tests/test_market_data_service.py app/tests/test_market_refresh_control.py -v
```

Esperado: todos en verde.

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/investments/market_data/router.py \
        backend/app/tests/test_eod_service.py
git commit -m "feat(market): add eod_only mode to ProviderRouter — 24h TTL, Stooq-only pool"
```

---

### Task 3: Integrar `EodMarketService` en el startup de FastAPI

**Files:**
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `get_eod_service() -> EodMarketService` de `eod_service.py`
- El thread es daemon=True — no bloquea el shutdown de la app.

- [ ] **Step 1: Modificar el lifespan de `main.py`**

En `backend/app/main.py`, reemplazar el bloque `@asynccontextmanager async def lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_tables()
    db = SessionLocal()
    try:
        from app.seeds.categories import seed_categories
        from app.seeds.settings import seed_settings
        seed_categories(db)
        seed_settings(db)
    finally:
        db.close()

    import threading
    from app.modules.investments.market_data.eod_service import get_eod_service
    threading.Thread(target=get_eod_service().ensure_today, daemon=True, name="eod-market-fetch").start()

    yield
```

- [ ] **Step 2: Verificar que el servidor arranca sin errores**

```
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Esperado: arranca sin errores. En los logs debe aparecer algo como `EodMarketService` o las llamadas a Stooq. Pulsar Ctrl+C para parar.

- [ ] **Step 3: Verificar que el test de health sigue verde**

```
cd backend
python -m pytest app/tests/test_health.py -v
```

Esperado: verde.

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(market): trigger EOD fetch in background on app startup"
```

---

### Task 4: Frontend — eliminar refresh, añadir `EodBadge`

**Files:**
- Create: `apps/desktop/src/features/markets/components/EodBadge.tsx`
- Modify: `apps/desktop/src/features/markets/MarketsPage.tsx`
- Modify: `apps/desktop/src/lib/hooks/useMarkets.ts`

**Interfaces:**
- `EodBadge` recibe `lastUpdated: string | null` (ISO datetime de `MarketQuote.last_updated`) e `isStale?: boolean`.
- `useMarkets` ya no expone `refresh`, `refreshing`, `secondsSinceUpdate`.

- [ ] **Step 1: Crear `EodBadge.tsx`**

Crear `apps/desktop/src/features/markets/components/EodBadge.tsx`:

```tsx
interface Props {
  lastUpdated: string | null;
  isStale?: boolean;
}

function formatCloseDate(isoStr: string | null): string {
  if (!isoStr) return "Sin datos";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return "Sin datos";
  }
}

export default function EodBadge({ lastUpdated, isStale = false }: Props) {
  const dateStr = formatCloseDate(lastUpdated);
  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-hairline-dark bg-surface-elevated"
      role="status"
      aria-label={isStale ? "Datos desactualizados" : `Datos de cierre del ${dateStr}`}
    >
      <span
        className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${
          isStale ? "bg-accent-warning" : "bg-stone"
        }`}
        aria-hidden="true"
      />
      <span
        className={`text-caption font-medium ${
          isStale ? "text-accent-warning" : "text-stone"
        }`}
      >
        {isStale ? "Datos desactualizados" : `Cierre ${dateStr}`}
      </span>
    </div>
  );
}
```

- [ ] **Step 2: Simplificar `useMarkets.ts`**

Reemplazar el contenido completo de `apps/desktop/src/lib/hooks/useMarkets.ts`:

```ts
import { useCallback, useEffect, useState } from "react";
import { getQuotes } from "@/lib/api/markets";
import type { MarketQuote } from "@/lib/types";

export function useMarkets(): {
  quotes: MarketQuote[];
  loading: boolean;
  error: string | null;
} {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getQuotes();
      setQuotes(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { quotes, loading, error };
}
```

- [ ] **Step 3: Actualizar `MarketsPage.tsx`**

Reemplazar el contenido completo de `apps/desktop/src/features/markets/MarketsPage.tsx`:

```tsx
import { useMemo, useState } from "react";
import type { MarketCategory, MarketQuote } from "@/lib/types";
import { useMarkets } from "@/lib/hooks/useMarkets";
import CategoryTabs from "./components/CategoryTabs";
import EodBadge from "./components/EodBadge";
import QuoteRow from "./components/QuoteRow";

const CATEGORY_ORDER: Array<{ key: MarketCategory; label: string }> = [
  { key: "indices_eu", label: "EUROPA" },
  { key: "indices_us", label: "ESTADOS UNIDOS" },
  { key: "indices_asia", label: "ASIA" },
  { key: "crypto", label: "CRIPTOMONEDAS" },
  { key: "fx", label: "DIVISAS" },
  { key: "bonds", label: "BONOS 10Y" },
  { key: "commodities", label: "MATERIAS PRIMAS" },
  { key: "volatility", label: "VOLATILIDAD" },
];

function TableHeader() {
  return (
    <div className="grid grid-cols-[1fr_80px_120px_100px] items-center gap-4 px-6 py-2 border-b border-divider-soft">
      <span className="text-caption text-mute uppercase tracking-widest">Activo</span>
      <span className="text-caption text-mute uppercase tracking-widest text-center">Tendencia</span>
      <span className="text-caption text-mute uppercase tracking-widest text-right">Precio cierre</span>
      <span className="text-caption text-mute uppercase tracking-widest text-right">Variación</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
      <TableHeader />
      <div className="divide-y divide-divider-soft">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-[1fr_80px_120px_100px] items-center gap-4 px-6 py-3 animate-pulse">
            <div className="space-y-1.5">
              <div className="h-3.5 w-28 rounded bg-stone/20" />
              <div className="h-3 w-14 rounded bg-stone/20" />
            </div>
            <div className="h-6 w-[60px] rounded bg-stone/20 mx-auto" />
            <div className="space-y-1.5 items-end flex flex-col">
              <div className="h-3.5 w-20 rounded bg-stone/20" />
              <div className="h-3 w-10 rounded bg-stone/20" />
            </div>
            <div className="flex flex-col items-end gap-1">
              <div className="h-5 w-16 rounded-full bg-stone/20" />
              <div className="h-3 w-14 rounded bg-stone/20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-6 flex items-start gap-4">
      <div className="w-8 h-8 rounded-full bg-accent-danger/15 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-accent-danger text-sm font-bold">!</span>
      </div>
      <div>
        <p className="text-body-sm font-medium text-on-dark">Error al cargar datos de mercado</p>
        <p className="text-caption text-stone mt-1">{message}</p>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated p-12 flex flex-col items-center text-center gap-3">
      <div className="w-10 h-10 rounded-full bg-surface-card flex items-center justify-center">
        <span className="text-stone text-lg">—</span>
      </div>
      <p className="text-body-sm text-stone">
        Los datos de cierre se cargarán al arrancar la aplicación.
      </p>
    </div>
  );
}

export default function MarketsPage() {
  const initialCategory = new URLSearchParams(window.location.search).get("category") as MarketCategory | null;
  const [activeCategory, setActiveCategory] = useState<MarketCategory | "all">(initialCategory ?? "all");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const { quotes, loading, error } = useMarkets();

  const visibleQuotes = activeCategory === "all"
    ? quotes
    : quotes.filter((q) => q.category === activeCategory);

  const handleSelectAsset = (symbol: string) => {
    setSelectedSymbol((prev) => (prev === symbol ? null : symbol));
  };

  const hasData = !loading && !error && visibleQuotes.length > 0;
  const isEmpty = !loading && !error && visibleQuotes.length === 0;

  // Tomar la fecha de cierre del quote más reciente para el badge
  const latestUpdated = useMemo(() => {
    if (!quotes.length) return null;
    return quotes.reduce((latest, q) =>
      !latest || q.last_updated > latest ? q.last_updated : latest,
      null as string | null,
    );
  }, [quotes]);

  const anyStale = quotes.some((q) => q.is_stale);

  return (
    <div className="p-8 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-heading-md text-on-dark">Mercados</h1>
          <p className="text-caption text-stone mt-1">
            Precios de cierre diario de índices, divisas, cripto, bonos y materias primas.
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 pt-1">
          <EodBadge lastUpdated={latestUpdated} isStale={anyStale} />
        </div>
      </div>

      {/* Category tabs */}
      <CategoryTabs activeCategory={activeCategory} onSelect={setActiveCategory} />

      {/* States */}
      {loading && <LoadingSkeleton />}
      {error && !loading && <ErrorState message={error} />}
      {isEmpty && <EmptyState />}

      {/* All categories grouped */}
      {hasData && activeCategory === "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          <TableHeader />
          {CATEGORY_ORDER.map((cat, catIdx) => {
            const catQuotes = visibleQuotes.filter((q) => q.category === cat.key);
            if (!catQuotes.length) return null;
            return (
              <div key={cat.key}>
                {catIdx > 0 && <div className="border-t border-hairline-dark" />}
                <div className="px-6 pt-4 pb-2">
                  <span className="text-caption text-mute uppercase tracking-widest font-medium">
                    {cat.label}
                  </span>
                </div>
                <div className="divide-y divide-divider-soft">
                  {catQuotes.map((q) => (
                    <QuoteRow
                      key={q.symbol}
                      quote={q}
                      isSelected={selectedSymbol === q.symbol}
                      onSelect={handleSelectAsset}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Single category flat list */}
      {hasData && activeCategory !== "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          <TableHeader />
          <div className="divide-y divide-divider-soft">
            {visibleQuotes.map((q) => (
              <QuoteRow
                key={q.symbol}
                quote={q}
                isSelected={selectedSymbol === q.symbol}
                onSelect={handleSelectAsset}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Verificar que TypeScript compila sin errores**

```
cd apps/desktop
npx tsc --noEmit
```

Esperado: sin errores (o solo errores preexistentes no relacionados).

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/features/markets/components/EodBadge.tsx \
        apps/desktop/src/features/markets/MarketsPage.tsx \
        apps/desktop/src/lib/hooks/useMarkets.ts
git commit -m "feat(market-ui): replace live refresh with EOD badge, remove refresh button"
```

---

### Task 5: Actualizar el roadmap

**Files:**
- Modify: `docs/02_ROADMAP.md`

- [ ] **Step 1: Añadir Fase 4.7 al roadmap**

En `docs/02_ROADMAP.md`, en la tabla de estado, añadir la fila nueva después de la Fase 4.6:

```markdown
| 4.7 | EOD Market Data | ✅ Completa | rama actual |
```

Y añadir al final del bloque de Fase 4.6 (antes de Fase 5) una sección nueva:

```markdown
## Fase 4.7 — EOD Market Data ✅

### Objetivo

Simplificar el modelo de datos de mercado a cierre diario (EOD). Una única llamada al arranque, sin refresh manual, sin estados "live".

### Incluye

- `EodMarketService` — fetch secuencial Stooq al arrancar (background thread).
- `eod_only` mode en `ProviderRouter` — TTL 24h, pool filtrado a Stooq.
- `EodBadge` — sustituye `LiveIndicator`, muestra "Cierre DD/MM/YYYY".
- Eliminación del botón "Actualizar" en Market Watch.
- 6 tests unitarios cubriendo cache hit, cache miss, fallo, concurrencia y filtrado de providers.
```

- [ ] **Step 2: Commit**

```bash
git add docs/02_ROADMAP.md
git commit -m "docs: add Fase 4.7 EOD Market Data to roadmap"
```
