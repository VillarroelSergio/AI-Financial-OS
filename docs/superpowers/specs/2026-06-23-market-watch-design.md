# Spec: Fase 4 — Market Watch

**Fecha:** 2026-06-23  
**Estado:** Aprobado por usuario  

---

## Contexto y objetivo

Pantalla de contexto de mercado global para un inversor español con cartera en Trade Republic y Finizens. Responde: **"¿Cómo están los mercados ahora mismo?"** sin mezclar datos personales con datos de mercado.

36 activos fijos en 8 categorías, con precios actualizándose automáticamente cada 5 segundos (experiencia visual tipo Trade Republic / Revolut). Sin botón de refresh manual — el polling es transparente para el usuario.

---

## Alcance

### Incluye

- 36 activos fijos en 8 categorías (sin UI de edición)
- Polling automático cada 5s desde el frontend
- Caché en backend con TTL de 15s (yfinance se consulta cada 15s máximo)
- Sparklines intraday del día actual por activo
- Flash animation en precio al detectar cambio
- Indicador "● Live" pulsante en el header
- Navegación por tabs de categoría (pill buttons)
- Estados: loading skeleton / error / success
- Mock data en `mock-data.ts`
- UX snapshot en `snapshot-routes.ts`

### No incluye

- Edición de la lista de activos desde la UI
- Histórico de más de 1 día (solo intraday del día actual para sparkline)
- Alertas de precio
- Comparativas con cartera personal (eso va en Fase 5+)

---

## Activos

### Europa (6)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| IBEX 35 | `^IBEX` | indices_eu |
| Euro Stoxx 50 | `^STOXX50E` | indices_eu |
| STOXX Europe 600 | `^STOXX` | indices_eu |
| DAX | `^GDAXI` | indices_eu |
| CAC 40 | `^FCHI` | indices_eu |
| FTSE 100 | `^FTSE` | indices_eu |

### EEUU (4)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| S&P 500 | `^GSPC` | indices_us |
| Nasdaq 100 | `^NDX` | indices_us |
| Dow Jones | `^DJI` | indices_us |
| Russell 2000 | `^RUT` | indices_us |

### Asia (4)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| Nikkei 225 | `^N225` | indices_asia |
| Hang Seng | `^HSI` | indices_asia |
| Shanghai Composite | `000001.SS` | indices_asia |
| Nifty 50 | `^NSEI` | indices_asia |

### Cripto (4)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| Bitcoin | `BTC-USD` | crypto |
| Ethereum | `ETH-USD` | crypto |
| BNB | `BNB-USD` | crypto |
| Solana | `SOL-USD` | crypto |

### Divisas (6)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| EUR/USD | `EURUSD=X` | fx |
| EUR/GBP | `EURGBP=X` | fx |
| EUR/JPY | `EURJPY=X` | fx |
| GBP/USD | `GBPUSD=X` | fx |
| USD/JPY | `JPY=X` | fx |
| USD/CHF | `CHF=X` | fx |

### Bonos 10Y (5)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| Treasury EEUU 10Y | `^TNX` | bonds |
| Bund Alemania 10Y | `^IRX` | bonds |
| Bono España 10Y | `ES10Y=X` | bonds |
| Gilt UK 10Y | `^TMBMKGB-10Y` | bonds |
| BTP Italia 10Y | `IT10Y=X` | bonds |

### Materias Primas (6)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| Oro | `GC=F` | commodities |
| Plata | `SI=F` | commodities |
| Petróleo Brent | `BZ=F` | commodities |
| Petróleo WTI | `CL=F` | commodities |
| Gas Natural | `NG=F` | commodities |
| Cobre | `HG=F` | commodities |

### Volatilidad (1)
| Nombre | Ticker yfinance | Categoría |
|--------|----------------|-----------|
| VIX | `^VIX` | volatility |

---

## Arquitectura

### Backend

**Módulo:** `backend/app/modules/market_data/` (scaffold vacío existente)

**Archivos a crear:**
- `routes.py` — endpoints REST
- `service.py` — lógica de negocio + caché en memoria
- `schemas.py` — modelos Pydantic

**Caché en memoria (TTL 15s):**

```python
_cache: dict = {"data": None, "updated_at": None}
CACHE_TTL = 15  # segundos
```

Si `updated_at` es None o han pasado más de 15s: llama a yfinance en background thread y devuelve el caché anterior si existe (never-block). Primera llamada espera sincrónicamente.

**Sparkline:**
`yfinance.Ticker(ticker).history(period="1d", interval="5m")` — devuelve los precios del día actual en intervalos de 5 minutos como lista de floats.

#### Endpoints

```
GET /api/markets/quotes
  → QuoteOut[] — todos los activos con precio, variación, sparkline

GET /api/markets/quotes?category=indices_eu
  → QuoteOut[] — filtrado por categoría
```

#### Schema `QuoteOut`

```python
class QuoteOut(BaseModel):
    symbol: str           # "^IBEX"
    name: str             # "IBEX 35"
    category: str         # "indices_eu"
    price: float | None   # último precio
    change_pct: float | None   # variación % del día
    currency: str         # "EUR", "USD", etc.
    sparkline: list[float]     # precios intraday del día (hasta 78 puntos a 5min)
    last_updated: str     # ISO 8601 UTC
    market_open: bool     # si el mercado está abierto ahora
```

Si yfinance falla para un ticker: `price: null`, `change_pct: null`, `sparkline: []`. No bloquea el resto.

### Frontend

**Archivos:**
- `apps/desktop/src/lib/api/markets.ts` — API client
- `apps/desktop/src/lib/hooks/useMarkets.ts` — hook con polling
- `apps/desktop/src/features/markets/components/QuoteRow.tsx`
- `apps/desktop/src/features/markets/components/MiniSparkline.tsx`
- `apps/desktop/src/features/markets/components/CategoryTabs.tsx`
- `apps/desktop/src/features/markets/components/LiveIndicator.tsx`
- `apps/desktop/src/features/markets/MarketsPage.tsx` — reemplazar scaffold

#### Hook `useMarkets`

```typescript
function useMarkets(category?: string) {
  // Polling cada 5s, pausado cuando document.hidden
  // Devuelve: { quotes, loading, error, lastUpdated, secondsSinceUpdate }
}
```

- `useInterval(fetch, 5000)` — usando `@react-hook/interval` o implementación propia
- `document.addEventListener("visibilitychange", ...)` — pausa al cambiar de tab
- Compara quotes anterior con nuevo para detectar cambios de precio

#### Componente `QuoteRow`

```
[Nombre]        [MiniSparkline]   [Precio]    [Badge ±%]
IBEX 35         ~~~~              9.842,15    ▲ +1,23%
```

- Flash: cuando `price` cambia, aplica clase CSS `flash-up` o `flash-down` durante 300ms
- `flash-up`: background `accent-teal/10` → transparente
- `flash-down`: background `accent-danger/10` → transparente
- Precio con formato local: `toLocaleString("es-ES", { minimumFractionDigits: 2 })`
- Badge: `badge-semantic` `success` (verde) o `danger` (rojo)

#### Componente `MiniSparkline`

- Recharts `LineChart` sin ejes, sin grid, sin tooltip — solo la línea
- Dimensiones: 60×24px
- Color: `accent-teal` si change_pct ≥ 0, `accent-danger` si < 0
- Si sparkline está vacío: línea plana en gris (`stone`)

#### Componente `LiveIndicator`

```
● En vivo · Actualizado hace 3s
```

- Punto: 6px, `accent-teal`, animación `pulse` (opacity 1→0.3→1, 2s loop)
- Texto: `caption`, `stone`
- "Actualizado hace Xs" se recalcula cada segundo con `useInterval(tick, 1000)`

#### Componente `CategoryTabs`

Pills `button-pill-sm`:
`Todos` · `Europa` · `EEUU` · `Asia` · `Cripto` · `Divisas` · `Bonos` · `Mat. Primas`

Mapeo categoría → label:
```
all          → "Todos"
indices_eu   → "Europa"
indices_us   → "EEUU"
indices_asia → "Asia"
crypto       → "Cripto"
fx           → "Divisas"
bonds        → "Bonos"
commodities  → "Mat. Primas"
volatility   → "Volatilidad"
```

#### Layout `MarketsPage`

```
p-xxxl space-y-xl

[Header row]
  "Mercados" (text-heading-lg)
  <LiveIndicator />

[CategoryTabs]

[Card surface-elevated rounded-lg]
  Tab "Todos":
    [Section header: "EUROPA" (caption stone uppercase)]
    [QuoteRow × 6] separados por divider-soft
    [Section header: "ESTADOS UNIDOS"]
    [QuoteRow × 4]
    ... (resto de categorías)

  Tab específica:
    [QuoteRow × N] sin section headers

[Loading state]: skeleton de QuoteRow (mismo tamaño)
[Error state]: InsightCard severity:danger + texto "Error al cargar datos de mercado"
```

---

## Animaciones

```css
@keyframes flash-up {
  0%   { background-color: rgba(0, 168, 126, 0.15); }
  100% { background-color: transparent; }
}

@keyframes flash-down {
  0%   { background-color: rgba(226, 59, 74, 0.15); }
  100% { background-color: transparent; }
}

/* Duración: 300ms, una sola vez (no loop) */
.flash-up   { animation: flash-up 300ms ease-out forwards; }
.flash-down { animation: flash-down 300ms ease-out forwards; }

@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
.live-dot { animation: live-pulse 2s ease-in-out infinite; }
```

Para aplicar el flash: React re-monta la clase CSS asignando una key aleatoria o usando `useEffect` con un timeout de limpieza.

---

## Mock data

En `apps/desktop/src/lib/api/mock-data.ts`, fixture `mockMarketQuotes`:
- 36 entradas con precios reales aproximados a fecha de escritura del spec
- Sparklines: arrays de 20 puntos generados sintéticamente (tendencia aleatoria)
- `last_updated`: "2026-06-23T10:00:00Z"
- `market_open`: true para índices EU/US, false para Asia (fuera de horario)

Ruta mock: `/api/markets/quotes`

---

## UX Snapshots

Añadir a `tools/ux-snapshot/snapshot-routes.ts`:
```typescript
{ path: "/markets", filename: "markets.png", screenName: "Markets", state: "mock_data", description: "Market Watch con 36 activos en 8 categorías, tab Todos" }
{ path: "/markets", filename: "markets-europa.png", screenName: "Markets Europa", state: "mock_data", description: "Market Watch filtrado por categoría Europa" }
```

---

## Deuda técnica generada

| # | Deuda | Impacto |
|---|-------|---------|
| TD-07 | Tickers de bonos 10Y pueden no estar disponibles en yfinance para todos los países — fallback a `price: null` | Bajo — se muestra "—" en la UI |
| TD-08 | Caché en memoria se pierde al reiniciar el servidor | Bajo — se reconstruye en el primer poll |
| TD-09 | Sin datos históricos de más de 1 día — solo intraday actual | Medio — gráfica histórica queda para Fase 5+ |

---

## Actualización del roadmap

Al completar esta fase, marcar en `docs/02_ROADMAP.md`:
- Fase 4 → ✅ Completa
