# Markets & Economy UX Improvement — Design Spec

**Date:** 2026-07-01
**Status:** Approved
**Branch:** release/1.0-prep

---

## Objetivo

Mejorar la legibilidad y atractivo visual de las pantallas Mercados y Economía. Eliminar información técnica interna (providers, tickers crudos, IDs de catálogo) que confunde al usuario final, corregir bugs de datos visibles (IBM duplicado en commodities, duplicados en EEUU), y rediseñar las tarjetas de impacto personal con mejor jerarquía tipográfica e iconografía.

---

## Contexto

- Stack: Tauri + React/TypeScript + FastAPI Python
- Pantallas afectadas: `MarketsPage.tsx`, `EconomyPage.tsx`
- Componentes afectados: `QuoteRow.tsx`, `IndicatorCard.tsx`, `ImpactCard.tsx`
- Backend afectado: `schemas.py`, `service.py` (market intelligence API), `alpha_vantage.py` adapter, YAMLs de catálogo
- El catálogo YAML ya tiene `name` (legible), `description` y `country` en cada ítem — solo falta exponerlos en la API

---

## Problemas a resolver

| # | Problema | Tipo | Archivo |
|---|---|---|---|
| 1 | Tickers crudos con `^` (^SPX, ^NDQ) como título principal | Frontend + Backend | `QuoteRow.tsx`, `schemas.py` |
| 2 | Provider visible en subtítulo de cada fila | Frontend | `QuoteRow.tsx`, `IndicatorCard.tsx`, filas forex/bonds inline |
| 3 | Sin contexto de país/región para índices | Frontend + Backend | `QuoteRow.tsx`, `schemas.py` |
| 4 | IBM aparece 3 veces en Materias Primas | Backend | `alpha_vantage.py`, `commodities.yaml` |
| 5 | Indicadores de región: nombres no traducidos, sin descripción | Frontend + Backend | `IndicatorCard.tsx`, `MacroDataPoint` schema |
| 6 | Eurozona vacía sigue mostrando tab activa | Frontend | `EconomyPage.tsx`, `RegionTabs.tsx` |
| 7 | Duplicados 3.63% en EEUU (todos los bonos mismo valor) | Backend | `FREDAdapter`, repository de yields |
| 8 | ImpactCard: emojis feos, texto difícil de leer, señal en inglés | Frontend | `ImpactCard.tsx` |

---

## Arquitectura del cambio

### Backend — Enriquecimiento del catálogo en la API

**`schemas.py`** — añadir campos opcionales a los schemas de salida:

```python
class MacroDataPoint(BaseModel):
    # campos existentes...
    display_name: Optional[str] = None      # catálogo name (ej. "PIB España")
    description: Optional[str] = None       # catálogo description (ej. "Producto Interior Bruto")

class QuoteOut(BaseModel):
    # campos existentes...
    display_name: Optional[str] = None      # catálogo name (ej. "S&P 500")
    display_country: Optional[str] = None   # catálogo country ISO (ej. "US", "ES", "EA")
```

**`service.py` — `get_market_snapshot()`** — al construir cada `QuoteOut`, buscar el ítem en el catálogo:

```python
cat_item = _catalog.get_by_id(catalog_item_id)
display_name = cat_item.name if cat_item else None
display_country = cat_item.country if cat_item else None
```

**`service.py` — `get_macro_snapshot()`** — mismo patrón para `MacroDataPoint`:

```python
cat_item = _catalog.get_by_id(r.get("catalog_item_id", ""))
payload["display_name"] = cat_item.name if cat_item else None
payload["description"] = cat_item.description if cat_item else None
```

### Backend — Fix IBM (AlphaVantage)

**`commodities.yaml`** — quitar `provider_secondary: alpha_vantage` de los 3 commodities afectados (gold, silver, copper). Alpha Vantage no tiene endpoints de commodities físicos equivalentes — el adapter actual es un placeholder hardcodeado a IBM stock.

```yaml
# gold, silver, copper: eliminar provider_secondary
- id: gold
  provider_primary: stooq
  # provider_secondary eliminado
```

El adapter `alpha_vantage.py` queda intacto (puede tener utilidad para otros usos futuros como acciones) pero no se invoca para commodities.

### Backend — Fix duplicados EEUU (yields / FRED adapter)

**Bug exacto:** `FREDAdapter._BOND_INDICATOR_IDS` contiene `"us_treasury_2y"`, `"us_treasury_10y"`, etc., pero el catálogo (`bonds.yaml`) usa `"us_2y"`, `"us_10y"`. El `elif indicator_id in _BOND_INDICATOR_IDS` nunca hace match → los bonds caen al `else` → `_INDICATOR_SERIES.get("us_2y", [])` devuelve `[]` → FRED retorna `success=False`. El valor 3.63% que aparece viene de la ingesta de health-check (`indicator_id=None`) que mezcla todos los yields sin discriminar por catalog_item_id.

**Fix en `fred.py`:** Añadir un mapa `_CATALOG_TO_FRED_SERIES` que relacione los IDs del catálogo con las series FRED correctas:

```python
_CATALOG_TO_FRED_SERIES: dict[str, tuple[str, str]] = {
    "us_2y":  ("DGS2",  "2Y"),
    "us_5y":  ("DGS5",  "5Y"),
    "us_10y": ("DGS10", "10Y"),
    "us_30y": ("DGS30", "30Y"),
}
```

En `fetch(indicator_id)`: añadir `elif indicator_id in _CATALOG_TO_FRED_SERIES:` antes del `else`, que descarga solo la serie FRED correcta para ese bono y retorna un `YieldCurvePoint` con el `maturity` correspondiente.

---

## Cambios de Frontend

### `QuoteRow.tsx`

**Estructura de una fila (antes → después):**

```
ANTES:
Línea 1: ^SPX                          [precio] [cambio%]
Línea 2: sp500 · stooq                 [divisa]  [calidad]

DESPUÉS:
Línea 1: S&P 500                       [precio] [cambio%]
Línea 2: 🇺🇸 EE.UU.                    [divisa]
```

Cambios concretos:
- Título: `display_name ?? catalog_item_id.replace(/_/g, " ")` — nunca `quote.symbol` directamente
- Subtítulo: bandera + región usando el mapa de países (ver abajo), sin provider
- Eliminar el badge de calidad (`quality_score`) del área visible del usuario — es información interna
- Mantener `DataStatusBadge` (Limitado / Sin dato / Revisar) porque sí es relevante para el usuario

**Mapa de países** (constante en el componente):
```typescript
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
```

### Filas inline de Forex y Bonds (en `MarketsPage.tsx`)

- Forex: subtítulo → quitar `catalog_item_id` y `provider_id`; mostrar solo par (`EUR / USD`) y fecha
- Bonds: subtítulo → quitar `catalog_item_id` y `provider_id`; mostrar solo país + vencimiento y fecha

### `IndicatorCard.tsx`

**Estructura (antes → después):**

```
ANTES:
confianza consumidor spain ●
86 index [PARCIAL]
fred · 2026-06

DESPUÉS:
Confianza Consumidor España ●
86 index [PARCIAL]
2026-06
```

Cambios:
- Título: `display_name ?? catalog_item_id.replace(/_/g, " ")` 
- Footer: solo `indicator.period` — sin `provider_id`
- Añadir `title` HTML con `indicator.description` del catálogo (aparece en tooltip al hover) — el catálogo ya lo tiene en inglés; traducirlo en el YAML si se detecta en inglés, o mostrarlo directamente si el YAML ya está en español

### `EconomyPage.tsx` + `RegionTabs.tsx`

- `RegionTabs`: recibir prop `availableRegions: RegionTab[]`; solo renderizar tabs para las regiones con datos
- `EconomyPage`: calcular `availableRegions` antes de renderizar:
  ```typescript
  const availableRegions: RegionTab[] = [
    ...(macro.spain.length > 0 ? ["ES" as const] : []),
    ...(macro.eurozone.length > 0 ? ["EA" as const] : []),
    ...(macro.usa.length > 0 ? ["US" as const] : []),
  ];
  ```
- Si `availableRegions` tiene solo 1 elemento, no mostrar el selector de tabs en absoluto
- `activeRegion` inicial = primer elemento de `availableRegions`

### `ImpactCard.tsx`

**Señal — badge rediseñado:**
- Quitar emojis ✅ ➖ ⚠️
- Usar iconos Lucide: `TrendingUp` (positive), `Minus` (neutral), `TrendingDown` (negative), `AlertTriangle` (warning)
- Textos en español: `{ positive: "Positivo", neutral: "Neutral", negative: "Negativo", warning: "Atención" }`
- Tamaño del ícono: `size={12}`

**Tipografía:**
- `signal_text` (análisis): subir de `text-caption` a `text-body-sm font-medium`
- `description` (explicación): mantener `text-caption text-stone` pero añadir `leading-relaxed`

**Layout:**
- Añadir `<hr className="border-hairline-dark" />` entre la fila Mercado/Personal y el bloque de texto de análisis
- Pequeño padding extra entre la fila de valores y el separador

---

## Archivos a tocar

### Backend
| Archivo | Cambio |
|---|---|
| `backend/app/modules/market_intelligence/api/schemas.py` | Añadir `display_name`, `display_country`, `description` |
| `backend/app/modules/market_intelligence/api/service.py` | Enriquecer `QuoteOut` y `MacroDataPoint` desde catálogo |
| `backend/app/modules/market_intelligence/catalog/yaml/commodities.yaml` | Quitar `provider_secondary: alpha_vantage` de gold, silver, copper |
| `backend/app/modules/market_intelligence/storage/repository.py` | Fix `get_latest_yields()` — discriminar por catalog_item_id correcto |

### Frontend
| Archivo | Cambio |
|---|---|
| `apps/desktop/src/features/markets/components/QuoteRow.tsx` | display_name, banderas, quitar provider y quality_score badge |
| `apps/desktop/src/features/markets/MarketsPage.tsx` | Filas forex y bonds — quitar provider/catalog_id |
| `apps/desktop/src/features/economy/components/IndicatorCard.tsx` | display_name, quitar provider, tooltip con description |
| `apps/desktop/src/features/economy/components/RegionTabs.tsx` | Prop availableRegions, ocultar tabs sin datos |
| `apps/desktop/src/features/economy/EconomyPage.tsx` | Calcular availableRegions, pasar a RegionTabs |
| `apps/desktop/src/features/economy/components/ImpactCard.tsx` | Iconos Lucide, textos en español, tipografía mejorada |
| `apps/desktop/src/lib/types/market-intelligence.ts` | Añadir campos nuevos al tipo TypeScript |

---

## Tests a actualizar / añadir

- `backend/tests/market_intelligence/test_api_service.py`: verificar que `display_name` se puebla en `get_market_snapshot()` y `get_macro_snapshot()`
- `backend/app/tests/test_economy_data_integrity.py`: verificar que no hay yields duplicados con el mismo valor para distintos maturities (snapshot test)

---

## Lo que NO cambia

- La lógica de negocio de ingesta y almacenamiento (salvo el fix de yields y el YAML de commodities)
- El componente `QualityBadge` del header de MarketsPage (es información agregada, no por-fila)
- La sección "Pulso de mercado" del header
- El comportamiento de refresco y estado de ingesta
