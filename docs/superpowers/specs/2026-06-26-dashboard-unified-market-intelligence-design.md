# Fase 5.6 — Dashboard Unificado sobre Market Intelligence: Design

## Objetivo

Unificar las pantallas Economy y Markets para que consuman `market_intelligence` como única fuente de verdad, eliminando los módulos legacy `economic_data` y `market_data` (EOD). La ingesta se lanza automáticamente al arrancar la app. Se amplía el impacto personal a 11 comparativos que cruzan datos de mercado con datos personales del usuario.

## Arquitectura

```
App start
  └─ startup_event → IngestOnStartupService (background thread, daemon)
        └─ run_ingestion(priority="critical") → tablas mi_* en DuckDB

Frontend
  EconomyPage  → GET /api/market-intelligence/snapshot/macro     → MI service → DuckDB
               → GET /api/market-intelligence/personal-impact    → MI service → DuckDB + SQLite
  MarketsPage  → GET /api/market-intelligence/snapshot/market    → MI service → DuckDB
               → GET /api/market-intelligence/snapshot/forex     → MI service → DuckDB
               → GET /api/market-intelligence/snapshot/bonds     → MI service → DuckDB
  Ambas        → GET /api/market-intelligence/ingest-status      → estado ingesta
```

## Global Constraints

- Python 3.12+, Pydantic v2, FastAPI, DuckDB singleton `get_duckdb()` — nunca `duckdb.connect()` directo
- API keys desde `app.core.config.settings` via `getattr(settings, env_var, None)` — nunca `os.environ.get()`
- No se rompe ningún endpoint fuera de `/api/economy/*` y `/api/markets/*` (se eliminan explícitamente)
- Frontend: React + TypeScript + shadcn/ui, sin lógica financiera en el cliente
- Los comparativos de impacto personal son 100% deterministas — sin LLM
- Datos MI pueden estar vacíos en primera ejecución — la ingesta resuelve esto automáticamente en startup
- Tests con `pytest`, mocks via `unittest.mock.patch`

---

## Sección 1 — Eliminación de módulos legacy

### Backend — eliminar

| Ruta | Motivo |
|---|---|
| `backend/app/modules/economic_data/` | Sustituido por MI |
| `backend/app/modules/investments/market_data/` | Sustituido por MI |
| `backend/tests/economic_data/` (si existe) | Tests del módulo eliminado |
| `backend/tests/market_data/` (si existe) | Tests del módulo eliminado |

Desregistrar en `main.py`:
```python
# Eliminar estas líneas:
from app.modules.economic_data.routes import router as economic_data_router
from app.modules.investments.market_data.routes import router as market_data_router
app.include_router(economic_data_router, prefix="/api/economy", ...)
app.include_router(market_data_router, prefix="/api/markets", ...)
```

### Frontend — eliminar

| Ruta | Motivo |
|---|---|
| `apps/desktop/src/lib/api/economy.ts` | Sustituido por market-intelligence.ts |
| `apps/desktop/src/lib/api/markets.ts` | Ídem |
| `apps/desktop/src/lib/hooks/useEconomy.ts` | Sustituido por useMarketIntelligence.ts |
| `apps/desktop/src/lib/hooks/useMarkets.ts` | Ídem |
| `apps/desktop/src/features/markets/components/EodBadge.tsx` | Concepto EOD eliminado |

---

## Sección 2 — Ingesta automática al arrancar

### `IngestOnStartupService`

Nuevo servicio en `backend/app/modules/market_intelligence/ingestion/startup.py`:

```python
from threading import Thread
from app.modules.market_intelligence.ingestion.runner import run_ingestion

_status: dict = {"status": "idle", "last_run": None, "count": 0}

def get_ingest_status() -> dict:
    return _status.copy()

def launch_startup_ingest() -> None:
    """Lanza ingesta en background. Llamar una vez en startup."""
    def _run():
        _status["status"] = "running"
        try:
            summary = run_ingestion(priority="critical")
            _status["count"] = summary.total_fetched
            _status["status"] = "done"
        except Exception:
            _status["status"] = "error"
        from datetime import datetime, timezone
        _status["last_run"] = datetime.now(timezone.utc).isoformat()
    Thread(target=_run, daemon=True).start()
```

### Registro en `main.py`

```python
from app.modules.market_intelligence.ingestion.startup import launch_startup_ingest

@app.on_event("startup")
async def on_startup():
    launch_startup_ingest()
```

### Nuevo endpoint `/api/market-intelligence/ingest-status`

En `backend/app/modules/market_intelligence/api/routes.py`:

```python
@router.get("/ingest-status")
def ingest_status():
    from app.modules.market_intelligence.ingestion.startup import get_ingest_status
    return get_ingest_status()
```

Respuesta:
```json
{ "status": "running" | "done" | "idle" | "error", "last_run": "2026-06-26T...", "count": 42 }
```

---

## Sección 3 — Refactor `service.py`: clasificación desde CatalogLoader

Problema actual: `_SPAIN_CATALOG_IDS`, `_EUROZONE_CATALOG_IDS`, etc. son sets hardcodeados que duplican el YAML.

Solución: `get_macro_snapshot()` usa `CatalogLoader` para clasificar por `country`/`region`:

```python
from app.modules.market_intelligence.catalog.loader import CatalogLoader

_catalog = CatalogLoader()

def _region_for(catalog_item_id: str) -> str | None:
    item = _catalog.get_by_id(catalog_item_id)
    if item is None:
        return None
    if item.country in ("ES",):
        return "spain"
    if item.region in ("Eurozone", "EU"):
        return "eurozone"
    if item.country in ("US",):
        return "usa"
    return None
```

Eliminar los 5 sets hardcodeados (`_SPAIN_CATALOG_IDS`, etc.).

---

## Sección 4 — Endpoint de impacto personal

### Nuevo endpoint

```
GET /api/market-intelligence/personal-impact
→ PersonalImpactOut
```

### Schema `PersonalImpactOut`

```python
class ImpactComparative(BaseModel):
    id: str                    # slug único, e.g. "inflation_vs_savings"
    title: str                 # "Inflación vs tu tasa de ahorro"
    description: str           # Explicación en una línea
    market_value: float | None # Valor del indicador de mercado
    market_label: str          # "IPC General: 3.2%"
    personal_value: float | None  # Valor del usuario (puede ser None si no hay datos)
    personal_label: str        # "Tu tasa de ahorro: 8.1%"
    signal: str                # "positive" | "negative" | "neutral" | "warning"
    signal_text: str           # "Estás por encima de la inflación" | etc.
    source_ids: list[str]      # catalog_item_ids usados

class PersonalImpactOut(BaseModel):
    generated_at: str
    comparatives: list[ImpactComparative]
    warnings: list[str] = []
```

### Los 11 comparativos y su lógica de señal

Implementados en `backend/app/modules/market_intelligence/api/impact.py`:

| id | Datos de mercado | Datos personales | Signal positivo |
|---|---|---|---|
| `inflation_vs_savings` | `ipc_general` (value) | tasa ahorro = ingresos netos / gasto mensual | personal > market |
| `rates_vs_liquidity` | `tipo_bce` (value) | meses cubiertos = saldo total / gasto mensual medio | ≥ 3 meses |
| `market_vs_portfolio` | media rentabilidad índices MI | rentabilidad inversiones (portfolio) | personal ≥ market |
| `purchasing_power` | IPC acumulado 12m | — (solo informativo) | IPC < 2.0% |
| `euribor_vs_mortgage` | `euribor_12m` (value) | deuda total en cuentas tipo "mortgage" | euribor < 3.0% |
| `eurusd_vs_intl_spending` | `eur_usd` (rate) | gasto medio mensual en USD (categorías detectadas) | EUR/USD > 1.10 |
| `oil_vs_transport` | `brent_crude` (price) | gasto mensual en categoría "transporte"/"gasolina" | brent < 80 USD |
| `risk_premium_spain` | `bono_spain_10y` - `bund_10y` | — (solo informativo) | spread < 100 bps |
| `real_portfolio_return` | `ipc_general` (value) | rentabilidad real = portfolio_return - ipc | real > 0 |
| `core_cpi_vs_food_spending` | `ipc_subyacente` (value) | gasto alimentación+hogar / gasto total × 100 | personal < subyacente |
| `consumer_confidence_vs_liquidity` | `confianza_consumidor_spain` (value) | meses cubiertos (igual que #2) | meses ≥ 6 si confianza < 90 |

**Lógica de señal general:**

```python
def compute_signal(personal: float | None, threshold: float, higher_is_better: bool) -> str:
    if personal is None:
        return "neutral"
    delta = personal - threshold
    if abs(delta) < threshold * 0.05:
        return "neutral"
    return "positive" if (delta > 0) == higher_is_better else "negative"
```

**Datos personales** se leen desde SQLite vía `repository` de los módulos `accounts`, `transactions`, `investments` existentes. La función `get_personal_impact()` en `service.py` importa estos repositorios directamente.

---

## Sección 5 — Cliente frontend unificado

### `apps/desktop/src/lib/api/market-intelligence.ts`

```typescript
import { api } from "./client";
import type {
  MacroSnapshotMI, MarketSnapshotMI, ForexSnapshotMI,
  BondSnapshotMI, PersonalImpactMI, IngestStatus,
} from "@/lib/types/market-intelligence";

export const getMacroSnapshot = () =>
  api.get<MacroSnapshotMI>("/api/market-intelligence/snapshot/macro");

export const getMarketSnapshot = () =>
  api.get<MarketSnapshotMI>("/api/market-intelligence/snapshot/market");

export const getForexSnapshot = () =>
  api.get<ForexSnapshotMI>("/api/market-intelligence/snapshot/forex");

export const getBondSnapshot = () =>
  api.get<BondSnapshotMI>("/api/market-intelligence/snapshot/bonds");

export const getPersonalImpact = () =>
  api.get<PersonalImpactMI>("/api/market-intelligence/personal-impact");

export const getIngestStatus = () =>
  api.get<IngestStatus>("/api/market-intelligence/ingest-status");
```

### `apps/desktop/src/lib/types/market-intelligence.ts`

```typescript
export interface MacroDataPointMI {
  catalog_item_id: string;
  indicator_id?: string;
  country?: string;
  period?: string;
  value?: number;
  unit?: string;
  provider_id?: string;
  quality_score: number;
}

export interface MacroSnapshotMI {
  spain: MacroDataPointMI[];
  eurozone: MacroDataPointMI[];
  usa: MacroDataPointMI[];
  generated_at: string;
  warnings: string[];
}

export interface QuoteMI {
  catalog_item_id: string;
  symbol?: string;
  asset_type?: string;
  price?: number;
  change_pct?: number;
  currency?: string;
  provider_id?: string;
  quality_score: number;
}

export interface MarketSnapshotMI {
  indices: QuoteMI[];
  crypto: QuoteMI[];
  commodities: Record<string, unknown>[];
  generated_at: string;
  warnings: string[];
}

export interface ForexRateMI {
  catalog_item_id: string;
  base_currency?: string;
  quote_currency?: string;
  rate?: number;
  date?: string;
  provider_id?: string;
  quality_score: number;
}

export interface ForexSnapshotMI {
  rates: ForexRateMI[];
  generated_at: string;
  warnings: string[];
}

export interface BondYieldMI {
  catalog_item_id: string;
  country?: string;
  maturity?: string;
  yield_value?: number;
  date?: string;
  provider_id?: string;
  quality_score: number;
}

export interface BondSnapshotMI {
  yields: BondYieldMI[];
  generated_at: string;
  warnings: string[];
}

export interface ImpactComparative {
  id: string;
  title: string;
  description: string;
  market_value: number | null;
  market_label: string;
  personal_value: number | null;
  personal_label: string;
  signal: "positive" | "negative" | "neutral" | "warning";
  signal_text: string;
  source_ids: string[];
}

export interface PersonalImpactMI {
  generated_at: string;
  comparatives: ImpactComparative[];
  warnings: string[];
}

export interface IngestStatus {
  status: "idle" | "running" | "done" | "error";
  last_run: string | null;
  count: number;
}
```

### `apps/desktop/src/lib/hooks/useMarketIntelligence.ts`

```typescript
import { useEffect, useState, useCallback } from "react";
import {
  getMacroSnapshot, getMarketSnapshot, getForexSnapshot,
  getBondSnapshot, getPersonalImpact, getIngestStatus,
} from "@/lib/api/market-intelligence";
import type {
  MacroSnapshotMI, MarketSnapshotMI, ForexSnapshotMI,
  BondSnapshotMI, PersonalImpactMI, IngestStatus,
} from "@/lib/types/market-intelligence";

export function useEconomyMI() {
  const [macro, setMacro] = useState<MacroSnapshotMI | null>(null);
  const [impact, setImpact] = useState<PersonalImpactMI | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [macroData, impactData] = await Promise.all([
        getMacroSnapshot(), getPersonalImpact(),
      ]);
      setMacro(macroData);
      setImpact(impactData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Poll ingest status until done
    const pollStatus = async () => {
      const status = await getIngestStatus();
      setIngestStatus(status);
      if (status.status === "running") {
        setTimeout(pollStatus, 3000);
      } else {
        load();
      }
    };
    pollStatus();
  }, [load]);

  return { macro, impact, ingestStatus, loading, error };
}

export function useMarketsMI() {
  const [market, setMarket] = useState<MarketSnapshotMI | null>(null);
  const [forex, setForex] = useState<ForexSnapshotMI | null>(null);
  const [bonds, setBonds] = useState<BondSnapshotMI | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      const status = await getIngestStatus();
      setIngestStatus(status);
      if (status.status === "running") {
        setTimeout(pollStatus, 3000);
      } else {
        try {
          const [marketData, forexData, bondsData] = await Promise.all([
            getMarketSnapshot(), getForexSnapshot(), getBondSnapshot(),
          ]);
          setMarket(marketData);
          setForex(forexData);
          setBonds(bondsData);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Error desconocido");
        } finally {
          setLoading(false);
        }
      }
    };
    pollStatus();
  }, []);

  return { market, forex, bonds, ingestStatus, loading, error };
}
```

---

## Sección 6 — Actualización de pantallas

### `EconomyPage.tsx`

- Usa `useEconomyMI()` en lugar de `useEconomy()`
- Mientras `ingestStatus.status === "running"`: muestra loading skeleton con texto "Cargando datos de mercado…"
- `IndicatorCard` recibe `MacroDataPointMI` — mostrar `value`, `unit`, `period`, `quality_score`
- Sección de impacto personal: `ImpactCard` recibe `ImpactComparative` — mostrar `signal` como color (verde/rojo/neutro), `signal_text`, `market_label`, `personal_label`
- Eliminado botón "Actualizar" (la ingesta es automática)

### `MarketsPage.tsx`

- Usa `useMarketsMI()` en lugar de `useMarkets()`
- Mientras `ingestStatus.status === "running"`: loading skeleton
- `QuoteRow` recibe `QuoteMI` — mostrar `price`, `change_pct`, `quality_score` como badge (≥0.8 verde, 0.5–0.8 amarillo, <0.5 rojo)
- Forex y bonos en tabs separadas (nueva estructura)
- Eliminado `EodBadge` — sustituido por `QualityBadge` que muestra el quality_score medio del snapshot
- Sin botón de refresh manual

### Componente nuevo `QualityBadge`

```typescript
// apps/desktop/src/features/markets/components/QualityBadge.tsx
interface QualityBadgeProps { score: number; generatedAt: string; }
// score ≥ 0.8 → "● Alta calidad" (verde)
// score 0.5–0.8 → "● Calidad media" (amarillo)
// score < 0.5 → "● Datos limitados" (rojo)
```

---

## Sección 7 — Tests

### Backend

| Archivo | Qué testea |
|---|---|
| `tests/market_intelligence/test_startup.py` | `launch_startup_ingest` lanza thread, `get_ingest_status` devuelve estado correcto |
| `tests/market_intelligence/test_personal_impact.py` | Los 11 comparativos: señal correcta con datos mockeados, None cuando no hay datos personales |
| `tests/market_intelligence/test_service_catalog.py` | `_region_for()` clasifica correctamente por CatalogLoader en lugar de sets hardcodeados |

### Frontend

TypeScript check limpio (`npx tsc --noEmit`) tras eliminar los tipos legacy.

---

## Archivos a crear / modificar / eliminar

### Crear

| Archivo | Descripción |
|---|---|
| `backend/app/modules/market_intelligence/ingestion/startup.py` | IngestOnStartupService |
| `backend/app/modules/market_intelligence/api/impact.py` | Lógica de los 11 comparativos |
| `backend/tests/market_intelligence/test_startup.py` | Tests startup |
| `backend/tests/market_intelligence/test_personal_impact.py` | Tests impacto personal |
| `backend/tests/market_intelligence/test_service_catalog.py` | Tests clasificación catálogo |
| `apps/desktop/src/lib/api/market-intelligence.ts` | Cliente API unificado |
| `apps/desktop/src/lib/types/market-intelligence.ts` | Tipos TypeScript MI |
| `apps/desktop/src/lib/hooks/useMarketIntelligence.ts` | Hooks useEconomyMI + useMarketsMI |
| `apps/desktop/src/features/markets/components/QualityBadge.tsx` | Badge de calidad |

### Modificar

| Archivo | Cambio |
|---|---|
| `backend/app/main.py` | Añadir startup event, eliminar routers legacy |
| `backend/app/modules/market_intelligence/api/routes.py` | Añadir `/ingest-status` y `/personal-impact` |
| `backend/app/modules/market_intelligence/api/schemas.py` | Añadir `ImpactComparative`, `PersonalImpactOut` |
| `backend/app/modules/market_intelligence/api/service.py` | Refactor clasificación + añadir `get_personal_impact()` |
| `apps/desktop/src/features/economy/EconomyPage.tsx` | Usar useEconomyMI, adaptar IndicatorCard, ImpactCard |
| `apps/desktop/src/features/markets/MarketsPage.tsx` | Usar useMarketsMI, eliminar EodBadge, añadir QualityBadge |

### Eliminar

| Archivo/Directorio |
|---|
| `backend/app/modules/economic_data/` |
| `backend/app/modules/investments/market_data/` |
| `apps/desktop/src/lib/api/economy.ts` |
| `apps/desktop/src/lib/api/markets.ts` |
| `apps/desktop/src/lib/hooks/useEconomy.ts` |
| `apps/desktop/src/lib/hooks/useMarkets.ts` |
| `apps/desktop/src/features/markets/components/EodBadge.tsx` |
