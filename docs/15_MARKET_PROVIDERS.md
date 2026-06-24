# 15 — Market Data Providers

## Resumen

AI Financial OS usa una arquitectura **multi-provider gratuita con motor de consenso**.
Todos los proveedores son gratuitos. No existe ningún proveedor de pago. No existe importación
manual por CSV para datos de mercado.

En lugar de un fallback secuencial, el sistema hace un **fetch paralelo** de todos los
proveedores configurados para cada activo y aplica un **ConsensusEngine** que:

1. Descarta outliers (precios que se desvían más del umbral por tipo de activo).
2. Compara el proveedor primario contra la mediana.
3. Calcula un `confidence_score` ponderado por frescura, tipo de proveedor y posición en la cadena.
4. Devuelve el precio más fiable junto con metadatos de decisión auditables.

Yahoo Finance actúa únicamente como **último recurso** — solo se consulta si todos los
demás proveedores fallan para un activo concreto.

---

## Proveedores

### 1. StooqProvider — Primario para índices, bonos y volatilidad

| | |
|---|---|
| **API key** | No requerida |
| **Activado por defecto** | Sí |
| **Cobertura** | Índices mundiales, forex básico, commodities (futuros), bonos, volatilidad |
| **Tipo de dato** | EOD (End of Day) — el más reciente disponible |
| **Freshness** | `eod`, `fresh` si el dato es <30 min |
| **Límites** | Sin límite oficial. Throttle interno: 1 llamada/segundo |
| **Caché TTL** | 15 min (quotes), 24h (histórico) |
| **Nota** | Stooq no promete datos en tiempo real. Puede requerir JavaScript en ciertas rutas — su endpoint CSV público sigue funcionando. |

**Primario para:** `index`, `bond`, `volatility`, `stocks_europe`

---

### 2. TwelveDataProvider — Primario para forex y commodities *(nuevo)*

| | |
|---|---|
| **API key** | `TWELVEDATA_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Cobertura** | Índices (US + EU), acciones (US + EU), forex, cripto, commodities |
| **Free tier** | 800 req/día, 8 req/min |
| **Budget interno** | 700 req/día (margen de seguridad) |
| **Freshness** | `live` / `delayed` según timestamp de respuesta |
| **Endpoints usados** | `/price` (precio actual) + `/quote` (prev_close, market_time, is_market_open) |
| **Símbolos forex** | Formato `EUR/USD`, `GBP/USD` (slash notation) |
| **Símbolos índices** | `SPX`, `NDX`, `DAX`, `CAC40`, etc. |
| **Símbolos cripto** | `BTC/USD`, `ETH/USD` (slash notation) |
| **Símbolos commodity** | `XAU/USD` (Oro), `XAG/USD` (Plata), `WTI/USD`, `BRENT/USD` |

**Cómo obtener API key gratuita:**
1. Ir a https://twelvedata.com — crear cuenta (no requiere tarjeta)
2. Copiar la API key del dashboard
3. Añadir a `.env`: `TWELVEDATA_API_KEY=tu_clave`

**Primario para:** `forex`, `commodity`
**Validador para:** `index`, `stocks_us`, `stocks_europe`, `crypto`

---

### 3. FinnhubProvider — Primario para acciones USA y cripto

| | |
|---|---|
| **API key** | `FINNHUB_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Cobertura** | Acciones USA, forex (OANDA), cripto (Binance), perfiles, fundamentales |
| **Free tier** | 60 req/min |
| **Rate limiter** | 55 req/min (con buffer) — en 429, devuelve error y continúa |
| **Freshness** | Puede ser `live` si el timestamp es reciente (<5 min) |
| **Endpoint** | `https://finnhub.io/api/v1/quote` |

**Cómo obtener API key gratuita:**
1. Ir a https://finnhub.io/register
2. Registrarse
3. Añadir a `.env`: `FINNHUB_API_KEY=tu_clave`

**Primario para:** `stocks_us`, `crypto`
**Validador para:** `index`, `forex`

---

### 4. AlphaVantageProvider — Validador con presupuesto

| | |
|---|---|
| **API key** | `ALPHA_VANTAGE_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Cobertura** | Acciones, forex, cripto |
| **Free tier** | 25 req/día (estándar) o 500 req/día (con registro de email) |
| **Budget interno** | 400 req/día (margen de seguridad) |
| **Rate limiter** | 5 req/min (interno) — se salta si el presupuesto diario está agotado |
| **Uso recomendado** | Solo como validador secundario, no como primario |

**Cómo obtener API key gratuita:**
1. Ir a https://www.alphavantage.co/support/#api-key
2. Registrarse con email
3. Añadir a `.env`: `ALPHA_VANTAGE_API_KEY=tu_clave`

**Validador para:** `forex`, `crypto`, `stocks_us` (presupuesto-dependiente)

---

### 5. FMPProvider — Fundamentales y perfiles

| | |
|---|---|
| **API key** | `FMP_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Cobertura** | Acciones, ETFs, perfiles de empresa, fundamentales, ratios |
| **Free tier** | 250 req/día |
| **Budget interno** | 200 req/día (margen de seguridad) |
| **Freshness** | `eod` (dato EOD en free tier) |

**Cómo obtener API key gratuita:**
1. Ir a https://financialmodelingprep.com/register
2. Registrarse
3. Añadir a `.env`: `FMP_API_KEY=tu_clave`

**Primario para:** `fundamentals`
**Validador para:** `stocks_us`, `stocks_europe`

---

### 6. YahooFinanceProvider — Último recurso

| | |
|---|---|
| **API key** | No requerida |
| **Activado por defecto** | Sí |
| **Rol** | `last_resort` — NUNCA primario, NUNCA validador |
| **Cobertura** | Universal (todos los asset types) |
| **Tipo de dato** | Delayed (retrasado, no garantizado) |
| **Freshness** | Siempre `delayed` o `unknown` — nunca `live` |
| **Cuándo se usa** | Solo si `valid_provider_count == 0` tras el fetch paralelo de todos los demás |
| **Warning** | `yahoo_last_resort` añadido al quote cuando se usa |
| `diagnostic_mode` | `false` por defecto — si se activa, Yahoo aparece en logs de decisión como comparador |

---

## ConsensusEngine

El `ConsensusEngine` (`consensus.py`) resuelve el precio a partir de los quotes recogidos en paralelo.

### Algoritmo

```
Inputs: List[MarketQuoteInternal] de N proveedores
Output: ConsensusResult (precio final + confidence_score + logs de decisión)

1. Filtrar errores: price != None AND freshness_status != "error"

2. 0 válidos → error (confidence = 0.0)

3. 1 válido → precio del único proveedor
              confidence = min(base_weight × 0.6, 0.6)
              warning: "unverified_single_provider"

4. ≥2 válidos:
   a. Si ≥3: calcular mediana, detectar outliers (desviación > threshold por asset_type),
             descartar outliers, recalcular mediana
   b. Comprobar proveedor primario vs mediana:
      - Dentro del 1% → usar precio del primario (method: "primary")
      - Fuera del 1% → usar mediana (method: "median"), warning: "provider_mismatch"
   c. Si primario ausente → usar mediana (sin warning de mismatch)
   d. Calcular weighted_confidence
```

### Fórmula de confianza ponderada

```
confidence = Σ(base_weight × freshness × primary_bonus × fallback_penalty + market_time_bonus)
             ─────────────────────────────────────────────────────────────────────────────────
                              Σ(base_weight)  [denominador: pesos base]

Donde:
  freshness:        live=1.0, fresh=0.9, delayed=0.8, eod=0.6, closed=0.6, unknown=0.5
  primary_bonus:    ×1.2 si es el proveedor primario del asset_type
  fallback_penalty: ×0.5 si is_fallback=True
  market_time_bonus: +0.1 si tiene market_time (timestamp exacto del mercado)
```

### Umbrales de outlier por asset_type

| Tipo | Umbral |
|---|---|
| `index` | 1% |
| `stock` | 2% |
| `forex` | 0.5% |
| `crypto` | 5% |
| `commodity` | 3% |
| `bond` | 1% |
| `volatility` | 5% |

---

## Routing

El `ProviderRouter` usa **fetch paralelo** + `ConsensusEngine`. El YAML define el rol de cada
proveedor por asset_type:

| Tipo de activo | Primario | Validadores | Budget-aware | Último recurso |
|---|---|---|---|---|
| Índices | Stooq | TwelveData, Finnhub | AV | Yahoo |
| Acciones USA | Finnhub | TwelveData, FMP | AV | Yahoo |
| Acciones Europa | Stooq | TwelveData, FMP | — | Yahoo |
| Forex | TwelveData | Finnhub, AV | AV | Yahoo |
| Cripto | Finnhub | TwelveData, AV | AV | Yahoo |
| Commodities | TwelveData | — | — | Yahoo |
| Bonos | Stooq | — | — | Yahoo |
| Volatilidad | Stooq | — | — | Yahoo |
| Fundamentales | FMP | Finnhub, AV | AV | — |

El routing se configura en `market_data_config.yaml` bajo la clave `routing:`.
Cada entrada tiene la forma:

```yaml
routing:
  indices:
    primary: stooq
    validators: [twelvedata, finnhub]
    budget_aware: [alphavantage]
    last_resort: yahoo
```

---

## RequestBudget

El `RequestBudget` (`budget.py`) protege los providers con límite diario:

| Proveedor | Free tier | Budget interno |
|---|---|---|
| Alpha Vantage | 500/día | 400/día |
| TwelveData | 800/día | 700/día |
| FMP | 250/día | 200/día |

Antes de cada petición, el router llama `budget.can_request(provider)`. Si devuelve `False`,
el provider se omite en el fetch paralelo y se añade el warning `budget_exhausted` al quote.

Los conteos se calculan directamente desde `market_provider_logs` en DuckDB (campo `fetched_at`,
filtro `cache_hit = false`). El presupuesto se resetea automáticamente a medianoche UTC.

---

## Warnings normalizados

Todos los warnings en `MarketQuoteInternal.warning` usan estos códigos estandarizados:

| Código | Significado |
|---|---|
| `rate_limited` | El proveedor devolvió 429 o señal de rate limit |
| `budget_exhausted` | Presupuesto diario agotado para este proveedor |
| `provider_error` | El proveedor devolvió un error en la respuesta |
| `provider_timeout` | La petición al proveedor superó el timeout (5s) |
| `provider_mismatch` | El primario se desvía >1% de la mediana del consenso |
| `outlier_detected` | Uno o más proveedores descartados por precio outlier |
| `unverified_single_provider` | Solo un proveedor disponible — dato sin verificar |
| `yahoo_last_resort` | Yahoo usado porque todos los demás fallaron |
| `stale_cache_used` | Dato cacheado servido porque todos los providers fallaron |

---

## Caché (DuckDB)

Tablas en `data/analytics.duckdb`:

| Tabla | Descripción | TTL |
|---|---|---|
| `market_quotes_cache` | Último quote por símbolo (upsert) | Variable por tipo |
| `market_candles_cache` | OHLCV histórico (append) | 24h |
| `market_provider_logs` | Logs de fetch y budget tracking | Sin TTL automático |
| `market_company_profiles` | Perfiles de empresa | 30 días |
| `market_fundamentals_cache` | Fundamentales | 7 días |

**TTL por tipo de activo:**

| Tipo | TTL |
|---|---|
| Cripto / Volatilidad | 5 minutos |
| Índices / Acciones / Forex / Commodities / Bonos | 15 minutos |
| EOD / Histórico diario | 24 horas |
| Fundamentales | 7 días |
| Perfiles de empresa | 30 días |

---

## Estados de frescura (freshness_status)

| Estado | Descripción | Cuándo aparece |
|---|---|---|
| `live` | Precio <5 min, mercado abierto | Solo Finnhub/TwelveData con timestamp reciente |
| `fresh` | Precio <15 min | Stooq o Finnhub con dato muy reciente |
| `delayed` | Precio retrasado 15–60 min | TwelveData, Yahoo Finance |
| `eod` | Último cierre del mercado | Stooq (EOD), FMP free tier |
| `closed` | Mercado confirmado cerrado | Cuando el provider reporta mercado cerrado |
| `stale` | Caché vencida | Todos los proveedores fallaron, se usa caché antigua |
| `error` | Sin datos disponibles | Todos los proveedores fallaron y no hay caché |
| `unknown` | Sin información de frescura | Dato sin timestamp fiable |

**Regla importante:** la UI solo muestra "En vivo" cuando `freshness_status == "live"`.
Yahoo Finance nunca reporta `live`. TwelveData puede reportar `live` si el timestamp es reciente.

---

## Configuración

El archivo `backend/app/modules/market_data/config/market_data_config.yaml` contiene:

- `providers:` — prioridad, API key env var, rate limits, rol
- `routing:` — primary / validators / budget_aware / last_resort por asset_type
- `outlier_thresholds:` — umbral de outlier por asset_type
- `provider_weights:` — peso base por proveedor × asset_type (usado en ConsensusEngine)
- `request_budget:` — límites diarios conservadores por proveedor
- `cache_ttl:` — TTL por categoría de dato
- `symbol_mappings:` — 36 activos con símbolos por proveedor

---

## Añadir un nuevo símbolo

1. Abrir `market_data_config.yaml`
2. Añadir entrada en `symbol_mappings`:

```yaml
"TICKER_INTERNO":
  name: "Nombre del activo"
  category: "indices_eu"     # categoría visible en la UI
  asset_type: "index"        # index | stock | etf | forex | crypto | bond | commodity | volatility
  currency: "EUR"
  providers:
    stooq: "ticker_stooq"
    yahoo: "TICKER_YAHOO"
    twelvedata: "TICKER_TD"  # formato según asset_type (slash para forex/cripto)
    finnhub: "TICKER_FH"     # opcional
```

3. El router lo cargará automáticamente en el siguiente arranque.

---

## Añadir un nuevo proveedor gratuito

1. Crear `backend/app/modules/market_data/providers/miprovider.py`
2. Extender `MarketDataProvider` (ABC en `providers/base.py`)
3. Implementar `supports()` y `get_quote()` — **nunca deben lanzar excepciones** (usar `_error_quote()`)
4. Añadir el provider a `providers/__init__.py`
5. Registrarlo en `ProviderRouter.__init__()` en `router.py`
6. Añadir configuración en `market_data_config.yaml` (providers + routing + provider_weights)
7. Si tiene límite diario, añadir en `request_budget:` del YAML

---

## Variables de entorno

```bash
# backend/.env  (nunca commitear este fichero)
TWELVEDATA_API_KEY=      # primario forex/commodities — https://twelvedata.com
FINNHUB_API_KEY=         # primario acciones USA/cripto — https://finnhub.io
ALPHA_VANTAGE_API_KEY=   # validador secundario — https://alphavantage.co
FMP_API_KEY=             # fundamentales y perfiles — https://financialmodelingprep.com
```

Las keys vacías desactivan el proveedor correspondiente.
La app funciona completamente sin API keys (Stooq cubre índices, bonos y volatilidad).
Con todas las keys, el ConsensusEngine puede cruzar hasta 4 fuentes por activo.

---

## Lo que NO existe

- **ManualCsvProvider** — no existe ni existirá. Los datos de mercado no se importan por CSV.
- **Proveedores de pago** — `paid_providers_allowed: false` en la config.
- **Planes premium** — solo free tier de cada proveedor.
- **Yahoo como fuente primaria** — `role: last_resort` en la config. Si aparece como `source` en un quote, significa que todos los demás fallaron.
- **Scraping HTML** — todos los providers usan APIs JSON o endpoints CSV públicos.
