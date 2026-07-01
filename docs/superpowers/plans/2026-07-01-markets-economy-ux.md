# Markets & Economy UX Improvement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mejorar la pantalla Mercados y Economía eliminando información técnica interna (tickers crudos, providers), añadiendo nombres legibles con banderas de país, corrigiendo bugs de datos (IBM en commodities, yields duplicados en EEUU) y rediseñando las tarjetas de impacto personal.

**Architecture:** El backend enriquece los schemas de salida con `display_name` y `display_country` tomados del catálogo YAML existente. El frontend consume esos campos nuevos en `QuoteRow`, `IndicatorCard` e `ImpactCard`. Los bugs de datos se corrigen en el adapter FRED y en el YAML de commodities. No se añaden dependencias nuevas.

**Tech Stack:** Python 3.11 / FastAPI / Pydantic v2 / DuckDB · React 18 / TypeScript / Tailwind · Lucide-react (ya instalado)

## Global Constraints

- No añadir dependencias npm ni Python nuevas
- Todos los tests existentes deben seguir pasando: `cd backend && uv run pytest app/tests/ tests/ -q --tb=short`
- TypeScript sin errores: `cd apps/desktop && npx tsc --noEmit`
- Español como idioma de UI en todos los textos nuevos
- Rama activa: `release/1.0-prep`
- Rutas absolutas desde la raíz del repo (`AI-Financial-OS/`)

---

## Mapa de archivos

| Archivo | Tarea | Tipo de cambio |
|---|---|---|
| `backend/app/modules/market_intelligence/api/schemas.py` | 1 | Añadir `display_name`, `display_country`, `description` |
| `backend/app/modules/market_intelligence/api/service.py` | 1 | Enriquecer `QuoteOut` y `MacroDataPoint` desde catálogo |
| `backend/tests/market_intelligence/test_api_service.py` | 1 | Tests de enriquecimiento con display_name |
| `backend/app/modules/market_intelligence/ingestion/adapters/usa/fred.py` | 2 | Añadir `_CATALOG_TO_FRED_SERIES` y branch para bonds |
| `backend/app/modules/market_intelligence/catalog/yaml/commodities.yaml` | 2 | Quitar `provider_secondary: alpha_vantage` de gold/silver/copper |
| `backend/tests/market_intelligence/test_adapters_import.py` | 2 | Test del fix FRED bond mapping |
| `apps/desktop/src/lib/types/market-intelligence.ts` | 3 | Añadir `display_name`, `display_country` a `QuoteMI` y `MacroDataPointMI` |
| `apps/desktop/src/features/markets/components/QuoteRow.tsx` | 3 | Usar `display_name`, banderas, quitar provider y quality badge |
| `apps/desktop/src/features/markets/MarketsPage.tsx` | 3 | Filas forex y bonds: quitar provider y catalog_id |
| `apps/desktop/src/features/economy/components/IndicatorCard.tsx` | 4 | Usar `display_name`, tooltip con `description`, quitar provider |
| `apps/desktop/src/features/economy/components/RegionTabs.tsx` | 4 | Prop `availableRegions` para ocultar tabs vacías |
| `apps/desktop/src/features/economy/EconomyPage.tsx` | 4 | Calcular y pasar `availableRegions` |
| `apps/desktop/src/features/economy/components/ImpactCard.tsx` | 5 | Iconos Lucide, labels en español, tipografía mejorada |

---

### Task 1: Backend — Enriquecimiento con display_name desde el catálogo

**Files:**
- Modify: `backend/app/modules/market_intelligence/api/schemas.py`
- Modify: `backend/app/modules/market_intelligence/api/service.py`
- Test: `backend/tests/market_intelligence/test_api_service.py`

**Interfaces:**
- Produces: `QuoteOut.display_name: Optional[str]`, `QuoteOut.display_country: Optional[str]`, `MacroDataPoint.display_name: Optional[str]`, `MacroDataPoint.description: Optional[str]` — usados en Tasks 3 y 4 desde el frontend TypeScript

- [ ] **Step 1: Escribir tests que fallan**

Añadir al final de `backend/tests/market_intelligence/test_api_service.py`:

```python
def test_get_market_snapshot_includes_display_name():
    rows = [{
        "catalog_item_id": "sp500",
        "symbol": "^SPX",
        "asset_type": "index",
        "price": 5800.0,
        "change_pct": 0.5,
        "currency": "USD",
        "observed_at": "2026-06-01T10:00:00Z",
        "provider_id": "stooq",
        "quality_score": 0.9,
    }]
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_quotes", return_value=rows):
        result = service.get_market_snapshot()
    assert result.indices[0].display_name == "S&P 500"
    assert result.indices[0].display_country == "US"


def test_get_macro_snapshot_includes_display_name():
    rows = [{
        "catalog_item_id": "ipc_general",
        "indicator_id": "ipc_general",
        "country": "ES",
        "period": "2026-05",
        "value": 2.1,
        "unit": "%",
        "provider_id": "ine",
        "quality_score": 0.9,
        "retrieved_at": "2026-06-01T10:00:00Z",
    }]
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_macro_all", return_value=rows):
        result = service.get_macro_snapshot()
    assert result.spain[0].display_name is not None
    assert "ipc" in result.spain[0].display_name.lower() or "general" in result.spain[0].display_name.lower()
    assert result.spain[0].description is not None
```

- [ ] **Step 2: Verificar que fallan**

```powershell
cd backend
uv run pytest tests/market_intelligence/test_api_service.py::test_get_market_snapshot_includes_display_name tests/market_intelligence/test_api_service.py::test_get_macro_snapshot_includes_display_name -v
```

Expected: FAIL con `AttributeError: 'QuoteOut' object has no attribute 'display_name'`

- [ ] **Step 3: Añadir campos a schemas.py**

En `backend/app/modules/market_intelligence/api/schemas.py`, modificar `MacroDataPoint` y `QuoteOut`:

```python
class MacroDataPoint(BaseModel):
    catalog_item_id: str
    indicator_id: Optional[str] = None
    country: Optional[str] = None
    period: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0
    data_status: str = "ok"
    retrieved_at: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None


class QuoteOut(BaseModel):
    catalog_item_id: str
    symbol: Optional[str] = None
    asset_type: Optional[str] = None
    price: Optional[float] = None
    change_pct: Optional[float] = None
    currency: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0
    data_status: str = "ok"
    observed_at: Optional[str] = None
    display_name: Optional[str] = None
    display_country: Optional[str] = None
```

- [ ] **Step 4: Enriquecer en service.py**

En `backend/app/modules/market_intelligence/api/service.py`, modificar la función `quote()` dentro de `get_market_snapshot()`:

```python
def quote(q: dict) -> QuoteOut:
    payload = {k: v for k, v in q.items() if k in QuoteOut.model_fields}
    payload["observed_at"] = str(q.get("observed_at", "")) if q.get("observed_at") else None
    payload["data_status"] = _status_for(q)
    cat_item = _catalog.get_by_id(q.get("catalog_item_id", ""))
    payload["display_name"] = cat_item.name if cat_item else None
    payload["display_country"] = cat_item.country if cat_item else None
    return QuoteOut(**payload)
```

Y en `get_macro_snapshot()`, dentro del bucle `for r in rows:`, añadir después de `payload["data_status"] = _status_for(r)`:

```python
cat_item = _catalog.get_by_id(r.get("catalog_item_id", ""))
payload["display_name"] = cat_item.name if cat_item else None
payload["description"] = cat_item.description if cat_item else None
```

La línea que construye el payload queda así (el loop completo):

```python
for r in rows:
    region = _region_for(r.get("catalog_item_id", ""))
    key = (region, r.get("value"), r.get("period"))
    seen_values.setdefault(key, set()).add(str(r.get("catalog_item_id", "")))
    payload = {k: v for k, v in r.items() if k in MacroDataPoint.model_fields}
    payload["retrieved_at"] = str(r.get("retrieved_at", "")) if r.get("retrieved_at") else None
    payload["data_status"] = _status_for(r)
    cat_item = _catalog.get_by_id(r.get("catalog_item_id", ""))
    payload["display_name"] = cat_item.name if cat_item else None
    payload["description"] = cat_item.description if cat_item else None
    point = MacroDataPoint(**payload)
    if region == "spain":
        spain.append(point)
    elif region == "eurozone":
        eurozone.append(point)
    elif region == "usa":
        usa.append(point)
```

- [ ] **Step 5: Verificar que los tests pasan**

```powershell
uv run pytest tests/market_intelligence/test_api_service.py -v --tb=short
```

Expected: todos los tests del archivo pasan (6 tests actualmente + 2 nuevos = 8 total)

- [ ] **Step 6: Correr suite completa para detectar regresiones**

```powershell
uv run pytest app/tests/ tests/ -q --tb=no
```

Expected: `N passed` sin fallos nuevos

- [ ] **Step 7: Commit**

```powershell
git add backend/app/modules/market_intelligence/api/schemas.py `
      backend/app/modules/market_intelligence/api/service.py `
      backend/tests/market_intelligence/test_api_service.py
git commit -m "feat(market-intelligence): expose display_name and description from catalog in API schemas"
```

---

### Task 2: Backend — Fix IBM en commodities y fix yields EEUU en FRED

**Files:**
- Modify: `backend/app/modules/market_intelligence/catalog/yaml/commodities.yaml`
- Modify: `backend/app/modules/market_intelligence/ingestion/adapters/usa/fred.py`
- Test: `backend/tests/market_intelligence/test_adapters_import.py`

**Interfaces:**
- Consumes: nada de Task 1
- Produces: el adapter FRED responde correctamente a `fetch("us_2y")`, `fetch("us_10y")`, etc. devolviendo un `YieldCurvePoint` con el maturity correcto

- [ ] **Step 1: Escribir test que falla para el fix FRED**

Leer el archivo existente:

```powershell
cat backend/tests/market_intelligence/test_adapters_import.py
```

Añadir al final:

```python
def test_fred_adapter_fetch_bond_by_catalog_id_returns_yield():
    """us_2y (catalog ID) debe mapear a DGS2 y devolver un YieldCurvePoint, no un error."""
    from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
    from app.modules.market_intelligence.ingestion.models import YieldCurvePoint
    from unittest.mock import patch, MagicMock

    csv_content = "DATE,VALUE\n2026-05-01,4.20\n2026-06-01,4.15\n"
    mock_response = MagicMock()
    mock_response.text = csv_content
    mock_response.raise_for_status = MagicMock()

    adapter = FREDAdapter()
    with patch("requests.get", return_value=mock_response):
        result = adapter.fetch("us_2y")

    assert result.success is True
    assert len(result.records) == 1
    assert isinstance(result.records[0], YieldCurvePoint)
    assert result.records[0].maturity == "2Y"
    assert result.records[0].yield_value == 4.15
```

- [ ] **Step 2: Verificar que falla**

```powershell
uv run pytest tests/market_intelligence/test_adapters_import.py::test_fred_adapter_fetch_bond_by_catalog_id_returns_yield -v
```

Expected: FAIL — `assert result.success is True` falla porque `us_2y` no está en `_BOND_INDICATOR_IDS`

- [ ] **Step 3: Añadir _CATALOG_TO_FRED_SERIES en fred.py**

En `backend/app/modules/market_intelligence/ingestion/adapters/usa/fred.py`, añadir después de `_BOND_INDICATOR_IDS`:

```python
# Mapping catalog IDs (bonds.yaml) → (FRED series, maturity label)
_CATALOG_TO_FRED_SERIES: dict[str, tuple[str, str]] = {
    "us_2y":  ("DGS2",  "2Y"),
    "us_5y":  ("DGS5",  "5Y"),
    "us_10y": ("DGS10", "10Y"),
    "us_30y": ("DGS30", "30Y"),
}
```

Y en el método `fetch()`, añadir un nuevo `elif` entre el bloque `elif indicator_id in _BOND_INDICATOR_IDS:` y el `else:`:

```python
elif indicator_id in _CATALOG_TO_FRED_SERIES:
    series_id, maturity = _CATALOG_TO_FRED_SERIES[indicator_id]
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        raw_sample = {"yield_preview": response.text[:500]}
        records.extend(_parse_yield_csv(response.text, series_id, maturity, url))
    except Exception as exc:
        errors.append(f"{series_id}: {exc}")
```

El bloque `fetch` completo con la nueva rama (solo la parte del `if/elif/elif/else`):

```python
if indicator_id is None:
    # ... (sin cambios)
elif indicator_id in _BOND_INDICATOR_IDS:
    # ... (sin cambios — legacy path para IDs antiguos)
elif indicator_id in _CATALOG_TO_FRED_SERIES:
    series_id, maturity = _CATALOG_TO_FRED_SERIES[indicator_id]
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        raw_sample = {"yield_preview": response.text[:500]}
        records.extend(_parse_yield_csv(response.text, series_id, maturity, url))
    except Exception as exc:
        errors.append(f"{series_id}: {exc}")
else:
    # ... (sin cambios)
```

- [ ] **Step 4: Verificar que el test pasa**

```powershell
uv run pytest tests/market_intelligence/test_adapters_import.py::test_fred_adapter_fetch_bond_by_catalog_id_returns_yield -v
```

Expected: PASS

- [ ] **Step 5: Fix IBM en commodities.yaml**

Editar `backend/app/modules/market_intelligence/catalog/yaml/commodities.yaml`. Eliminar la línea `provider_secondary: alpha_vantage` de los tres commodities afectados. El resultado para cada uno:

```yaml
- id: gold
  name: "Oro"
  category: commodities
  subcategory: precious_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD/oz"
  description: "Precio del oro por onza troy"
  provider_primary: stooq
  provider_fallback: polygon

- id: silver
  name: "Plata"
  category: commodities
  subcategory: precious_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD/oz"
  description: "Precio de la plata por onza troy"
  provider_primary: stooq

- id: copper
  name: "Cobre"
  category: commodities
  subcategory: base_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD/lb"
  description: "Precio del cobre"
  provider_primary: stooq
```

- [ ] **Step 6: Correr suite completa**

```powershell
uv run pytest app/tests/ tests/ -q --tb=no
```

Expected: todos pasan

- [ ] **Step 7: Commit**

```powershell
git add backend/app/modules/market_intelligence/ingestion/adapters/usa/fred.py `
      backend/app/modules/market_intelligence/catalog/yaml/commodities.yaml `
      backend/tests/market_intelligence/test_adapters_import.py
git commit -m "fix(market-intelligence): map catalog bond IDs to FRED series; remove alpha_vantage from commodities"
```

---

### Task 3: Frontend — Mercados: nombres legibles, banderas, quitar provider

**Files:**
- Modify: `apps/desktop/src/lib/types/market-intelligence.ts`
- Modify: `apps/desktop/src/features/markets/components/QuoteRow.tsx`
- Modify: `apps/desktop/src/features/markets/MarketsPage.tsx`

**Interfaces:**
- Consumes: `QuoteMI.display_name: string | undefined`, `QuoteMI.display_country: string | undefined` — definidos en este task en el tipo TypeScript

- [ ] **Step 1: Añadir campos al tipo TypeScript**

En `apps/desktop/src/lib/types/market-intelligence.ts`, modificar `QuoteMI` y `MacroDataPointMI`:

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
  data_status?: "ok" | "limited" | "unavailable" | "requires_review";
  retrieved_at?: string | null;
  display_name?: string;
  description?: string;
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
  data_status?: "ok" | "limited" | "unavailable" | "requires_review";
  observed_at?: string | null;
  display_name?: string;
  display_country?: string;
}
```

- [ ] **Step 2: Verificar TypeScript antes de cambiar componentes**

```powershell
cd apps/desktop
npx tsc --noEmit
```

Expected: sin errores (los campos nuevos son opcionales)

- [ ] **Step 3: Reescribir QuoteRow.tsx**

Reemplazar el contenido completo de `apps/desktop/src/features/markets/components/QuoteRow.tsx`:

```typescript
import type { QuoteMI } from "@/lib/types/market-intelligence";

const COUNTRY_LABELS: Record<string, string> = {
  US: "🇺🇸 EE.UU.",
  ES: "🇪🇸 España",
  DE: "🇩🇪 Alemania",
  FR: "🇫🇷 Francia",
  GB: "🇬🇧 Reino Unido",
  JP: "🇯🇵 Japón",
  EA: "🇪🇺 Eurozona",
  GLOBAL: "🌐 Global",
};

interface Props {
  quote: QuoteMI;
}

function formatPrice(price: number): string {
  const decimals = price < 10 ? 4 : 2;
  return price.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function DataStatusBadge({ status }: { status: QuoteMI["data_status"] }) {
  if (!status || status === "ok") return null;

  const config: Record<
    Exclude<QuoteMI["data_status"], "ok" | undefined>,
    { label: string; className: string }
  > = {
    limited: { label: "Limitado", className: "bg-amber-400/10 text-amber-400" },
    unavailable: { label: "Sin dato", className: "bg-white/5 text-stone" },
    requires_review: { label: "Revisar", className: "bg-accent-danger/10 text-accent-danger" },
  };

  const { label, className } = config[status];
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${className}`}>
      {label}
    </span>
  );
}

export default function QuoteRow({ quote }: Props) {
  const positive = (quote.change_pct ?? 0) >= 0;
  const title = quote.display_name ?? quote.catalog_item_id.replace(/_/g, " ");
  const regionLabel = quote.display_country
    ? (COUNTRY_LABELS[quote.display_country] ?? quote.display_country)
    : null;

  return (
    <div className="grid grid-cols-[1fr_100px_100px] items-center gap-4 px-6 py-3">
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">{title}</p>
        {regionLabel && (
          <p className="text-caption text-stone">{regionLabel}</p>
        )}
      </div>

      <div className="text-right">
        {quote.price != null ? (
          <>
            <p className="text-body-sm font-semibold text-on-dark tabular-nums">
              {formatPrice(quote.price)}
            </p>
            <p className="text-caption text-stone">{quote.currency ?? "—"}</p>
          </>
        ) : (
          <p className="text-body-sm text-stone">—</p>
        )}
      </div>

      <div className="text-right flex flex-col items-end gap-1">
        {quote.change_pct != null ? (
          <span
            className={[
              "inline-flex items-center gap-1 text-caption rounded-full px-2.5 py-[3px] font-medium",
              positive
                ? "bg-accent-teal/15 text-accent-teal"
                : "bg-accent-danger/15 text-accent-danger",
            ].join(" ")}
          >
            <span aria-hidden="true">{positive ? "▲" : "▼"}</span>
            {Math.abs(quote.change_pct).toFixed(2)}%
          </span>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
        <DataStatusBadge status={quote.data_status} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Limpiar filas de Forex y Bonds en MarketsPage.tsx**

En `apps/desktop/src/features/markets/MarketsPage.tsx`, localizar la sección del tab `forex` (línea ~133) y reemplazar el subtítulo de cada fila:

**Forex — cambiar el `<p>` del subtítulo:**

```tsx
{/* ANTES: */}
<p className="text-caption text-stone">{r.catalog_item_id} · {r.provider_id ?? "provider desconocido"} · calidad {(r.quality_score * 100).toFixed(0)}%</p>

{/* DESPUÉS: */}
<p className="text-caption text-stone">{r.date ?? "—"}</p>
```

**Bonds — cambiar el `<p>` del subtítulo:**

```tsx
{/* ANTES: */}
<p className="text-caption text-stone">{b.catalog_item_id} · {b.provider_id ?? "provider desconocido"} · calidad {(b.quality_score * 100).toFixed(0)}%</p>

{/* DESPUÉS: */}
<p className="text-caption text-stone">{b.date ?? "—"}</p>
```

El bloque completo de la fila forex queda:

```tsx
<div key={r.catalog_item_id} className="grid grid-cols-[1fr_120px_100px] items-center gap-4 px-6 py-3">
  <div>
    <p className="text-body-sm text-on-dark">{r.base_currency ?? "-"} / {r.quote_currency ?? "-"}</p>
    <p className="text-caption text-stone">{r.date ?? "—"}</p>
  </div>
  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">{r.rate != null ? r.rate.toLocaleString("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 }) : "-"}</p>
  <p className="text-caption text-stone text-right">{r.date ?? "-"}</p>
</div>
```

El bloque completo de la fila bonds queda:

```tsx
<div key={b.catalog_item_id} className="grid grid-cols-[1fr_120px_100px] items-center gap-4 px-6 py-3">
  <div>
    <p className="text-body-sm text-on-dark">{b.country ?? "-"} {b.maturity ?? ""}</p>
    <p className="text-caption text-stone">{b.date ?? "—"}</p>
  </div>
  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">{b.yield_value != null ? `${b.yield_value.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%` : "-"}</p>
  <p className="text-caption text-stone text-right">{b.date ?? "-"}</p>
</div>
```

- [ ] **Step 5: TypeScript check**

```powershell
npx tsc --noEmit
```

Expected: sin errores

- [ ] **Step 6: Commit**

```powershell
git add apps/desktop/src/lib/types/market-intelligence.ts `
      apps/desktop/src/features/markets/components/QuoteRow.tsx `
      apps/desktop/src/features/markets/MarketsPage.tsx
git commit -m "feat(markets): show display_name with country flags, remove provider info from quote rows"
```

---

### Task 4: Frontend — Economía: nombres legibles, ocultar Eurozona vacía

**Files:**
- Modify: `apps/desktop/src/features/economy/components/IndicatorCard.tsx`
- Modify: `apps/desktop/src/features/economy/components/RegionTabs.tsx`
- Modify: `apps/desktop/src/features/economy/EconomyPage.tsx`

**Interfaces:**
- Consumes: `MacroDataPointMI.display_name?: string`, `MacroDataPointMI.description?: string` — definidos en Task 3
- Consumes: `RegionTabs` recibe nueva prop `availableRegions: RegionTab[]`

- [ ] **Step 1: Reescribir IndicatorCard.tsx**

Reemplazar el contenido completo de `apps/desktop/src/features/economy/components/IndicatorCard.tsx`:

```typescript
import type { MacroDataPointMI } from "@/lib/types/market-intelligence";

const STATUS_LABELS: Record<string, string> = {
  unavailable: "Sin dato",
  seed: "Demo",
  stale: "En caché",
  limited: "Parcial",
  requires_review: "Revisar",
};

interface Props {
  indicator: MacroDataPointMI;
  size?: "default" | "large";
}

function formatValue(value: number | undefined, unit: string | undefined): string {
  if (value === undefined || value === null) return "—";
  const decimals = unit === "pts" || unit === "index" ? 0 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function IndicatorCard({ indicator, size = "default" }: Props) {
  const isUnavailable = indicator.value === undefined || indicator.value === null;
  const unitSuffix = indicator.unit ? ` ${indicator.unit}` : "";
  const valueStr = isUnavailable
    ? "—"
    : `${formatValue(indicator.value, indicator.unit)}${unitSuffix}`;

  const qualityColor =
    indicator.quality_score >= 0.8
      ? "text-accent-success"
      : indicator.quality_score >= 0.5
      ? "text-amber-400"
      : "text-accent-danger";

  const title = indicator.display_name ?? indicator.catalog_item_id.replace(/_/g, " ");

  return (
    <div
      className={[
        "rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-2",
        size === "large" ? "p-5" : "",
      ].join(" ")}
      title={indicator.description ?? undefined}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={`text-stone truncate ${size === "large" ? "text-body-sm" : "text-caption"}`}
        >
          {title}
        </span>
        <span
          className={`text-[10px] ${qualityColor} flex-shrink-0`}
          title={`Calidad: ${(indicator.quality_score * 100).toFixed(0)}%`}
        >
          ●
        </span>
      </div>

      <div
        className={`font-semibold tabular-nums flex items-center gap-2 ${
          size === "large" ? "text-2xl" : "text-xl"
        } ${isUnavailable ? "text-stone" : "text-on-dark"}`}
      >
        {valueStr}
        {indicator.data_status && indicator.data_status !== "ok" && (
          <span className="rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide bg-white/10 text-stone">
            {STATUS_LABELS[indicator.data_status] ?? indicator.data_status}
          </span>
        )}
      </div>

      {indicator.period && (
        <div className="text-[10px] text-mute mt-auto pt-1 border-t border-hairline-dark">
          {indicator.period}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Añadir prop availableRegions a RegionTabs.tsx**

Reemplazar el contenido completo de `apps/desktop/src/features/economy/components/RegionTabs.tsx`:

```typescript
type RegionTab = "ES" | "EA" | "US";

const ALL_TABS: Array<{ value: RegionTab; label: string }> = [
  { value: "ES", label: "España" },
  { value: "EA", label: "Eurozona" },
  { value: "US", label: "EEUU" },
];

interface Props {
  active: RegionTab;
  onSelect: (r: RegionTab) => void;
  availableRegions: RegionTab[];
}

export default function RegionTabs({ active, onSelect, availableRegions }: Props) {
  const tabs = ALL_TABS.filter((t) => availableRegions.includes(t.value));

  if (tabs.length <= 1) return null;

  return (
    <div role="tablist" aria-label="Seleccionar región" className="flex gap-1.5">
      {tabs.map((tab) => {
        const isActive = active === tab.value;
        return (
          <button
            key={tab.value}
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(tab.value)}
            className={[
              "flex-shrink-0 text-button-sm rounded-full px-3.5 py-1.5 h-8 transition-all duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-canvas-dark",
              isActive
                ? "bg-primary text-on-dark shadow-[0_0_0_1px_rgba(73,79,223,0.6)] font-medium"
                : "bg-surface-elevated text-stone border border-hairline-dark hover:text-on-dark hover:border-primary/40 hover:bg-surface-card",
            ].join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export type { RegionTab };
```

- [ ] **Step 3: Actualizar EconomyPage.tsx para calcular availableRegions**

En `apps/desktop/src/features/economy/EconomyPage.tsx`, modificar las líneas donde se calculan datos derivados de `macro` (después de `const globalIndicators = ...`):

```tsx
// Añadir estas líneas después de globalIndicators:
const availableRegions = macro
  ? ([
      macro.spain.length > 0 ? "ES" : null,
      macro.eurozone.length > 0 ? "EA" : null,
      macro.usa.length > 0 ? "US" : null,
    ].filter(Boolean) as import("./components/RegionTabs").RegionTab[])
  : (["ES"] as import("./components/RegionTabs").RegionTab[]);
```

Y actualizar el `useState` inicial para usar el primer elemento disponible (o "ES" como fallback):

```tsx
// La línea del useState permanece igual — se ajusta el default al montar
const [activeRegion, setActiveRegion] = useState<RegionTab>("ES");
```

Añadir un `useEffect` justo después del `useState` para ajustar `activeRegion` cuando los datos cargan:

```tsx
import { useState, useEffect } from "react";
// ...
useEffect(() => {
  if (availableRegions.length > 0 && !availableRegions.includes(activeRegion)) {
    setActiveRegion(availableRegions[0]);
  }
}, [availableRegions]);
```

Y pasar `availableRegions` a `RegionTabs`:

```tsx
{/* ANTES: */}
<RegionTabs active={activeRegion} onSelect={setActiveRegion} />

{/* DESPUÉS: */}
<RegionTabs active={activeRegion} onSelect={setActiveRegion} availableRegions={availableRegions} />
```

- [ ] **Step 4: TypeScript check**

```powershell
npx tsc --noEmit
```

Expected: sin errores

- [ ] **Step 5: Commit**

```powershell
git add apps/desktop/src/features/economy/components/IndicatorCard.tsx `
      apps/desktop/src/features/economy/components/RegionTabs.tsx `
      apps/desktop/src/features/economy/EconomyPage.tsx
git commit -m "feat(economy): show display_name in indicator cards, hide empty region tabs, remove provider from cards"
```

---

### Task 5: Frontend — ImpactCard: iconos Lucide, textos en español, tipografía

**Files:**
- Modify: `apps/desktop/src/features/economy/components/ImpactCard.tsx`

**Interfaces:**
- Consumes: `ImpactComparative` — tipo existente sin cambios
- Produce: misma API de props, solo cambios visuales

- [ ] **Step 1: Reescribir ImpactCard.tsx**

Reemplazar el contenido completo de `apps/desktop/src/features/economy/components/ImpactCard.tsx`:

```typescript
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import type { ImpactComparative } from "@/lib/types/market-intelligence";

const SIGNAL_CONFIG = {
  positive: {
    label: "Positivo",
    textColor: "text-accent-success",
    badgeClass: "bg-accent-success/10 text-accent-success border-accent-success/20",
    Icon: TrendingUp,
  },
  neutral: {
    label: "Neutral",
    textColor: "text-stone",
    badgeClass: "bg-stone/10 text-stone border-stone/20",
    Icon: Minus,
  },
  negative: {
    label: "Negativo",
    textColor: "text-accent-danger",
    badgeClass: "bg-accent-danger/10 text-accent-danger border-accent-danger/20",
    Icon: TrendingDown,
  },
  warning: {
    label: "Atención",
    textColor: "text-amber-400",
    badgeClass: "bg-amber-400/10 text-amber-400 border-amber-400/20",
    Icon: AlertTriangle,
  },
} as const;

interface Props {
  item: ImpactComparative;
}

export default function ImpactCard({ item }: Props) {
  const config = SIGNAL_CONFIG[item.signal] ?? SIGNAL_CONFIG.neutral;
  const { Icon } = config;

  return (
    <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <span className="text-body-sm text-on-dark font-medium">{item.title}</span>
        <span
          className={`text-caption border rounded px-2 py-0.5 flex-shrink-0 flex items-center gap-1.5 ${config.badgeClass}`}
        >
          <Icon size={12} />
          {config.label}
        </span>
      </div>

      <div className="flex items-center gap-4 text-body-sm tabular-nums">
        <div className="flex flex-col gap-0.5">
          <span className="text-caption text-stone">Mercado</span>
          <span className="text-on-dark">{item.market_label}</span>
        </div>
        <div className="w-px h-8 bg-hairline-dark" />
        <div className="flex flex-col gap-0.5">
          <span className="text-caption text-stone">Personal</span>
          <span className="text-on-dark">{item.personal_label}</span>
        </div>
      </div>

      <hr className="border-hairline-dark" />

      <p className={`text-body-sm font-medium leading-relaxed ${config.textColor}`}>
        {item.signal_text}
      </p>
      <p className="text-caption text-stone leading-relaxed">{item.description}</p>
    </div>
  );
}
```

- [ ] **Step 2: TypeScript check**

```powershell
npx tsc --noEmit
```

Expected: sin errores. Lucide-react ya está instalado — `TrendingUp`, `TrendingDown`, `Minus`, `AlertTriangle` existen.

Verificar con:

```powershell
grep -r "lucide-react" package.json
```

Expected: aparece en `dependencies` o `devDependencies`

- [ ] **Step 3: Commit**

```powershell
git add apps/desktop/src/features/economy/components/ImpactCard.tsx
git commit -m "feat(economy): redesign ImpactCard with Lucide icons, Spanish labels, improved typography"
```

---

## Self-Review del Plan

### 1. Cobertura del spec

| Requisito del spec | Tarea que lo implementa |
|---|---|
| Añadir `display_name`, `display_country`, `description` a schemas | Task 1 (schemas.py) |
| Enriquecer `QuoteOut` y `MacroDataPoint` desde catálogo en service.py | Task 1 (service.py) |
| Fix IBM: quitar `alpha_vantage` de gold/silver/copper en YAML | Task 2 (commodities.yaml) |
| Fix FRED: `_CATALOG_TO_FRED_SERIES` para us_2y/5y/10y/30y | Task 2 (fred.py) |
| Añadir `display_name`, `display_country` al tipo TypeScript | Task 3 (market-intelligence.ts) |
| `QuoteRow`: display_name, banderas de país, sin provider, sin quality badge | Task 3 (QuoteRow.tsx) |
| Filas forex y bonds: quitar provider y catalog_id del subtítulo | Task 3 (MarketsPage.tsx) |
| `IndicatorCard`: display_name, tooltip description, sin provider | Task 4 (IndicatorCard.tsx) |
| `RegionTabs`: ocultar tabs vacías vía `availableRegions` | Task 4 (RegionTabs.tsx) |
| `EconomyPage`: calcular availableRegions y pasar a RegionTabs | Task 4 (EconomyPage.tsx) |
| `ImpactCard`: Lucide icons, labels en español, tipografía mejorada | Task 5 (ImpactCard.tsx) |

### 2. Tipos consistentes

- `display_name: Optional[str]` en Python / `display_name?: string` en TypeScript — coherente
- `display_country: Optional[str]` en Python / `display_country?: string` en TypeScript — coherente
- `description: Optional[str]` en Python / `description?: string` en TypeScript — coherente
- `RegionTab` exportado desde `RegionTabs.tsx` y usado en `EconomyPage.tsx` — sin cambio

### 3. Sin placeholders

Todas las implementaciones tienen código completo. El único punto abierto (raíz de los duplicados 3.63%) se resuelve con el fix del FRED adapter — si los yields ya están en caché con el valor incorrecto, se limpian cuando el adapter haga una nueva ingesta con los IDs corregidos.
