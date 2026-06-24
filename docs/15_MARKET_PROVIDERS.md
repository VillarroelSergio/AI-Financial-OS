# 15 — Market Data Providers

## Resumen

AI Financial OS usa una arquitectura **multi-provider gratuita** para datos de mercado.
Todos los proveedores son gratuitos. No existe ningún proveedor de pago. No existe importación
manual por CSV para datos de mercado.

La app funciona **sin API keys** usando Stooq + Yahoo Finance. Si configuras API keys
gratuitas, amplías la cobertura con Alpha Vantage, Finnhub y FMP.

---

## Proveedores

### 1. StooqProvider — Fuente principal

| | |
|---|---|
| **API key** | No requerida |
| **Activado por defecto** | Sí |
| **Prioridad** | 1 (primero en la cadena) |
| **Cobertura** | Índices mundiales, forex, commodities (futuros), cripto básico, volatilidad |
| **Tipo de dato** | EOD (End of Day) — el más reciente disponible |
| **Freshness** | `eod`, `fresh` si el dato es de hace <30 min |
| **Límites** | Sin límite oficial. Throttle interno: 1 llamada/segundo |
| **Caché TTL** | 15 min (quotes), 24h (histórico) |

Stooq no promete datos en tiempo real. Para índices europeos durante horario de mercado,
el dato puede ser el EOD del día anterior o el intraday más reciente disponible.

### 2. YahooFinanceProvider — Fallback

| | |
|---|---|
| **API key** | No requerida |
| **Activado por defecto** | Sí |
| **Prioridad** | 99 (último recurso) |
| **Cobertura** | Universal (todos los asset types) |
| **Tipo de dato** | Delayed (retrasado, no garantizado) |
| **Freshness** | Siempre `delayed` o `unknown` — nunca `live` |
| **Nota** | Dato no garantizado. La UI mostrará badge "FB" (fallback). |

### 3. AlphaVantageProvider — Opcional

| | |
|---|---|
| **API key** | `ALPHA_VANTAGE_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Prioridad** | 3 |
| **Cobertura** | Acciones, forex, cripto |
| **Free tier** | 25 req/día (estándar) o 500 req/día (con registro de email) |
| **Rate limiter** | 5 req/min (interno) — nunca reintenta si alcanza el límite |

**Cómo obtener API key gratuita:**
1. Ir a https://www.alphavantage.co/support/#api-key
2. Registrarse con email
3. Añadir a `.env`: `ALPHA_VANTAGE_API_KEY=tu_clave`

### 4. FinnhubProvider — Opcional

| | |
|---|---|
| **API key** | `FINNHUB_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Prioridad** | 2 |
| **Cobertura** | Acciones USA, forex, cripto, perfiles, fundamentales |
| **Free tier** | 60 req/min |
| **Rate limiter** | 55 req/min (con buffer) — en 429, usa caché/fallback |
| **Freshness** | Puede ser `live` si el timestamp es reciente |

**Cómo obtener API key gratuita:**
1. Ir a https://finnhub.io/register
2. Registrarse
3. Añadir a `.env`: `FINNHUB_API_KEY=tu_clave`

### 5. FMPProvider — Opcional

| | |
|---|---|
| **API key** | `FMP_API_KEY` (obligatoria) |
| **Activado** | Solo si la variable de entorno está definida |
| **Prioridad** | 4 |
| **Cobertura** | Acciones, ETFs, perfiles de empresa, fundamentales, ratios |
| **Free tier** | 250 req/día |
| **Rate limiter** | Contador diario — no reintenta si alcanza el límite |
| **Freshness** | `eod` (dato EOD en free tier) |

**Cómo obtener API key gratuita:**
1. Ir a https://financialmodelingprep.com/register
2. Registrarse
3. Añadir a `.env`: `FMP_API_KEY=tu_clave`

---

## Routing

El `ProviderRouter` selecciona el proveedor según el tipo de activo:

| Tipo de activo | Orden de proveedores |
|---|---|
| Índices | Stooq → Finnhub → FMP → AlphaVantage → Yahoo |
| Acciones USA | Finnhub → FMP → AlphaVantage → Stooq → Yahoo |
| Acciones Europa | Stooq → FMP → Finnhub → Yahoo |
| Forex | Stooq → AlphaVantage → Finnhub → Yahoo |
| Cripto | Finnhub → AlphaVantage → FMP → Yahoo |
| Commodities | Stooq → Yahoo |
| Bonos | Stooq → Yahoo |
| Volatilidad | Stooq → Yahoo |

El router prueba los proveedores en orden. Si uno falla (error, sin datos, rate limit),
pasa al siguiente. Si todos fallan, devuelve el dato en caché marcado como `stale`.

---

## Caché (DuckDB)

Tablas en `data/analytics.duckdb`:

| Tabla | Descripción | TTL |
|---|---|---|
| `market_quotes_cache` | Último quote por símbolo (upsert) | Variable por tipo |
| `market_candles_cache` | OHLCV histórico (append) | 24h |
| `market_provider_logs` | Logs de fetch para debug | Sin TTL automático |
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
| `live` | Precio <5 min, mercado abierto | Solo Finnhub con timestamp reciente |
| `fresh` | Precio <15 min | Stooq o Finnhub con dato muy reciente |
| `delayed` | Precio retrasado 15–60 min | Yahoo Finance siempre; otros en delay |
| `eod` | Último cierre del mercado | Stooq (dato EOD), FMP free tier |
| `closed` | Mercado confirmado cerrado | Cuando el provider reporta mercado cerrado |
| `stale` | Caché vencida | Todos los proveedores fallaron, se usa caché antigua |
| `error` | Sin datos disponibles | Todos los proveedores fallaron y no hay caché |
| `unknown` | Sin información de frescura | Yahoo con dato sin timestamp |

**Regla importante:** la UI solo muestra "En vivo" cuando `freshness_status == "live"`.
Yahoo Finance nunca reporta `live`.

---

## Configuración

El archivo `backend/app/modules/market_data/config/market_data_config.yaml` contiene:
- Configuración de providers (habilitado, prioridad, API key env var)
- Orden de routing por tipo de activo
- TTL de caché
- Mappings de símbolos (36 activos, todos los providers)

---

## Añadir un nuevo símbolo

1. Abrir `market_data_config.yaml`
2. Añadir entrada en `symbol_mappings`:
```yaml
"TICKER_YAHOO":
  name: "Nombre del activo"
  category: "indices_eu"  # o cualquier MarketCategory
  asset_type: "index"     # index | stock | etf | forex | crypto | bond | commodity | volatility
  currency: "EUR"
  providers:
    stooq: "ticker_stooq"
    yahoo: "TICKER_YAHOO"
    finnhub: "TICKER_FINNHUB"  # opcional
```
3. El router lo cargará automáticamente en el siguiente arranque.

---

## Añadir un nuevo provider gratuito

1. Crear `backend/app/modules/market_data/providers/miprovider.py`
2. Extender `MarketDataProvider` (ABC en `providers/base.py`)
3. Implementar `supports()` y `get_quote()` — nunca deben lanzar excepciones
4. Añadir el provider a `providers/__init__.py`
5. Registrarlo en `ProviderRouter.__init__()` en `router.py`
6. Añadir configuración en `market_data_config.yaml`
7. Añadir al routing según los asset types que soporte

---

## Variables de entorno

```bash
# .env (en backend/)
ALPHA_VANTAGE_API_KEY=   # opcional — acciones, forex, cripto
FINNHUB_API_KEY=         # opcional — acciones USA, forex, cripto, fundamentales
FMP_API_KEY=             # opcional — acciones, ETFs, perfiles, fundamentales
```

Las keys vacías desactivan el proveedor correspondiente.
La app funciona completamente sin ninguna de estas keys.

---

## Lo que NO existe

- **ManualCsvProvider** — no existe ni existirá. Los datos de mercado no se importan por CSV.
- **Proveedores de pago** — `paid_providers_allowed: false` en la config.
- **Planes premium** — solo free tier de cada proveedor.
- **Scraping HTML** — Stooq usa endpoints CSV públicos, no scraping de HTML.
