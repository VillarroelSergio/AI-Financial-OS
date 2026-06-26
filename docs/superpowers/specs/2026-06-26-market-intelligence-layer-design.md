# Design: AI Financial OS — Fase 5.5 Market Intelligence Layer

**Date:** 2026-06-26
**Phase:** 5.5 — Market Intelligence Layer
**Approach chosen:** Opción B — Arquitectura por capas con boundaries claros

---

## Objetivo

Convertir la POC de datos de mercado (`market-data-poc/`) en una capa persistente, controlada y reutilizable integrada en el backend FastAPI. El sistema parte de un catálogo interno que define exactamente qué datos se quieren, con qué frecuencia y desde qué provider. Los adapters validados del POC se migran sin reescritura. La arquitectura nueva garantiza trazabilidad completa, quality scoring y un AI Datasheet como único punto de contacto entre la IA local y los datos externos.

---

## Decisiones arquitectónicas

| Decisión | Elección | Razón |
|---|---|---|
| Ubicación del módulo | `backend/app/modules/market_intelligence/` | Coherente con el patrón del backend existente |
| Migración de adapters | Copiar todo desde POC, reemplazar `economic_data` | El POC está probado; el módulo antiguo no vale |
| Storage de mercado | DuckDB exclusivamente | Diseñado para séries temporales; ya existe en el proyecto |
| Storage de usuario | SQLite sin cambios | No se toca la base de datos del usuario |
| Scheduler | Solo CLI en Fase 5.5 | Sin APScheduler; el usuario lanza updates manualmente |
| Frontend | Sin cambios en Fase 5.5 | Los endpoints `/api/economic-data/*` siguen funcionando vía proxy |

---

## Estructura de módulos

```
backend/app/modules/market_intelligence/
│
├── catalog/                        ← Capa 1: fuente de verdad
│   ├── loader.py                   ← carga y valida YAMLs
│   ├── schemas.py                  ← CatalogItem, ProviderMapping (Pydantic)
│   └── yaml/                       ← migrado desde market-data-poc/catalog/
│       ├── macro_spain.yaml
│       ├── macro_europe.yaml
│       ├── macro_usa.yaml
│       ├── bonds.yaml
│       ├── forex.yaml
│       ├── indices.yaml
│       ├── commodities.yaml
│       ├── crypto.yaml
│       └── news.yaml
│
├── ingestion/                      ← Capa 2: fetch de datos externos
│   ├── orchestrator.py             ← primary → secondary → fallback con trazabilidad
│   ├── runner.py                   ← ejecuta ingesta filtrada por category/priority
│   └── adapters/                   ← migrado desde market-data-poc/adapters/
│       ├── base.py
│       ├── europe/
│       ├── global_/
│       ├── spain/
│       ├── usa/
│       └── rss/
│
├── quality/                        ← Capa 3: validación y scoring
│   ├── engine.py                   ← orquesta checks, produce QualityResult
│   ├── checks.py                   ← freshness, completeness, validity, outlier, reliability
│   └── schemas.py                  ← QualityResult
│
├── storage/                        ← Capa 4: persistencia DuckDB
│   ├── migrations.py               ← CREATE TABLE IF NOT EXISTS (DDL directo DuckDB)
│   ├── repository.py               ← reads + writes para todas las tablas
│   └── snapshot.py                 ← genera y lee snapshots JSON
│
├── api/                            ← Capa 5: interfaz de consumo
│   ├── routes.py                   ← FastAPI router (endpoints internos)
│   ├── service.py                  ← get_market_snapshot(), get_ai_datasheet(), etc.
│   └── schemas.py                  ← MarketSnapshotOut, AiDatasheetOut, etc.
│
├── ai/
│   └── datasheet.py                ← genera JSON compacto para la IA local
│
└── cli/
    └── commands.py                 ← comandos market:* registrados en run_poc.py
```

### Boundaries entre capas

- `catalog` no depende de ninguna otra capa. Es solo lectura de YAMLs.
- `ingestion` conoce solo `catalog` (lee `CatalogItem`) y devuelve dicts raw. No escribe a DuckDB.
- `quality` recibe dicts normalizados y devuelve `QualityResult`. No conoce DuckDB ni providers.
- `storage` solo lee/escribe DuckDB. No llama a providers ni a quality engine.
- `api/service.py` orquesta `storage` para responder. Nunca llama a providers directamente.
- `ai/datasheet.py` consume únicamente `api/service.py`. Cero acceso a Internet.
- La IA local consume únicamente `get_ai_datasheet()`. Sin acceso directo a ninguna capa inferior.

---

## Schema DuckDB

Todas las tablas de market intelligence viven en DuckDB. Sin SQLAlchemy — DDL ejecutado por `storage/migrations.py`.

### Tablas de configuración

```sql
-- Proveedores registrados con scores de calidad
market_providers (
    id TEXT PRIMARY KEY,
    name TEXT,
    region TEXT,
    category TEXT,
    status TEXT,              -- ok | degraded | fallback | discarded
    coverage_score FLOAT,
    quality_score FLOAT,
    integration_score FLOAT,
    reliability_score FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Cada indicador/activo del catálogo
market_catalog_items (
    id TEXT PRIMARY KEY,
    name TEXT,
    category TEXT,
    subcategory TEXT,
    country TEXT,
    region TEXT,
    frequency TEXT,           -- realtime | daily | weekly | monthly | quarterly | yearly
    priority TEXT,            -- critical | high | medium | low
    dashboard_visible BOOLEAN,
    ai_visible BOOLEAN,
    historical_window TEXT,   -- 5y | 10y | etc.
    retention_policy TEXT,    -- forever | 5y | 3y | etc.
    model_type TEXT,          -- MacroIndicator | CurrencyRate | BondYield | etc.
    unit TEXT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Mapping provider → catalog_item con rol y configuración
provider_mappings (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    provider_id TEXT,
    role TEXT,                -- primary | secondary | fallback
    provider_symbol TEXT,
    provider_series_id TEXT,
    endpoint TEXT,
    priority_order INTEGER,
    enabled BOOLEAN,
    notes TEXT
)
```

### Tablas de datos

```sql
-- Payload bruto con checksum para idempotencia
raw_market_records (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    provider_id TEXT,
    raw_payload_json TEXT,
    source_url TEXT,
    retrieved_at TIMESTAMP,
    ingestion_run_id TEXT,
    checksum TEXT             -- MD5 del payload; evita reescrituras en re-ejecuciones
)

-- Registro normalizado universal con trazabilidad completa
normalized_market_records (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    provider_id TEXT,
    model_type TEXT,
    observed_at TIMESTAMP,
    value_numeric FLOAT,
    value_text TEXT,
    currency TEXT,
    unit TEXT,
    period TEXT,
    frequency TEXT,
    metadata_json TEXT,
    source_url TEXT,
    retrieved_at TIMESTAMP,
    confidence_score FLOAT,
    quality_score FLOAT,
    created_at TIMESTAMP
)

-- Precio actual de índices, cripto, commodities, forex
market_quotes (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    symbol TEXT,
    asset_type TEXT,
    price FLOAT,
    change_pct FLOAT,
    currency TEXT,
    market_status TEXT,
    observed_at TIMESTAMP,
    provider_id TEXT,
    quality_score FLOAT
)

-- OHLCV diario por símbolo
historical_prices (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    symbol TEXT,
    date DATE,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    currency TEXT,
    provider_id TEXT,
    quality_score FLOAT
)

-- Series macro (inflación, PIB, desempleo, tipos, etc.)
macro_observations (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    indicator_id TEXT,
    country TEXT,
    period TEXT,
    frequency TEXT,
    value FLOAT,
    unit TEXT,
    provider_id TEXT,
    quality_score FLOAT,
    source_url TEXT,
    retrieved_at TIMESTAMP
)

-- Tipos de cambio diarios
currency_rates (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    base_currency TEXT,
    quote_currency TEXT,
    rate FLOAT,
    date DATE,
    provider_id TEXT,
    quality_score FLOAT
)

-- Rendimientos de bonos soberanos
bond_yields (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    country TEXT,
    maturity TEXT,
    yield_value FLOAT,
    date DATE,
    currency TEXT,
    issuer TEXT,
    instrument_type TEXT,
    provider_id TEXT,
    quality_score FLOAT
)

-- Materias primas
commodities (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    symbol TEXT,
    name TEXT,
    price FLOAT,
    unit TEXT,
    currency TEXT,
    observed_at TIMESTAMP,
    provider_id TEXT,
    quality_score FLOAT
)

-- Perfil estático de empresas
company_profiles (
    id TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    sector TEXT,
    industry TEXT,
    market_cap FLOAT,
    exchange TEXT,
    isin TEXT,
    figi TEXT,
    country TEXT,
    provider_id TEXT,
    quality_score FLOAT,
    updated_at TIMESTAMP
)

-- Noticias financieras
news_items (
    id TEXT PRIMARY KEY,
    title TEXT,
    published_at TIMESTAMP,
    source_name TEXT,
    url TEXT,
    category TEXT,
    related_asset TEXT,
    sentiment_score FLOAT,
    importance_score FLOAT,
    provider_id TEXT,
    created_at TIMESTAMP
)
```

### Tablas de control y calidad

```sql
-- Log de salud por provider por ejecución
provider_health_logs (
    id TEXT PRIMARY KEY,
    provider_id TEXT,
    catalog_item_id TEXT,
    status TEXT,              -- success | error | timeout | degraded
    latency_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP
)

-- Resultado de cada check de calidad
data_quality_checks (
    id TEXT PRIMARY KEY,
    catalog_item_id TEXT,
    provider_id TEXT,
    check_type TEXT,          -- freshness | completeness | validity | outlier | reliability
    status TEXT,              -- pass | warn | fail
    details_json TEXT,
    created_at TIMESTAMP
)

-- AI Datasheets generados
ai_market_datasheets (
    id TEXT PRIMARY KEY,
    snapshot_date DATE,
    scope TEXT,               -- daily | weekly | monthly | portfolio
    datasheet_json TEXT,
    quality_score FLOAT,
    generated_at TIMESTAMP
)
```

---

## Flujo de ingesta

```
CatalogItem
    ↓
runner.py — filtra por category/priority, itera items
    ↓
orchestrator.py — intenta provider_primary
    ↓ falla → provider_secondary
    ↓ falla → provider_fallback
    ↓ falla todo → registra error en provider_health_logs, continúa con siguiente item
    ↓
raw payload (dict)
    ↓ compara checksum con último guardado → si igual, skip (idempotencia)
    ↓ guarda en raw_market_records
    ↓
adapter.normalize() → dict normalizado
    ↓
quality/engine.py → QualityResult (quality_score 0.0–1.0)
    ↓
storage/repository.py → escribe en tabla especializada + normalized_market_records
    ↓
provider_health_logs → latencia, éxito/fallo, provider usado
```

---

## Quality Engine

`quality/engine.py` calcula cinco sub-scores por dato normalizado:

| Check | Descripción | Peso |
|---|---|---|
| `freshness` | ¿El dato llega dentro de la ventana esperada según `frequency`? | 0.30 |
| `completeness` | ¿Están presentes todos los campos obligatorios? | 0.20 |
| `validity` | Valor nulo, negativo donde no aplica, moneda o fecha inválida | 0.25 |
| `outlier` | ¿El valor se desvía más de 3σ de la media histórica reciente? | 0.15 |
| `provider_reliability` | Score histórico del provider de `provider_health_logs` | 0.10 |

`final_quality_score = suma ponderada` de los cinco checks.

Si hay múltiples providers para el mismo `catalog_item` en el mismo periodo, `engine.py` calcula `cross_provider_variance`. Varianza > 5% genera `warn` en `data_quality_checks` y penaliza ambos scores.

Los pesos son constantes editables en `quality/checks.py`.

---

## API interna

### Funciones de `api/service.py`

```python
get_market_snapshot() -> MarketSnapshotOut
    # índices, cripto, commodities, forex — para dashboard Market Overview

get_macro_snapshot() -> MacroSnapshotOut
    # inflación, PIB, desempleo, tipos — por región ES/EA/US

get_forex_snapshot() -> ForexSnapshotOut
    # tipos de cambio actuales

get_bond_snapshot() -> BondSnapshotOut
    # curva de tipos soberanos US + España + Alemania

get_news_snapshot() -> NewsSnapshotOut
    # últimas noticias por categoría

get_ai_datasheet(scope: str = "daily") -> AiDatasheetOut
    # JSON compacto para la IA local
```

Cada función devuelve datos desde DuckDB vía `storage/repository.py`. Los datos con `quality_score < 0.5` se incluyen en `warnings[]` del response Pydantic correspondiente.

Los endpoints FastAPI de `api/routes.py` son wrappers sin lógica sobre estas funciones.

### Compatibilidad con `economic_data`

`modules/economic_data/routes.py` se convierte en proxy temporal que llama a `market_intelligence/api/service.py`. El frontend no necesita cambios.

---

## AI Datasheet

`ai/datasheet.py` genera el único contexto externo consumible por la IA local:

```json
{
  "generated_at": "2026-06-26T12:00:00Z",
  "quality_score": 0.94,
  "macro": {
    "spain":    { "inflation": {"value": 2.8, "period": "2026-05", "provider": "INE", "quality_score": 0.96}, ... },
    "eurozone": { ... },
    "usa":      { ... }
  },
  "markets": {
    "indices":     [{"id": "sp500", "value": 5400.2, "change_pct": 0.3, ...}],
    "commodities": [...],
    "crypto":      [...]
  },
  "forex":  {"eur_usd": {"rate": 1.082, "date": "2026-06-26", ...}},
  "bonds":  {"us_10y": {"yield": 4.32, "date": "2026-06-26", ...}},
  "news":   [{"title": "...", "category": "macro", "published_at": "..."}],
  "sources": [{"provider": "INE", "quality_score": 0.96, "last_updated": "..."}],
  "warnings": []
}
```

Scope `daily`: todos los `CatalogItem` con `ai: true`. Scope `portfolio`: reservado para Fase 6 (cruce con datos del usuario).

El datasheet se persiste en `ai_market_datasheets` tras cada generación.

---

## Comandos CLI

Registrados en `run_poc.py` (o equivalente en el backend):

```bash
python run_poc.py market:catalog                              # lista todos los items del catálogo
python run_poc.py market:catalog:validate                    # valida YAMLs contra CatalogItem schema

python run_poc.py market:intelligence:init-db                # crea todas las tablas DuckDB

python run_poc.py market:intelligence:update                 # ingesta completa
python run_poc.py market:intelligence:update --category macro
python run_poc.py market:intelligence:update --priority critical

python run_poc.py market:intelligence:quality                # reporte de calidad por item y provider
python run_poc.py market:intelligence:snapshot               # genera market_intelligence_snapshot.json
python run_poc.py market:intelligence:datasheet              # genera ai_datasheet_daily.json
```

Cada comando imprime al finalizar: items procesados, éxitos, fallos, quality score promedio, providers usados.

---

## Migración del módulo `economic_data`

| Elemento actual | Acción |
|---|---|
| `providers/fred_provider.py` | Reemplazado por `ingestion/adapters/usa/fred.py` (del POC) |
| `providers/stooq_macro_provider.py` | Reemplazado por `ingestion/adapters/global_/stooq.py` (del POC) |
| `repository.py` | Reemplazado por `storage/repository.py` (DuckDB) |
| `service.py` | Reemplazado por `api/service.py` |
| `routes.py` | Convertido en proxy temporal hacia `market_intelligence/api/service.py` |
| `schemas.py` | `MacroSnapshotOut`, `IndicatorOut` reutilizados/extendidos en `api/schemas.py` |
| Tabla SQLite `macro_indicators` | Se mantiene sin modificar; la lectura se migra gradualmente |

---

## Reportes generados

```
market_intelligence_catalog_report.md   ← lista de items, providers, frecuencias
market_intelligence_quality_report.md   ← quality scores por item y provider
market_intelligence_snapshot.json       ← snapshot completo de mercado
ai_datasheet_daily.json                 ← datasheet para la IA (scope daily)
```

---

## Criterios de aceptación

```
1.  Existe Market Data Catalog editable (YAMLs validados).
2.  Existe Provider Mapping por catalog_item.
3.  La ingesta solo descarga lo que define el catálogo.
4.  Los datos se actualizan desde el catálogo (runner filtra por category/priority).
5.  Se persisten raw_market_records con checksum (idempotencia).
6.  Se persisten normalized_market_records con trazabilidad completa.
7.  Se calculan quality_scores para cada registro.
8.  Se generan snapshots JSON desde DuckDB.
9.  Se genera AI Datasheet con scope daily.
10. Dashboard puede consumir datos vía get_market_snapshot() y get_macro_snapshot().
11. IA local puede consumir solo get_ai_datasheet(). Sin acceso directo a Internet.
12. Providers problemáticos (BDE, CNMV) no bloquean la arquitectura — marcados como degraded.
13. Los endpoints /api/economic-data/* siguen funcionando (compatibilidad vía proxy).
```

---

## Fuera de scope en Fase 5.5

- APScheduler / daemon de actualización automática (Fase 6)
- Cruce con datos del usuario / análisis de portfolio (Fase 6)
- AI Datasheet scope `portfolio` (Fase 6)
- Scraping de providers problemáticos (BDE, CNMV) — solo marcar como degraded
- Frontend nuevo para market intelligence (Fase 6)
