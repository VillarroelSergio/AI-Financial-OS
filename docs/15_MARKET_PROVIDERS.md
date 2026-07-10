# 15 - Market Intelligence Providers

## Estado actual

La documentacion vigente de proveedores corresponde al modulo:

```txt
backend/app/modules/market_intelligence/
```

El diseno anterior basado en `market_data`, `ProviderRouter`, `ConsensusEngine`,
`RequestBudget`, `/api/markets/*` y `/api/economy/*` ya no es la ruta activa del
backend. Esos conceptos solo deben consultarse como historico.

## Arquitectura

```txt
Catalog YAML
  -> CatalogLoader
  -> ProviderOrchestrator
  -> adapters por region/proveedor
  -> QualityEngine
  -> Repository SQLite (`mi_*`)
  -> API `/api/market-intelligence/*`
  -> UI y AI datasheet
```

## Catalogo

Los indicadores se declaran en:

```txt
backend/app/modules/market_intelligence/catalog/yaml/
```

Archivos principales:

| Archivo | Cobertura |
|---|---|
| `macro_spain.yaml` | Indicadores de Espana |
| `macro_europe.yaml` | Eurozona / Europa |
| `macro_usa.yaml` | EEUU |
| `indices.yaml` | Indices de mercado |
| `forex.yaml` | Divisas |
| `bonds.yaml` | Bonos |
| `commodities.yaml` | Commodities |
| `crypto.yaml` | Cripto |
| `news.yaml` | Noticias |

Cada item del catalogo define proveedor primario, secundarios/fallbacks, frecuencia,
prioridad y si debe entrar en contexto de IA.

## Adapters

Los adapters activos estan en:

```txt
backend/app/modules/market_intelligence/ingestion/adapters/
```

Familias:

| Carpeta | Ejemplos |
|---|---|
| `spain/` | BDE, INE, CNMV, BME, Tesoro, REE, AEMET |
| `europe/` | ECB, Eurostat, OECD, BIS, Eur-Lex |
| `usa/` | FRED, BEA, BLS, Treasury, Census, EIA, EDGAR |
| `global_/` | IMF, World Bank, Stooq, Finnhub, FMP, Polygon, CoinGecko |
| `rss/` | Feeds de noticias |

## Calidad

`QualityEngine` calcula un score por resultado antes de persistirlo. El objetivo es que
la UI y la IA distingan datos buenos, incompletos, viejos o procedentes de fallback.

Checks principales:

| Check | Peso |
|---|---:|
| Freshness | 0.30 |
| Completeness | 0.20 |
| Validity | 0.25 |
| Outlier | 0.15 |
| Provider reliability | 0.10 |

## Persistencia

Market Intelligence persiste en **SQLite WAL** (`data/market_intelligence.db`) mediante
`app.modules.market_intelligence.storage.db.get_conn()` (ECO-3b; antes DuckDB).
Las tablas del modulo usan prefijo `mi_*`.

Reglas importantes:

- Usar `get_conn()` (conexion unica compartida, WAL, autocommit) — no abrir `sqlite3.connect()` directo.
- Usar escrituras idempotentes con checksums cuando aplique.
- Para lecturas latest, usar subconsulta `ROW_NUMBER() OVER (...)` con `rn = 1` (SQLite no tiene `QUALIFY`).
- No consultar proveedores live desde la IA; la IA consume datasheets y endpoints backend.
- WAL admite lectores concurrentes con el escritor, asi que no hay fallback a memoria ni
  aviso de almacenamiento: `ingest-status` reporta siempre `storage: file`.

Notas de adapters:

- `world_bank`: PIB de España via `NY.GDP.MKTP.CN` (moneda local = EUR), escalado a
  "EUR bn" antes de persistir, alineado con el `unit` del catalogo.
- `coingecko`: una unica llamada batcheada (cache 60 s) para todos los coins; sin
  cache, la cuarta peticion consecutiva del free tier devolvia 429 y `xrp` quedaba
  sin datos (no tiene fallback: Stooq solo cubre indices).
- `stooq`: si el CSV esta bloqueado usa fallback interno a Yahoo Chart; el resultado
  es `success=True` con `error` informativo.
- `fred`: cada serie declara su unidad real (`_SERIES_UNITS`): INDPRO y UMCSENT son
  indices, no porcentajes; M2SL es "USD bn".

Guard de persistencia (`repository._record_matches_catalog`):

- Un registro solo se persiste si su tipo coincide con la categoria del item del
  catalogo (macro→MacroIndicator, bonds→YieldCurvePoint/BondYield, etc.). Evita que
  un fallback generico (FRED devolviendo Fed Funds) contamine bonos o commodities
  con valores clonados.
- Para bonos, la maturity del registro debe coincidir con la codificada en el id
  (`us_2y` → `2Y`); los adapters de curva devuelven las 8 maturities completas.
- `purge_mismatched_macro_observations()` limpia la contaminacion historica al
  arrancar la ingesta (idempotente, lanzada desde `launch_startup_ingest`).

## API activa

Endpoints registrados bajo `/api/market-intelligence`:

| Endpoint | Uso |
|---|---|
| `GET /snapshot/macro` | Macro por region |
| `GET /snapshot/market` | Indices, cripto y commodities |
| `GET /snapshot/forex` | Divisas |
| `GET /snapshot/bonds` | Bonos |
| `GET /snapshot/news` | Noticias |
| `GET /personal-impact` | Comparativas personales |
| `GET /ingest-status` | Estado de ingesta |
| `GET /ai-datasheet` | Contexto compacto para IA |

## Salidas generadas

Los comandos de snapshot/datasheet pueden escribir en:

```txt
output/market-intelligence/
```

Estas salidas son artefactos generados. No deben usarse como documentacion fuente ni
commitearse salvo decision explicita.

## Legado

`market-data-poc/` conserva codigo y notas del POC. Sirve para comparar adapters o
recuperar ideas, pero la documentacion operacional debe apuntar al modulo backend
`market_intelligence`.
