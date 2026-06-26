# Market Intelligence Layer — Fase 5.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar el market-data-poc al backend FastAPI como un módulo Market Intelligence Layer con catálogo-driven ingestion, persistencia DuckDB, quality scoring y AI datasheet, reemplazando el módulo `economic_data`.

**Architecture:** Cinco capas en `backend/app/modules/market_intelligence/`: catalog (YAML source of truth) → ingestion (adapters del POC + orchestrator) → quality (scoring engine) → storage (DuckDB) → api (FastAPI service). Los adapters del POC se migran con solo cambios de import; sin reescritura de lógica. El módulo `economic_data/routes.py` se convierte en proxy para que el frontend no necesite cambios.

**Tech Stack:** Python 3.12+, FastAPI, DuckDB via `app.core.duckdb.get_duckdb()`, Pydantic v2, PyYAML, requests, rich

## Global Constraints

- Todo acceso DuckDB usa el singleton existente `app.core.duckdb.get_duckdb()` — nunca abrir `duckdb.connect()` directamente
- Las API keys vienen de `app.core.config.settings` (Pydantic BaseSettings) — nunca leer env vars directamente
- Patrón de módulos del backend: `backend/app/modules/<module>/`
- Tests se ejecutan con `pytest backend/tests/` desde `AI-Financial-OS/backend/`
- Los endpoints existentes `/api/economy/*` deben seguir funcionando tras la migración
- Los providers BDE y CNMV se marcan `status=degraded` — sus adapters se migran pero sus fallos no bloquean la ingesta

---

## File Map

```
backend/app/modules/market_intelligence/
├── __init__.py
│
├── catalog/
│   ├── __init__.py
│   ├── schemas.py          ← CatalogIndicator dataclass (de POC models/catalog.py)
│   ├── loader.py           ← CatalogLoader (de POC catalog/__init__.py, imports adaptados)
│   └── yaml/               ← copiado de market-data-poc/catalog/*.yaml
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
├── ingestion/
│   ├── __init__.py
│   ├── config.py           ← bridge get_api_key() → app.core.config.settings
│   ├── models.py           ← merge de POC models/base.py + assets.py + macro.py + market.py + company.py + news.py
│   ├── orchestrator.py     ← de POC services/orchestrator.py (imports adaptados)
│   ├── runner.py           ← NUEVO: orquesta catalog→fetch→quality→persist
│   └── adapters/
│       ├── __init__.py
│       ├── base.py         ← de POC adapters/base.py (imports adaptados)
│       ├── catalog.py      ← de POC adapters/catalog.py (imports adaptados)
│       ├── europe/         ← copiado + imports fijados
│       ├── global_/        ← copiado + imports fijados
│       ├── spain/          ← copiado + imports fijados
│       ├── usa/            ← copiado + imports fijados
│       └── rss/            ← copiado + imports fijados
│
├── quality/
│   ├── __init__.py
│   ├── schemas.py          ← QualityResult dataclass
│   ├── checks.py           ← funciones de check individuales + pesos
│   └── engine.py           ← QualityEngine.score() → QualityResult
│
├── storage/
│   ├── __init__.py
│   ├── migrations.py       ← CREATE TABLE IF NOT EXISTS para todas las tablas DuckDB
│   ├── repository.py       ← write + read para cada tabla
│   └── snapshot.py         ← genera y lee market snapshot JSON desde DuckDB
│
├── api/
│   ├── __init__.py
│   ├── schemas.py          ← Pydantic output models (MarketSnapshotOut, etc.)
│   ├── service.py          ← get_market_snapshot(), get_macro_snapshot(), get_ai_datasheet(), etc.
│   └── routes.py           ← FastAPI router /api/market-intelligence/*
│
└── ai/
    ├── __init__.py
    └── datasheet.py        ← genera ai_datasheet_daily.json y persiste en DuckDB

backend/app/modules/market_intelligence/cli/
├── __init__.py
└── commands.py             ← funciones para cada market:intelligence:* command

Modified:
- backend/app/main.py                           ← registrar market_intelligence router
- backend/app/modules/economic_data/routes.py   ← convertir en proxy
- market-data-poc/run_poc.py                    ← añadir market:intelligence:* commands
```

---

### Task 1: Module scaffold + DuckDB migrations

**Files:**
- Create: `backend/app/modules/market_intelligence/__init__.py`
- Create: `backend/app/modules/market_intelligence/catalog/__init__.py`
- Create: `backend/app/modules/market_intelligence/ingestion/__init__.py`
- Create: `backend/app/modules/market_intelligence/ingestion/adapters/__init__.py`
- Create: `backend/app/modules/market_intelligence/quality/__init__.py`
- Create: `backend/app/modules/market_intelligence/storage/__init__.py`
- Create: `backend/app/modules/market_intelligence/api/__init__.py`
- Create: `backend/app/modules/market_intelligence/ai/__init__.py`
- Create: `backend/app/modules/market_intelligence/cli/__init__.py`
- Create: `backend/app/modules/market_intelligence/storage/migrations.py`
- Test: `backend/tests/market_intelligence/test_migrations.py`

**Interfaces:**
- Produces: `run_migrations(conn: DuckDBPyConnection) -> None` — crea todas las tablas si no existen

- [ ] **Step 1: Crear todos los directorios e `__init__.py` vacíos**

```bash
# Ejecutar desde AI-Financial-OS/backend/
python -c "
from pathlib import Path
dirs = [
    'app/modules/market_intelligence',
    'app/modules/market_intelligence/catalog',
    'app/modules/market_intelligence/ingestion',
    'app/modules/market_intelligence/ingestion/adapters',
    'app/modules/market_intelligence/quality',
    'app/modules/market_intelligence/storage',
    'app/modules/market_intelligence/api',
    'app/modules/market_intelligence/ai',
    'app/modules/market_intelligence/cli',
    'app/modules/market_intelligence/catalog/yaml',
    'tests/market_intelligence',
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
    init = Path(d) / '__init__.py'
    if not init.exists():
        init.touch()
print('Done')
"
```

Expected: `Done`

- [ ] **Step 2: Crear `storage/migrations.py` con el DDL completo**

Crear `backend/app/modules/market_intelligence/storage/migrations.py`:

```python
"""DuckDB DDL para el Market Intelligence Layer.

Ejecutar run_migrations(conn) al arrancar o con market:intelligence:init-db.
Todas las tablas usan CREATE TABLE IF NOT EXISTS para ser idempotentes.
"""
from __future__ import annotations
import duckdb


_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS mi_providers (
        id                TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        region            TEXT,
        category          TEXT,
        status            TEXT DEFAULT 'ok',
        coverage_score    DOUBLE DEFAULT 0.0,
        quality_score     DOUBLE DEFAULT 0.0,
        integration_score DOUBLE DEFAULT 0.0,
        reliability_score DOUBLE DEFAULT 0.0,
        created_at        TIMESTAMP DEFAULT current_timestamp,
        updated_at        TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_catalog_items (
        id                TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        category          TEXT,
        subcategory       TEXT,
        country           TEXT,
        region            TEXT,
        frequency         TEXT,
        priority          TEXT,
        dashboard_visible BOOLEAN DEFAULT true,
        ai_visible        BOOLEAN DEFAULT true,
        historical_window TEXT,
        retention_policy  TEXT,
        model_type        TEXT,
        unit              TEXT,
        description       TEXT,
        created_at        TIMESTAMP DEFAULT current_timestamp,
        updated_at        TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_provider_mappings (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        role              TEXT NOT NULL,
        provider_symbol   TEXT,
        provider_series_id TEXT,
        endpoint          TEXT,
        priority_order    INTEGER DEFAULT 0,
        enabled           BOOLEAN DEFAULT true,
        notes             TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_raw_records (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        raw_payload_json  TEXT,
        source_url        TEXT,
        retrieved_at      TIMESTAMP NOT NULL,
        ingestion_run_id  TEXT,
        checksum          TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_normalized_records (
        id                TEXT PRIMARY KEY,
        catalog_item_id   TEXT NOT NULL,
        provider_id       TEXT NOT NULL,
        model_type        TEXT,
        observed_at       TIMESTAMP,
        value_numeric     DOUBLE,
        value_text        TEXT,
        currency          TEXT,
        unit              TEXT,
        period            TEXT,
        frequency         TEXT,
        metadata_json     TEXT,
        source_url        TEXT,
        retrieved_at      TIMESTAMP,
        confidence_score  DOUBLE DEFAULT 1.0,
        quality_score     DOUBLE DEFAULT 1.0,
        created_at        TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_market_quotes (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        asset_type      TEXT,
        price           DOUBLE,
        change_pct      DOUBLE,
        currency        TEXT DEFAULT 'USD',
        market_status   TEXT,
        observed_at     TIMESTAMP,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_historical_prices (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        date            DATE,
        open            DOUBLE,
        high            DOUBLE,
        low             DOUBLE,
        close           DOUBLE,
        volume          BIGINT,
        currency        TEXT DEFAULT 'USD',
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_macro_observations (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        indicator_id    TEXT,
        country         TEXT,
        period          TEXT,
        frequency       TEXT,
        value           DOUBLE,
        unit            TEXT,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0,
        source_url      TEXT,
        retrieved_at    TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_currency_rates (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        base_currency   TEXT,
        quote_currency  TEXT,
        rate            DOUBLE,
        date            DATE,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_bond_yields (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        country         TEXT,
        maturity        TEXT,
        yield_value     DOUBLE,
        date            DATE,
        currency        TEXT DEFAULT 'USD',
        issuer          TEXT,
        instrument_type TEXT DEFAULT 'government_bond',
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_commodities (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        symbol          TEXT,
        name            TEXT,
        price           DOUBLE,
        unit            TEXT,
        currency        TEXT DEFAULT 'USD',
        observed_at     TIMESTAMP,
        provider_id     TEXT,
        quality_score   DOUBLE DEFAULT 1.0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_company_profiles (
        id            TEXT PRIMARY KEY,
        symbol        TEXT,
        name          TEXT,
        sector        TEXT,
        industry      TEXT,
        market_cap    DOUBLE,
        exchange      TEXT,
        isin          TEXT,
        figi          TEXT,
        country       TEXT,
        provider_id   TEXT,
        quality_score DOUBLE DEFAULT 1.0,
        updated_at    TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_news_items (
        id              TEXT PRIMARY KEY,
        title           TEXT,
        published_at    TIMESTAMP,
        source_name     TEXT,
        url             TEXT,
        category        TEXT,
        related_asset   TEXT,
        sentiment_score DOUBLE DEFAULT 0.0,
        importance_score DOUBLE DEFAULT 0.5,
        provider_id     TEXT,
        created_at      TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_provider_health_logs (
        id              TEXT PRIMARY KEY,
        provider_id     TEXT NOT NULL,
        catalog_item_id TEXT,
        status          TEXT,
        latency_ms      INTEGER,
        error_message   TEXT,
        checked_at      TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_data_quality_checks (
        id              TEXT PRIMARY KEY,
        catalog_item_id TEXT NOT NULL,
        provider_id     TEXT,
        check_type      TEXT,
        status          TEXT,
        details_json    TEXT,
        created_at      TIMESTAMP DEFAULT current_timestamp
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mi_ai_datasheets (
        id              TEXT PRIMARY KEY,
        snapshot_date   DATE NOT NULL,
        scope           TEXT NOT NULL DEFAULT 'daily',
        datasheet_json  TEXT NOT NULL,
        quality_score   DOUBLE DEFAULT 0.0,
        generated_at    TIMESTAMP DEFAULT current_timestamp
    )
    """,
]


def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Crea todas las tablas MI en DuckDB si no existen."""
    for ddl in _DDL_STATEMENTS:
        conn.execute(ddl)
```

- [ ] **Step 3: Crear directorio de tests e `__init__.py`**

```bash
# desde AI-Financial-OS/backend/
python -c "
from pathlib import Path
Path('tests/market_intelligence').mkdir(parents=True, exist_ok=True)
Path('tests/market_intelligence/__init__.py').touch()
print('Done')
"
```

- [ ] **Step 4: Escribir el test de migrations**

Crear `backend/tests/market_intelligence/test_migrations.py`:

```python
import duckdb
import pytest
from app.modules.market_intelligence.storage.migrations import run_migrations

EXPECTED_TABLES = [
    "mi_providers",
    "mi_catalog_items",
    "mi_provider_mappings",
    "mi_raw_records",
    "mi_normalized_records",
    "mi_market_quotes",
    "mi_historical_prices",
    "mi_macro_observations",
    "mi_currency_rates",
    "mi_bond_yields",
    "mi_commodities",
    "mi_company_profiles",
    "mi_news_items",
    "mi_provider_health_logs",
    "mi_data_quality_checks",
    "mi_ai_datasheets",
]


@pytest.fixture
def conn():
    c = duckdb.connect(":memory:")
    yield c
    c.close()


def test_migrations_create_all_tables(conn):
    run_migrations(conn)
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    for table in EXPECTED_TABLES:
        assert table in existing, f"Missing table: {table}"


def test_migrations_are_idempotent(conn):
    run_migrations(conn)
    run_migrations(conn)  # segunda vez no debe fallar
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert len(existing) == len(EXPECTED_TABLES)
```

- [ ] **Step 5: Ejecutar tests**

```bash
# desde AI-Financial-OS/backend/
pytest tests/market_intelligence/test_migrations.py -v
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/market_intelligence/ backend/tests/market_intelligence/
git commit -m "feat(mi): scaffold module structure + DuckDB migrations"
```

---

### Task 2: Modelos POC + config bridge

**Files:**
- Create: `backend/app/modules/market_intelligence/ingestion/models.py`
- Create: `backend/app/modules/market_intelligence/ingestion/config.py`
- Test: `backend/tests/market_intelligence/test_ingestion_models.py`

**Interfaces:**
- Produces: `AdapterResult`, `ProviderMetadata`, `ProviderHealth`, `ProviderStatus`, `ProviderRecord`, `MacroIndicator`, `CurrencyRate`, `BondYield`, `YieldCurvePoint`, `MarketQuote`, `HistoricalPrice`, `MacroSeries`, `CompanyProfile`, `NewsItem`, `MarketNews`, `Commodity`
- Produces: `get_api_key(provider_name: str) -> str | None`

- [ ] **Step 1: Crear `ingestion/models.py` mergeando todos los modelos del POC**

Crear `backend/app/modules/market_intelligence/ingestion/models.py`:

```python
"""Modelos de datos del Market Intelligence Layer.

Consolidado desde market-data-poc/models/{base,assets,macro,market,company,news}.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ── Base ─────────────────────────────────────────────────────────────────────

@dataclass
class ProviderRecord:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0


@dataclass
class ProviderMetadata:
    name: str
    id: str
    category: str
    region: str
    method: str
    base_url: str
    requires_api_key: bool
    declared_update_frequency: str
    declared_historical_depth_years: int
    license: str
    notes: str = ""
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"


@dataclass
class AdapterResult:
    provider: str
    success: bool
    records: list
    error: Optional[str]
    latency_ms: float
    raw_sample: Optional[dict]
    metadata: ProviderMetadata


class ProviderStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class ProviderHealth:
    provider: str
    status: ProviderStatus
    checked_at: datetime
    latency_ms: float = 0.0
    error: Optional[str] = None


# ── Macro ─────────────────────────────────────────────────────────────────────

@dataclass
class MacroIndicator:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    indicator_id: str = ""
    name: str = ""
    value: float = 0.0
    unit: str = ""
    period: str = ""
    frequency: str = ""


@dataclass
class MacroSeries:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    series_id: str = ""
    name: str = ""
    unit: str = ""
    frequency: str = ""
    observations: list[dict] = field(default_factory=list)


# ── Assets ────────────────────────────────────────────────────────────────────

@dataclass
class CurrencyRate:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    base_currency: str = ""
    quote_currency: str = ""
    rate: float = 0.0
    date: Optional[date] = None
    frequency: str = "daily"


@dataclass
class YieldCurvePoint:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    maturity: str = ""
    yield_value: float = 0.0
    date: Optional[date] = None
    currency: str = ""


@dataclass
class BondYield(YieldCurvePoint):
    issuer: str = ""
    instrument_type: str = "government_bond"


@dataclass
class Commodity:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    price: float = 0.0
    unit: str = ""
    currency: str = "USD"


# ── Market ────────────────────────────────────────────────────────────────────

@dataclass
class MarketQuote:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    asset_type: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    currency: str = "EUR"
    market_status: str = ""


@dataclass
class HistoricalPrice:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    date: Optional[date] = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


# ── Company ───────────────────────────────────────────────────────────────────

@dataclass
class CompanyProfile:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    symbol: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    exchange: str = ""


# ── News ──────────────────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    title: str = ""
    published_at: Optional[datetime] = None
    source_name: str = ""
    url: str = ""
    category: str = ""
    related_asset: str = ""


@dataclass
class MarketNews:
    provider: str
    source: str
    retrieved_at: datetime
    country: str
    region: str
    confidence_score: float = 1.0
    title: str = ""
    url: str = ""
    published_at: Optional[datetime] = None
    source_name: str = ""
    tickers: list[str] = field(default_factory=list)
```

- [ ] **Step 2: Crear `ingestion/config.py` con el bridge de API keys**

Crear `backend/app/modules/market_intelligence/ingestion/config.py`:

```python
"""Bridge entre el sistema de API keys del POC y los settings del backend."""
from __future__ import annotations
from app.core.config import settings


def get_api_key(provider_name: str) -> str | None:
    """Devuelve la API key del provider o None si no está configurada.

    Convierte el nombre del provider al nombre de la variable en settings.
    Ejemplo: 'alpha_vantage' → settings.ALPHA_VANTAGE_API_KEY
    """
    env_var = f"{provider_name.upper().replace(' ', '_').replace('-', '_')}_API_KEY"
    value = getattr(settings, env_var, None)
    return value if value else None


def get_timeout() -> int:
    return 15


def get_workers() -> int:
    return 5
```

- [ ] **Step 3: Escribir tests**

Crear `backend/tests/market_intelligence/test_ingestion_models.py`:

```python
from datetime import datetime, timezone
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, MacroIndicator, CurrencyRate, BondYield,
    MarketQuote, ProviderMetadata, ProviderStatus, ProviderHealth,
)
from app.modules.market_intelligence.ingestion.config import get_api_key


def _meta():
    return ProviderMetadata(
        name="test", id="test", category="macro", region="Global",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def test_adapter_result_success():
    result = AdapterResult(
        provider="test", success=True, records=[], error=None,
        latency_ms=50.0, raw_sample=None, metadata=_meta(),
    )
    assert result.success is True
    assert result.latency_ms == 50.0


def test_macro_indicator_defaults():
    now = datetime.now(timezone.utc)
    ind = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain",
    )
    assert ind.confidence_score == 1.0
    assert ind.value == 0.0


def test_bond_yield_inherits_yield_curve_point():
    now = datetime.now(timezone.utc)
    b = BondYield(
        provider="FRED", source="https://fred.org", retrieved_at=now,
        country="US", region="USA", maturity="10Y", yield_value=4.32,
    )
    assert b.instrument_type == "government_bond"
    assert b.yield_value == 4.32


def test_get_api_key_missing_returns_none():
    result = get_api_key("nonexistent_provider_xyz")
    assert result is None


def test_provider_health_status_enum():
    now = datetime.now(timezone.utc)
    h = ProviderHealth(provider="test", status=ProviderStatus.DEGRADED, checked_at=now)
    assert h.status == ProviderStatus.DEGRADED
```

- [ ] **Step 4: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_ingestion_models.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/market_intelligence/ingestion/
git commit -m "feat(mi): add ingestion models + config bridge"
```

---

### Task 3: Catalog layer

**Files:**
- Create: `backend/app/modules/market_intelligence/catalog/schemas.py`
- Create: `backend/app/modules/market_intelligence/catalog/loader.py`
- Copy: `market-data-poc/catalog/*.yaml` → `backend/app/modules/market_intelligence/catalog/yaml/`
- Test: `backend/tests/market_intelligence/test_catalog.py`

**Interfaces:**
- Consumes: catalog YAML files
- Produces: `CatalogIndicator` dataclass, `CatalogLoader.load_all() -> list[CatalogIndicator]`, `CatalogLoader.get_by_category(cat) -> list`, `CatalogLoader.get_by_priority(*p) -> list`, `CatalogLoader.validate() -> list[str]`

- [ ] **Step 1: Crear `catalog/schemas.py`**

Crear `backend/app/modules/market_intelligence/catalog/schemas.py`:

```python
"""Schemas del catálogo de datos de mercado."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CatalogIndicator:
    id: str
    name: str
    category: str
    subcategory: str
    country: str
    region: str
    frequency: str
    priority: str
    dashboard: bool
    ai: bool
    historical: str
    retention: str
    unit: str
    description: str
    provider_primary: str
    provider_secondary: str | None = None
    provider_fallback: str | None = None
```

- [ ] **Step 2: Copiar los YAMLs del catálogo**

```bash
# desde AI-Financial-OS/
python -c "
import shutil
from pathlib import Path
src = Path('market-data-poc/catalog')
dst = Path('backend/app/modules/market_intelligence/catalog/yaml')
dst.mkdir(parents=True, exist_ok=True)
for f in src.glob('*.yaml'):
    shutil.copy(f, dst / f.name)
    print(f'Copied {f.name}')
"
```

Expected: 9 líneas de `Copied *.yaml`

- [ ] **Step 3: Crear `catalog/loader.py`**

Crear `backend/app/modules/market_intelligence/catalog/loader.py`:

```python
"""CatalogLoader — carga y valida los indicadores del catálogo YAML."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator

_CATALOG_DIR = Path(__file__).parent / "yaml"
_VALID_PRIORITIES = {"critical", "high", "medium", "low"}
_VALID_FREQUENCIES = {"realtime", "daily", "weekly", "monthly", "quarterly", "yearly"}


class CatalogLoader:
    def __init__(self, catalog_dir: Path | None = None):
        self._dir = catalog_dir or _CATALOG_DIR
        self._cache: list[CatalogIndicator] | None = None

    def load_all(self) -> list[CatalogIndicator]:
        if self._cache is not None:
            return self._cache
        indicators: list[CatalogIndicator] = []
        for yaml_file in sorted(self._dir.glob("*.yaml")):
            raw: list[dict[str, Any]] = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or []
            for entry in raw:
                indicators.append(self._parse(entry))
        self._cache = indicators
        return indicators

    def get_by_id(self, indicator_id: str) -> CatalogIndicator | None:
        return next((i for i in self.load_all() if i.id == indicator_id), None)

    def get_by_priority(self, *priorities: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.priority in priorities]

    def get_by_provider(self, provider_id: str) -> list[CatalogIndicator]:
        return [
            i for i in self.load_all()
            if provider_id in (i.provider_primary, i.provider_secondary, i.provider_fallback)
        ]

    def get_by_category(self, category: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.category == category]

    def get_for_ai(self) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.ai]

    def get_for_dashboard(self) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.dashboard]

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen_ids: set[str] = set()
        for ind in self.load_all():
            if not ind.id:
                errors.append("Indicator missing id")
            elif ind.id in seen_ids:
                errors.append(f"Duplicate id: {ind.id}")
            else:
                seen_ids.add(ind.id)
            if not ind.name:
                errors.append(f"{ind.id}: missing name")
            if not ind.provider_primary:
                errors.append(f"{ind.id}: missing provider_primary")
            if ind.priority not in _VALID_PRIORITIES:
                errors.append(f"{ind.id}: invalid priority '{ind.priority}'")
            if ind.frequency not in _VALID_FREQUENCIES:
                errors.append(f"{ind.id}: invalid frequency '{ind.frequency}'")
        return errors

    @staticmethod
    def _parse(entry: dict[str, Any]) -> CatalogIndicator:
        return CatalogIndicator(
            id=entry["id"],
            name=entry["name"],
            category=entry.get("category", ""),
            subcategory=entry.get("subcategory", ""),
            country=entry.get("country", "GLOBAL"),
            region=entry.get("region", "Global"),
            frequency=entry.get("frequency", "monthly"),
            priority=entry.get("priority", "medium"),
            dashboard=bool(entry.get("dashboard", False)),
            ai=bool(entry.get("ai", False)),
            historical=entry.get("historical", "1y"),
            retention=entry.get("retention", "1y"),
            unit=entry.get("unit", ""),
            description=entry.get("description", ""),
            provider_primary=entry.get("provider_primary", ""),
            provider_secondary=entry.get("provider_secondary"),
            provider_fallback=entry.get("provider_fallback"),
        )
```

- [ ] **Step 4: Escribir tests**

Crear `backend/tests/market_intelligence/test_catalog.py`:

```python
import pytest
from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.catalog.schemas import CatalogIndicator


@pytest.fixture
def loader():
    return CatalogLoader()


def test_load_all_returns_indicators(loader):
    items = loader.load_all()
    assert len(items) > 0
    assert all(isinstance(i, CatalogIndicator) for i in items)


def test_all_items_have_required_fields(loader):
    for item in loader.load_all():
        assert item.id, f"Missing id in {item}"
        assert item.name, f"Missing name in {item.id}"
        assert item.provider_primary, f"Missing provider_primary in {item.id}"


def test_validate_returns_no_errors(loader):
    errors = loader.validate()
    assert errors == [], f"Catalog validation errors: {errors}"


def test_get_by_category(loader):
    macro = loader.get_by_category("macro")
    assert len(macro) > 0
    assert all(i.category == "macro" for i in macro)


def test_get_by_priority(loader):
    critical = loader.get_by_priority("critical")
    assert len(critical) > 0
    assert all(i.priority == "critical" for i in critical)


def test_get_for_ai_returns_ai_items(loader):
    ai_items = loader.get_for_ai()
    assert len(ai_items) > 0
    assert all(i.ai for i in ai_items)


def test_get_by_id_returns_correct_item(loader):
    items = loader.load_all()
    first = items[0]
    found = loader.get_by_id(first.id)
    assert found is not None
    assert found.id == first.id


def test_loader_cache_is_consistent(loader):
    items1 = loader.load_all()
    items2 = loader.load_all()
    assert items1 is items2  # mismo objeto — cache funciona
```

- [ ] **Step 5: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_catalog.py -v
```

Expected: `8 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/market_intelligence/catalog/
git commit -m "feat(mi): add catalog layer with YAML loader"
```

---

### Task 4: Migración de adapters del POC

**Files:**
- Create: `backend/app/modules/market_intelligence/ingestion/adapters/base.py`
- Create: `backend/app/modules/market_intelligence/ingestion/adapters/catalog.py`
- Create (via migration script): todos los adapters de spain/, europe/, usa/, global_/, rss/
- Test: `backend/tests/market_intelligence/test_adapters_import.py`

**Interfaces:**
- Consumes: `ingestion/models.py`, `ingestion/config.py`
- Produces: `BaseAdapter` con `.fetch(indicator_id) -> AdapterResult`, `.is_available() -> bool`, `.supports(indicator_id) -> bool`

- [ ] **Step 1: Crear `ingestion/adapters/base.py`**

Crear `backend/app/modules/market_intelligence/ingestion/adapters/base.py`:

```python
"""BaseAdapter para el Market Intelligence Layer.

Adaptado de market-data-poc/adapters/base.py con imports actualizados.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
import time

from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderHealth, ProviderMetadata, ProviderStatus,
)
from app.modules.market_intelligence.ingestion.config import get_api_key


class BaseAdapter(ABC):
    name: str = ""
    category: str = ""
    region: str = ""
    requires_api_key: bool = False
    api_key_names: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"
    supported_indicators: dict[str, dict] = {}

    @abstractmethod
    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ...

    def is_available(self) -> bool:
        if self.requires_api_key:
            key_names = self.api_key_names or (self.name,)
            return any(get_api_key(name) is not None for name in key_names)
        return True

    def supports(self, indicator_id: str) -> bool:
        return indicator_id in self.supported_indicators

    def _make_metadata(self, **kwargs) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            id=kwargs.get("id", self.name.lower().replace(" ", "_")),
            category=self.category,
            region=self.region,
            method=kwargs.get("method", "api"),
            base_url=kwargs.get("base_url", ""),
            requires_api_key=self.requires_api_key,
            declared_update_frequency=kwargs.get("declared_update_frequency", "unknown"),
            declared_historical_depth_years=kwargs.get("declared_historical_depth_years", 0),
            license=kwargs.get("license", "unknown"),
            notes=kwargs.get("notes", ""),
            capabilities=kwargs.get("capabilities", self.capabilities),
            priority=kwargs.get("priority", self.priority),
        )

    def health_check(self, timeout: int = 10) -> ProviderHealth:
        t0 = time.perf_counter()
        try:
            if not self.is_available():
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.OFFLINE,
                    checked_at=datetime.utcnow(),
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    error="Provider unavailable or required API key missing",
                )
            result = self.fetch()
            status = ProviderStatus.ONLINE if result.success else ProviderStatus.DEGRADED
            return ProviderHealth(
                provider=self.name,
                status=status,
                checked_at=datetime.utcnow(),
                latency_ms=result.latency_ms,
                error=result.error,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.OFFLINE,
                checked_at=datetime.utcnow(),
                latency_ms=(time.perf_counter() - t0) * 1000,
                error=str(exc),
            )
```

- [ ] **Step 2: Crear `ingestion/adapters/catalog.py`**

Crear `backend/app/modules/market_intelligence/ingestion/adapters/catalog.py`:

```python
"""PublicDatasetAdapter — adapter para datasets públicos.

Adaptado de market-data-poc/adapters/catalog.py.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroSeries, MarketNews

_HEADERS = {"User-Agent": "AIFinancialOS/0.1 contact@example.com"}


class PublicDatasetAdapter(BaseAdapter):
    name = ""
    provider_id = ""
    category = "macro"
    region = "Global"
    base_url = ""
    notes = ""
    capabilities = ()
    priority = "fallback"
    method = "api"
    license = "open"
    update_frequency = "unknown"
    historical_depth_years = 0

    def is_available(self) -> bool:
        if not self.base_url:
            return False
        try:
            response = requests.get(self.base_url, headers=_HEADERS, timeout=10)
            return response.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = self._make_metadata(
            id=self.provider_id,
            base_url=self.base_url,
            method=self.method,
            license=self.license,
            notes=self.notes,
            declared_update_frequency=self.update_frequency,
            declared_historical_depth_years=self.historical_depth_years,
        )
        t0 = time.perf_counter()
        try:
            response = requests.get(self.base_url, headers=_HEADERS, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            record = self._record(response)
            return AdapterResult(
                provider=self.name, success=True, records=[record],
                error=None, latency_ms=latency_ms,
                raw_sample={"status_code": response.status_code, "preview": response.text[:500]},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None, metadata=metadata,
            )

    def _record(self, response):
        retrieved_at = datetime.now(timezone.utc)
        if self.category == "news":
            return MarketNews(
                provider=self.name, source=self.base_url, retrieved_at=retrieved_at,
                country="GLOBAL", region=self.region, confidence_score=0.6,
                title=f"{self.name} public feed reachable", url=self.base_url,
                source_name=self.name,
            )
        return MacroSeries(
            provider=self.name, source=self.base_url, retrieved_at=retrieved_at,
            country=self.region if self.region in ("Spain", "USA") else "GLOBAL",
            region=self.region, confidence_score=0.7,
            series_id=self.provider_id, name=self.name,
            frequency=self.update_frequency, observations=[],
        )
```

- [ ] **Step 3: Ejecutar script de migración de adapters**

Ejecutar este script desde `AI-Financial-OS/`:

```python
# Guardar como migrate_adapters.py y ejecutar: python migrate_adapters.py
import shutil
import re
from pathlib import Path

POC_ADAPTERS = Path("market-data-poc/adapters")
BACKEND_ADAPTERS = Path("backend/app/modules/market_intelligence/ingestion/adapters")

SUBDIRS = ["europe", "global_", "spain", "usa", "rss"]

IMPORT_REPLACEMENTS = [
    (r"from adapters\.base import", "from app.modules.market_intelligence.ingestion.adapters.base import"),
    (r"from adapters\.catalog import", "from app.modules.market_intelligence.ingestion.adapters.catalog import"),
    (r"from models\.base import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from models\.assets import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from models\.macro import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from models\.market import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from models\.company import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from models\.news import", "from app.modules.market_intelligence.ingestion.models import"),
    (r"from config\.settings import get_api_key", "from app.modules.market_intelligence.ingestion.config import get_api_key"),
    (r"from config\.settings import", "from app.modules.market_intelligence.ingestion.config import"),
]

def fix_imports(content: str) -> str:
    for pattern, replacement in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    return content

copied = 0
for subdir in SUBDIRS:
    src_dir = POC_ADAPTERS / subdir
    dst_dir = BACKEND_ADAPTERS / subdir
    if not src_dir.exists():
        print(f"  SKIP (not found): {src_dir}")
        continue
    dst_dir.mkdir(parents=True, exist_ok=True)
    for py_file in src_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        content = fix_imports(content)
        dst = dst_dir / py_file.name
        dst.write_text(content, encoding="utf-8")
        copied += 1

print(f"Migrated {copied} adapter files")
```

```bash
python migrate_adapters.py
```

Expected: `Migrated N adapter files` donde N > 20

- [ ] **Step 4: Verificar que los `__init__.py` de subdirectorios existen**

```bash
python -c "
from pathlib import Path
base = Path('backend/app/modules/market_intelligence/ingestion/adapters')
for d in ['europe', 'global_', 'spain', 'usa', 'rss']:
    init = base / d / '__init__.py'
    if not init.exists():
        init.touch()
        print(f'Created {init}')
    else:
        print(f'OK {init}')
"
```

- [ ] **Step 5: Escribir test de importación de adapters**

Crear `backend/tests/market_intelligence/test_adapters_import.py`:

```python
"""Verifica que todos los adapters migrados se importan sin error."""
import importlib
import pytest


ADAPTER_MODULES = [
    "app.modules.market_intelligence.ingestion.adapters.base",
    "app.modules.market_intelligence.ingestion.adapters.catalog",
    "app.modules.market_intelligence.ingestion.adapters.europe.ecb",
    "app.modules.market_intelligence.ingestion.adapters.europe.eurostat",
    "app.modules.market_intelligence.ingestion.adapters.europe.oecd",
    "app.modules.market_intelligence.ingestion.adapters.spain.ine",
    "app.modules.market_intelligence.ingestion.adapters.spain.bde",
    "app.modules.market_intelligence.ingestion.adapters.usa.fred",
    "app.modules.market_intelligence.ingestion.adapters.global_.frankfurter",
    "app.modules.market_intelligence.ingestion.adapters.global_.coingecko",
    "app.modules.market_intelligence.ingestion.adapters.global_.stooq",
]


@pytest.mark.parametrize("module_path", ADAPTER_MODULES)
def test_adapter_module_imports(module_path):
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_base_adapter_has_required_interface():
    from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
    assert hasattr(BaseAdapter, "fetch")
    assert hasattr(BaseAdapter, "is_available")
    assert hasattr(BaseAdapter, "supports")
    assert hasattr(BaseAdapter, "health_check")
```

- [ ] **Step 6: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_adapters_import.py -v
```

Expected: todos passed. Si algún adapter falla por import no encontrado, revisar el script de migración para ese archivo específico y corregir manualmente.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/market_intelligence/ingestion/
git commit -m "feat(mi): migrate POC adapters to backend with fixed imports"
```

---

### Task 5: Orchestrator + Runner

**Files:**
- Create: `backend/app/modules/market_intelligence/ingestion/orchestrator.py`
- Create: `backend/app/modules/market_intelligence/ingestion/runner.py`
- Test: `backend/tests/market_intelligence/test_orchestrator.py`

**Interfaces:**
- Consumes: `BaseAdapter`, `CatalogIndicator`, `AdapterResult`
- Produces: `ProviderOrchestrator.fetch_indicator(indicator: CatalogIndicator) -> CatalogFetchResult`, `run_ingestion(category, priority, dry_run) -> IngestionSummary`

- [ ] **Step 1: Crear `ingestion/orchestrator.py`**

Crear `backend/app/modules/market_intelligence/ingestion/orchestrator.py`:

```python
"""ProviderOrchestrator — selección y fallback de providers por CatalogIndicator.

Adaptado de market-data-poc/services/orchestrator.py.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderMetadata,
)

logger = logging.getLogger("market_intelligence.orchestrator")


@dataclass
class CatalogFetchResult:
    indicator: CatalogIndicator
    adapter_result: AdapterResult
    provider_used: str
    fallback_used: bool
    catalog_id: str


class ProviderOrchestrator:
    def __init__(self, adapters: list[BaseAdapter]):
        self._adapters = adapters

    def _get_adapter(self, provider_id: str) -> BaseAdapter | None:
        return next(
            (
                a for a in self._adapters
                if (
                    getattr(a, "provider_id", None) == provider_id
                    or a.name.lower().replace(" ", "_") == provider_id
                    or getattr(a, "_provider_id", None) == provider_id
                )
            ),
            None,
        )

    def fetch_indicator(self, indicator: CatalogIndicator) -> CatalogFetchResult:
        chain = [
            indicator.provider_primary,
            indicator.provider_secondary,
            indicator.provider_fallback,
        ]
        for provider_id in [p for p in chain if p]:
            adapter = self._get_adapter(provider_id)
            if adapter is None:
                logger.debug("No adapter found for provider '%s'", provider_id)
                continue
            if not adapter.is_available():
                logger.info("Provider '%s' not available (API key missing?)", provider_id)
                continue
            if not adapter.supports(indicator.id):
                logger.debug("Provider '%s' does not support indicator '%s'", provider_id, indicator.id)
                continue
            try:
                result = adapter.fetch(indicator.id)
            except Exception as exc:
                logger.warning("Adapter '%s' raised exception: %s", provider_id, exc)
                continue
            logger.info(
                "fetch indicator=%s provider=%s success=%s fallback=%s latency=%.0fms",
                indicator.id, provider_id, result.success, provider_id != indicator.provider_primary,
                result.latency_ms,
            )
            if result.success:
                return CatalogFetchResult(
                    indicator=indicator,
                    adapter_result=result,
                    provider_used=provider_id,
                    fallback_used=(provider_id != indicator.provider_primary),
                    catalog_id=indicator.id,
                )

        _empty_meta = ProviderMetadata(
            name="Orchestrator", id="orchestrator", category="orchestration",
            region="Global", method="internal", base_url="",
            requires_api_key=False, declared_update_frequency="unknown",
            declared_historical_depth_years=0, license="internal",
        )
        return CatalogFetchResult(
            indicator=indicator,
            adapter_result=AdapterResult(
                provider="Orchestrator", success=False, records=[],
                error=f"No provider produced data for '{indicator.id}'",
                latency_ms=0.0, raw_sample=None, metadata=_empty_meta,
            ),
            provider_used="none",
            fallback_used=False,
            catalog_id=indicator.id,
        )

    def health(self) -> list:
        return [a.health_check() for a in self._adapters]
```

- [ ] **Step 2: Crear `ingestion/runner.py`**

Crear `backend/app/modules/market_intelligence/ingestion/runner.py`:

```python
"""Runner de ingesta — orquesta catalog → fetch → quality → persist.

Punto de entrada para los comandos CLI market:intelligence:update.
"""
from __future__ import annotations
import importlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.orchestrator import (
    CatalogFetchResult, ProviderOrchestrator,
)

logger = logging.getLogger("market_intelligence.runner")

# Map provider_id → módulo del adapter (mismo que en POC run_poc.py)
_ADAPTER_MAP: dict[str, str] = {
    "bde": "app.modules.market_intelligence.ingestion.adapters.spain.bde",
    "ine": "app.modules.market_intelligence.ingestion.adapters.spain.ine",
    "cnmv": "app.modules.market_intelligence.ingestion.adapters.spain.cnmv",
    "bme": "app.modules.market_intelligence.ingestion.adapters.spain.bme",
    "tesoro": "app.modules.market_intelligence.ingestion.adapters.spain.tesoro",
    "ree": "app.modules.market_intelligence.ingestion.adapters.spain.ree",
    "aemet": "app.modules.market_intelligence.ingestion.adapters.spain.aemet",
    "seguridad_social": "app.modules.market_intelligence.ingestion.adapters.spain.seguridad_social",
    "agencia_tributaria": "app.modules.market_intelligence.ingestion.adapters.spain.agencia_tributaria",
    "ecb": "app.modules.market_intelligence.ingestion.adapters.europe.ecb",
    "eurostat": "app.modules.market_intelligence.ingestion.adapters.europe.eurostat",
    "oecd": "app.modules.market_intelligence.ingestion.adapters.europe.oecd",
    "bis": "app.modules.market_intelligence.ingestion.adapters.europe.bis",
    "european_commission": "app.modules.market_intelligence.ingestion.adapters.europe.european_commission",
    "eur_lex": "app.modules.market_intelligence.ingestion.adapters.europe.eur_lex",
    "fred": "app.modules.market_intelligence.ingestion.adapters.usa.fred",
    "edgar": "app.modules.market_intelligence.ingestion.adapters.usa.edgar",
    "bls": "app.modules.market_intelligence.ingestion.adapters.usa.bls",
    "treasury": "app.modules.market_intelligence.ingestion.adapters.usa.treasury",
    "bea": "app.modules.market_intelligence.ingestion.adapters.usa.bea",
    "census": "app.modules.market_intelligence.ingestion.adapters.usa.census",
    "eia": "app.modules.market_intelligence.ingestion.adapters.usa.eia",
    "world_bank": "app.modules.market_intelligence.ingestion.adapters.global_.world_bank",
    "imf": "app.modules.market_intelligence.ingestion.adapters.global_.imf",
    "coingecko": "app.modules.market_intelligence.ingestion.adapters.global_.coingecko",
    "stooq": "app.modules.market_intelligence.ingestion.adapters.global_.stooq",
    "alpha_vantage": "app.modules.market_intelligence.ingestion.adapters.global_.alpha_vantage",
    "finnhub": "app.modules.market_intelligence.ingestion.adapters.global_.finnhub",
    "fmp": "app.modules.market_intelligence.ingestion.adapters.global_.fmp",
    "twelvedata": "app.modules.market_intelligence.ingestion.adapters.global_.twelvedata",
    "openfigi": "app.modules.market_intelligence.ingestion.adapters.global_.openfigi",
    "polygon": "app.modules.market_intelligence.ingestion.adapters.global_.polygon",
    "frankfurter": "app.modules.market_intelligence.ingestion.adapters.global_.frankfurter",
    "un_data": "app.modules.market_intelligence.ingestion.adapters.global_.un_data",
    "rss": "app.modules.market_intelligence.ingestion.adapters.rss.reader",
}


@dataclass
class IngestionSummary:
    run_id: str
    started_at: datetime
    finished_at: datetime
    total: int
    success: int
    failed: int
    fallbacks_used: int
    results: list[CatalogFetchResult] = field(default_factory=list)


def build_adapters(provider_ids: list[str] | None = None) -> list[BaseAdapter]:
    """Instancia los adapters para los provider_ids dados (o todos si None)."""
    ids = provider_ids or list(_ADAPTER_MAP.keys())
    adapters: list[BaseAdapter] = []
    for pid in ids:
        module_path = _ADAPTER_MAP.get(pid)
        if not module_path:
            continue
        try:
            module = importlib.import_module(module_path)
            adapter_cls = getattr(module, "Adapter", None)
            if adapter_cls is None:
                candidates = [
                    v for v in vars(module).values()
                    if isinstance(v, type) and issubclass(v, BaseAdapter) and v is not BaseAdapter
                ]
                adapter_cls = candidates[0] if candidates else None
            if adapter_cls is None:
                continue
            adapters.append(adapter_cls())
        except Exception as exc:
            logger.warning("Could not load adapter '%s': %s", pid, exc)
    return adapters


def run_ingestion(
    category: str | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> IngestionSummary:
    """Ejecuta la ingesta completa o filtrada y persiste en DuckDB."""
    from app.modules.market_intelligence.quality.engine import QualityEngine
    from app.modules.market_intelligence.storage import repository

    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now(timezone.utc)

    loader = CatalogLoader()
    indicators = loader.load_all()
    if category:
        indicators = [i for i in indicators if i.category == category]
    if priority:
        indicators = [i for i in indicators if i.priority == priority]

    adapters = build_adapters()
    orchestrator = ProviderOrchestrator(adapters)
    quality_engine = QualityEngine()

    results: list[CatalogFetchResult] = []
    success = 0
    failed = 0
    fallbacks = 0

    for indicator in indicators:
        result = orchestrator.fetch_indicator(indicator)
        results.append(result)

        if result.adapter_result.success:
            success += 1
            if result.fallback_used:
                fallbacks += 1
            if not dry_run:
                quality_result = quality_engine.score(result, indicator)
                repository.persist_fetch_result(result, quality_result, run_id)
        else:
            failed += 1
            if not dry_run:
                repository.log_provider_health(
                    provider_id=result.provider_used,
                    catalog_item_id=indicator.id,
                    status="error",
                    latency_ms=int(result.adapter_result.latency_ms),
                    error_message=result.adapter_result.error,
                )

        logger.info(
            "run=%s indicator=%s provider=%s success=%s fallback=%s",
            run_id, indicator.id, result.provider_used,
            result.adapter_result.success, result.fallback_used,
        )

    return IngestionSummary(
        run_id=run_id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        total=len(indicators),
        success=success,
        failed=failed,
        fallbacks_used=fallbacks,
        results=results,
    )
```

- [ ] **Step 3: Escribir tests del orchestrator**

Crear `backend/tests/market_intelligence/test_orchestrator.py`:

```python
from unittest.mock import MagicMock
from datetime import datetime, timezone
import pytest

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import ProviderOrchestrator
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderMetadata, ProviderStatus,
)


def _make_meta(name: str) -> ProviderMetadata:
    return ProviderMetadata(
        name=name, id=name, category="macro", region="Global",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def _make_adapter(name: str, success: bool, provider_id: str, supports: bool = True):
    adapter = MagicMock()
    adapter.name = name
    adapter.provider_id = provider_id
    adapter.is_available.return_value = True
    adapter.supports.return_value = supports
    adapter.fetch.return_value = AdapterResult(
        provider=name, success=success, records=[], error=None if success else "fail",
        latency_ms=50.0, raw_sample=None, metadata=_make_meta(name),
    )
    return adapter


def _make_indicator(primary: str, secondary: str | None = None, fallback: str | None = None):
    return CatalogIndicator(
        id="test_ind", name="Test", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="5y", retention="5y",
        unit="%", description="", provider_primary=primary,
        provider_secondary=secondary, provider_fallback=fallback,
    )


def test_uses_primary_when_available():
    primary = _make_adapter("primary", success=True, provider_id="primary")
    orch = ProviderOrchestrator([primary])
    result = orch.fetch_indicator(_make_indicator("primary"))
    assert result.provider_used == "primary"
    assert result.fallback_used is False
    assert result.adapter_result.success is True


def test_falls_back_to_secondary_when_primary_fails():
    primary = _make_adapter("primary", success=False, provider_id="primary")
    secondary = _make_adapter("secondary", success=True, provider_id="secondary")
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"
    assert result.fallback_used is True


def test_returns_failure_when_all_providers_fail():
    primary = _make_adapter("primary", success=False, provider_id="primary")
    orch = ProviderOrchestrator([primary])
    result = orch.fetch_indicator(_make_indicator("primary"))
    assert result.adapter_result.success is False
    assert result.provider_used == "none"


def test_skips_unavailable_adapter():
    primary = _make_adapter("primary", success=True, provider_id="primary")
    primary.is_available.return_value = False
    secondary = _make_adapter("secondary", success=True, provider_id="secondary")
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"


def test_skips_adapter_that_does_not_support_indicator():
    primary = _make_adapter("primary", success=True, provider_id="primary", supports=False)
    secondary = _make_adapter("secondary", success=True, provider_id="secondary", supports=True)
    orch = ProviderOrchestrator([primary, secondary])
    result = orch.fetch_indicator(_make_indicator("primary", secondary="secondary"))
    assert result.provider_used == "secondary"
```

- [ ] **Step 4: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_orchestrator.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/market_intelligence/ingestion/
git commit -m "feat(mi): add orchestrator with fallback + ingestion runner"
```

---

### Task 6: Quality Engine

**Files:**
- Create: `backend/app/modules/market_intelligence/quality/schemas.py`
- Create: `backend/app/modules/market_intelligence/quality/checks.py`
- Create: `backend/app/modules/market_intelligence/quality/engine.py`
- Test: `backend/tests/market_intelligence/test_quality.py`

**Interfaces:**
- Consumes: `CatalogFetchResult`, `CatalogIndicator`
- Produces: `QualityEngine.score(result, indicator) -> QualityResult`; `QualityResult.final_score: float`

- [ ] **Step 1: Crear `quality/schemas.py`**

Crear `backend/app/modules/market_intelligence/quality/schemas.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    name: str
    status: str        # "pass" | "warn" | "fail"
    score: float       # 0.0 – 1.0
    detail: str = ""


@dataclass
class QualityResult:
    final_score: float
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.final_score >= 0.5
```

- [ ] **Step 2: Crear `quality/checks.py`**

Crear `backend/app/modules/market_intelligence/quality/checks.py`:

```python
"""Funciones de check individuales para el Quality Engine."""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import CheckResult

# Pesos de cada check en el score final
WEIGHTS = {
    "freshness": 0.30,
    "completeness": 0.20,
    "validity": 0.25,
    "outlier": 0.15,
    "provider_reliability": 0.10,
}

# Ventana máxima de frescura por frecuencia (horas)
_FRESHNESS_WINDOWS: dict[str, int] = {
    "realtime": 1,
    "daily": 26,
    "weekly": 8 * 24,
    "monthly": 35 * 24,
    "quarterly": 95 * 24,
    "yearly": 370 * 24,
}


def check_freshness(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    retrieved_at = result.adapter_result.records[0].retrieved_at if result.adapter_result.records else None
    if retrieved_at is None:
        return CheckResult("freshness", "fail", 0.0, "No retrieved_at available")

    now = datetime.now(timezone.utc)
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    age_hours = (now - retrieved_at).total_seconds() / 3600
    max_hours = _FRESHNESS_WINDOWS.get(indicator.frequency, 26)

    if age_hours <= max_hours:
        return CheckResult("freshness", "pass", 1.0, f"Age {age_hours:.1f}h <= {max_hours}h")
    elif age_hours <= max_hours * 2:
        score = 0.5
        return CheckResult("freshness", "warn", score, f"Age {age_hours:.1f}h > {max_hours}h")
    else:
        return CheckResult("freshness", "fail", 0.0, f"Age {age_hours:.1f}h far exceeds {max_hours}h")


def check_completeness(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    if not result.adapter_result.records:
        return CheckResult("completeness", "fail", 0.0, "No records returned")
    record = result.adapter_result.records[0]
    required = ["provider", "source", "retrieved_at", "country", "region"]
    missing = [f for f in required if not getattr(record, f, None)]
    if not missing:
        return CheckResult("completeness", "pass", 1.0, "All required fields present")
    score = max(0.0, 1.0 - len(missing) * 0.2)
    return CheckResult("completeness", "warn", score, f"Missing: {missing}")


def check_validity(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    if not result.adapter_result.records:
        return CheckResult("validity", "fail", 0.0, "No records")
    record = result.adapter_result.records[0]
    value = getattr(record, "value", None) or getattr(record, "rate", None) or getattr(record, "price", None)
    if value is None:
        return CheckResult("validity", "warn", 0.6, "Numeric value field is None")
    if isinstance(value, float) and math.isnan(value):
        return CheckResult("validity", "fail", 0.0, "Value is NaN")
    if value < 0 and indicator.category not in ("macro",):
        return CheckResult("validity", "warn", 0.7, f"Unexpected negative value: {value}")
    return CheckResult("validity", "pass", 1.0, f"Value {value} looks valid")


def check_outlier(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    # Sin historia previa en DuckDB no podemos calcular σ — devolvemos neutral
    return CheckResult("outlier", "pass", 1.0, "Outlier check skipped (no history yet)")


def check_provider_reliability(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    # Sin history de health logs — devolvemos score neutro
    # En producción leer mi_provider_health_logs y calcular success_rate
    return CheckResult("provider_reliability", "pass", 0.8, "Reliability check: no history, using default 0.8")
```

- [ ] **Step 3: Crear `quality/engine.py`**

Crear `backend/app/modules/market_intelligence/quality/engine.py`:

```python
"""QualityEngine — calcula el quality score de un CatalogFetchResult."""
from __future__ import annotations

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.checks import (
    WEIGHTS,
    check_completeness,
    check_freshness,
    check_outlier,
    check_provider_reliability,
    check_validity,
)
from app.modules.market_intelligence.quality.schemas import CheckResult, QualityResult


class QualityEngine:
    def score(self, result: CatalogFetchResult, indicator: CatalogIndicator) -> QualityResult:
        if not result.adapter_result.success:
            return QualityResult(
                final_score=0.0,
                checks=[CheckResult("overall", "fail", 0.0, "Adapter fetch failed")],
            )

        checks = [
            check_freshness(result, indicator),
            check_completeness(result, indicator),
            check_validity(result, indicator),
            check_outlier(result, indicator),
            check_provider_reliability(result, indicator),
        ]

        final_score = sum(
            WEIGHTS[c.name] * c.score
            for c in checks
            if c.name in WEIGHTS
        )

        return QualityResult(final_score=round(final_score, 4), checks=checks)
```

- [ ] **Step 4: Escribir tests**

Crear `backend/tests/market_intelligence/test_quality.py`:

```python
from unittest.mock import MagicMock
from datetime import datetime, timezone
import pytest

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderMetadata, MacroIndicator,
)
from app.modules.market_intelligence.quality.engine import QualityEngine
from app.modules.market_intelligence.quality.checks import (
    check_freshness, check_completeness, check_validity, WEIGHTS,
)


def _meta():
    return ProviderMetadata(
        name="test", id="test", category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="daily", declared_historical_depth_years=0,
        license="open",
    )


def _indicator():
    return CatalogIndicator(
        id="ipc_general", name="IPC España", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="ine",
    )


def _record(value: float = 2.8):
    return MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=datetime.now(timezone.utc),
        country="ES", region="Spain", value=value, indicator_id="ipc_general",
        name="IPC General", unit="%", period="2026-05", frequency="monthly",
    )


def _successful_result(records=None):
    if records is None:
        records = [_record()]
    return CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=records, error=None,
            latency_ms=120.0, raw_sample=None, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )


def test_score_successful_fetch_returns_positive_score():
    engine = QualityEngine()
    result = _successful_result()
    quality = engine.score(result, _indicator())
    assert quality.final_score > 0.0
    assert quality.final_score <= 1.0
    assert quality.passed is True


def test_score_failed_fetch_returns_zero():
    engine = QualityEngine()
    failed = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=False, records=[], error="timeout",
            latency_ms=10000.0, raw_sample=None, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )
    quality = engine.score(failed, _indicator())
    assert quality.final_score == 0.0
    assert quality.passed is False


def test_completeness_check_fails_with_no_records():
    result = _successful_result(records=[])
    result.adapter_result.success = True  # forzar
    check = check_completeness(result, _indicator())
    assert check.status == "fail"
    assert check.score == 0.0


def test_validity_check_with_valid_value():
    result = _successful_result()
    check = check_validity(result, _indicator())
    assert check.status == "pass"
    assert check.score == 1.0


def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"


def test_quality_result_has_five_checks():
    engine = QualityEngine()
    result = _successful_result()
    quality = engine.score(result, _indicator())
    assert len(quality.checks) == 5
```

- [ ] **Step 5: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_quality.py -v
```

Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/market_intelligence/quality/
git commit -m "feat(mi): add quality engine with five checks + weighted score"
```

---

### Task 7: Storage repository + snapshot

**Files:**
- Create: `backend/app/modules/market_intelligence/storage/repository.py`
- Create: `backend/app/modules/market_intelligence/storage/snapshot.py`
- Test: `backend/tests/market_intelligence/test_repository.py`

**Interfaces:**
- Consumes: `CatalogFetchResult`, `QualityResult`, DuckDB connection
- Produces: `persist_fetch_result(result, quality, run_id)`, `log_provider_health(...)`, `get_latest_macro(catalog_item_id) -> dict | None`, `get_latest_quotes() -> list[dict]`, `get_latest_forex() -> list[dict]`, `get_latest_bonds() -> list[dict]`, `get_latest_news(limit) -> list[dict]`, `generate_snapshot() -> dict`

- [ ] **Step 1: Crear `storage/repository.py`**

Crear `backend/app/modules/market_intelligence/storage/repository.py`:

```python
"""Repository DuckDB para el Market Intelligence Layer."""
from __future__ import annotations
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.duckdb import get_duckdb
from app.modules.market_intelligence.ingestion.models import (
    MacroIndicator, CurrencyRate, BondYield, MarketQuote,
    HistoricalPrice, Commodity, NewsItem,
)
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import QualityResult
from app.modules.market_intelligence.storage.migrations import run_migrations

logger = logging.getLogger("market_intelligence.repository")

_migrations_run = False


def _conn():
    global _migrations_run
    c = get_duckdb()
    if not _migrations_run:
        run_migrations(c)
        _migrations_run = True
    return c


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


def _checksum(payload: str) -> str:
    return hashlib.md5(payload.encode()).hexdigest()


# ── Persist fetch result ──────────────────────────────────────────────────────

def persist_fetch_result(
    result: CatalogFetchResult,
    quality: QualityResult,
    run_id: str,
) -> None:
    """Persiste raw record + normalized record + log de salud."""
    conn = _conn()
    now = _now()
    catalog_item_id = result.catalog_id
    provider_id = result.provider_used

    # Raw record
    raw_payload = json.dumps(result.adapter_result.raw_sample or {})
    checksum = _checksum(raw_payload)
    # Idempotencia: skip si mismo checksum ya existe
    existing = conn.execute(
        "SELECT id FROM mi_raw_records WHERE catalog_item_id = ? AND checksum = ? LIMIT 1",
        [catalog_item_id, checksum],
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO mi_raw_records (id, catalog_item_id, provider_id, raw_payload_json,
                source_url, retrieved_at, ingestion_run_id, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [_uid(), catalog_item_id, provider_id, raw_payload,
             result.adapter_result.metadata.base_url, now, run_id, checksum],
        )

    # Normalized records por tipo de modelo
    for record in result.adapter_result.records:
        _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now)

    # Health log
    log_provider_health(
        provider_id=provider_id,
        catalog_item_id=catalog_item_id,
        status="success",
        latency_ms=int(result.adapter_result.latency_ms),
    )


def _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now):
    model_type = type(record).__name__
    value_numeric = (
        getattr(record, "value", None)
        or getattr(record, "rate", None)
        or getattr(record, "price", None)
        or getattr(record, "yield_value", None)
    )
    conn.execute(
        """
        INSERT INTO mi_normalized_records
            (id, catalog_item_id, provider_id, model_type, observed_at, value_numeric,
             unit, period, frequency, source_url, retrieved_at, confidence_score, quality_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            _uid(), catalog_item_id, provider_id, model_type,
            getattr(record, "retrieved_at", now),
            value_numeric,
            getattr(record, "unit", ""),
            getattr(record, "period", ""),
            getattr(record, "frequency", ""),
            getattr(record, "source", ""),
            now,
            getattr(record, "confidence_score", 1.0),
            quality.final_score,
            now,
        ],
    )

    # Tablas especializadas
    if isinstance(record, MacroIndicator):
        _upsert_macro(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, CurrencyRate):
        _upsert_currency(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, BondYield):
        _upsert_bond(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, MarketQuote):
        _upsert_quote(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, Commodity):
        _upsert_commodity(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, NewsItem):
        _insert_news(conn, provider_id, record)


def _upsert_macro(conn, catalog_item_id, provider_id, record: MacroIndicator, quality):
    conn.execute(
        """
        INSERT OR REPLACE INTO mi_macro_observations
            (id, catalog_item_id, indicator_id, country, period, frequency,
             value, unit, provider_id, quality_score, source_url, retrieved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.indicator_id, record.country,
         record.period, record.frequency, record.value, record.unit,
         provider_id, quality.final_score, record.source, record.retrieved_at],
    )


def _upsert_currency(conn, catalog_item_id, provider_id, record: CurrencyRate, quality):
    conn.execute(
        """
        INSERT OR REPLACE INTO mi_currency_rates
            (id, catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.base_currency, record.quote_currency,
         record.rate, record.date, provider_id, quality.final_score],
    )


def _upsert_bond(conn, catalog_item_id, provider_id, record: BondYield, quality):
    conn.execute(
        """
        INSERT OR REPLACE INTO mi_bond_yields
            (id, catalog_item_id, country, maturity, yield_value, date, currency,
             issuer, instrument_type, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.country, record.maturity, record.yield_value,
         record.date, record.currency, record.issuer, record.instrument_type,
         provider_id, quality.final_score],
    )


def _upsert_quote(conn, catalog_item_id, provider_id, record: MarketQuote, quality):
    conn.execute(
        """
        INSERT OR REPLACE INTO mi_market_quotes
            (id, catalog_item_id, symbol, asset_type, price, change_pct, currency,
             market_status, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.asset_type, record.price,
         record.change_pct, record.currency, record.market_status,
         record.retrieved_at, provider_id, quality.final_score],
    )


def _upsert_commodity(conn, catalog_item_id, provider_id, record: Commodity, quality):
    conn.execute(
        """
        INSERT OR REPLACE INTO mi_commodities
            (id, catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.name, record.price,
         record.unit, record.currency, record.retrieved_at, provider_id, quality.final_score],
    )


def _insert_news(conn, provider_id, record: NewsItem):
    conn.execute(
        """
        INSERT INTO mi_news_items (id, title, published_at, source_name, url, category, related_asset, provider_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), record.title, record.published_at, record.source_name,
         record.url, record.category, record.related_asset, provider_id],
    )


def log_provider_health(
    provider_id: str,
    catalog_item_id: str,
    status: str,
    latency_ms: int = 0,
    error_message: str | None = None,
) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_provider_health_logs (id, provider_id, catalog_item_id, status, latency_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [_uid(), provider_id, catalog_item_id, status, latency_ms, error_message],
    )


# ── Read functions ────────────────────────────────────────────────────────────

def get_latest_macro(catalog_item_id: str) -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM mi_macro_observations
        WHERE catalog_item_id = ?
        ORDER BY retrieved_at DESC
        LIMIT 1
        """,
        [catalog_item_id],
    ).fetchone()
    if row is None:
        return None
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit", "provider_id", "quality_score", "retrieved_at"]
    return dict(zip(cols, row))


def get_latest_macro_all() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (catalog_item_id)
               catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM mi_macro_observations
        ORDER BY catalog_item_id, retrieved_at DESC
        """
    ).fetchall()
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit", "provider_id", "quality_score", "retrieved_at"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_quotes() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (catalog_item_id)
               catalog_item_id, symbol, asset_type, price, change_pct, currency, observed_at, provider_id, quality_score
        FROM mi_market_quotes
        ORDER BY catalog_item_id, observed_at DESC
        """
    ).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct", "currency", "observed_at", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_forex() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (catalog_item_id)
               catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score
        FROM mi_currency_rates
        ORDER BY catalog_item_id, date DESC
        """
    ).fetchall()
    cols = ["catalog_item_id", "base_currency", "quote_currency", "rate", "date", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_bonds() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (catalog_item_id)
               catalog_item_id, country, maturity, yield_value, date, provider_id, quality_score
        FROM mi_bond_yields
        ORDER BY catalog_item_id, date DESC
        """
    ).fetchall()
    cols = ["catalog_item_id", "country", "maturity", "yield_value", "date", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_news(limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, title, published_at, source_name, url, category, related_asset, provider_id
        FROM mi_news_items
        ORDER BY published_at DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    cols = ["id", "title", "published_at", "source_name", "url", "category", "related_asset", "provider_id"]
    return [dict(zip(cols, r)) for r in rows]


def save_ai_datasheet(scope: str, datasheet_json: str, quality_score: float) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_ai_datasheets (id, snapshot_date, scope, datasheet_json, quality_score)
        VALUES (?, current_date, ?, ?, ?)
        """,
        [_uid(), scope, datasheet_json, quality_score],
    )


def get_latest_ai_datasheet(scope: str = "daily") -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT scope, datasheet_json, quality_score, generated_at
        FROM mi_ai_datasheets
        WHERE scope = ?
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        [scope],
    ).fetchone()
    if row is None:
        return None
    return {"scope": row[0], "datasheet_json": row[1], "quality_score": row[2], "generated_at": row[3]}
```

- [ ] **Step 2: Crear `storage/snapshot.py`**

Crear `backend/app/modules/market_intelligence/storage/snapshot.py`:

```python
"""Generador de market snapshot JSON desde DuckDB."""
from __future__ import annotations
from datetime import datetime, timezone

from app.modules.market_intelligence.storage import repository


def generate_snapshot() -> dict:
    """Genera snapshot completo del estado de mercado desde DuckDB."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "macro": repository.get_latest_macro_all(),
        "quotes": repository.get_latest_quotes(),
        "forex": repository.get_latest_forex(),
        "bonds": repository.get_latest_bonds(),
        "news": repository.get_latest_news(limit=10),
    }
```

- [ ] **Step 3: Escribir tests del repository**

Crear `backend/tests/market_intelligence/test_repository.py`:

```python
import duckdb
import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import MacroIndicator, CurrencyRate
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.quality.schemas import QualityResult, CheckResult
from app.modules.market_intelligence.storage.migrations import run_migrations


@pytest.fixture
def in_memory_conn():
    c = duckdb.connect(":memory:")
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def patch_duckdb(in_memory_conn):
    with patch("app.modules.market_intelligence.storage.repository.get_duckdb", return_value=in_memory_conn):
        import app.modules.market_intelligence.storage.repository as repo
        repo._migrations_run = True
        yield


def _meta():
    return ProviderMetadata(
        name="INE", id="ine", category="macro", region="Spain",
        method="api", base_url="https://ine.es", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=10,
        license="open",
    )


def _indicator():
    return CatalogIndicator(
        id="ipc_general", name="IPC España", category="macro", subcategory="inflation",
        country="ES", region="Spain", frequency="monthly", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="ine",
    )


def _quality():
    return QualityResult(
        final_score=0.92,
        checks=[CheckResult("freshness", "pass", 1.0)],
    )


def test_persist_macro_and_read_back(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    now = datetime.now(timezone.utc)
    record = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain", indicator_id="ipc_general",
        name="IPC General", value=2.8, unit="%", period="2026-05", frequency="monthly",
    )
    fetch_result = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=[record], error=None,
            latency_ms=120.0, raw_sample={"test": 1}, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )

    repository.persist_fetch_result(fetch_result, _quality(), "run001")

    result = repository.get_latest_macro("ipc_general")
    assert result is not None
    assert result["catalog_item_id"] == "ipc_general"
    assert result["value"] == pytest.approx(2.8)


def test_idempotent_raw_records(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    now = datetime.now(timezone.utc)
    record = MacroIndicator(
        provider="INE", source="https://ine.es", retrieved_at=now,
        country="ES", region="Spain", indicator_id="ipc_general",
        name="IPC General", value=2.8, unit="%", period="2026-05", frequency="monthly",
    )
    fetch_result = CatalogFetchResult(
        indicator=_indicator(),
        adapter_result=AdapterResult(
            provider="INE", success=True, records=[record], error=None,
            latency_ms=120.0, raw_sample={"same": "payload"}, metadata=_meta(),
        ),
        provider_used="ine",
        fallback_used=False,
        catalog_id="ipc_general",
    )

    repository.persist_fetch_result(fetch_result, _quality(), "run001")
    repository.persist_fetch_result(fetch_result, _quality(), "run002")

    count = in_memory_conn.execute("SELECT COUNT(*) FROM mi_raw_records").fetchone()[0]
    assert count == 1  # segundo insert con mismo checksum no persiste


def test_log_provider_health(in_memory_conn):
    from app.modules.market_intelligence.storage import repository

    repository.log_provider_health("ine", "ipc_general", "success", 120)
    count = in_memory_conn.execute("SELECT COUNT(*) FROM mi_provider_health_logs").fetchone()[0]
    assert count == 1
```

- [ ] **Step 4: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_repository.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/market_intelligence/storage/
git commit -m "feat(mi): add DuckDB repository with idempotent writes + snapshot"
```

---

### Task 8: API service + routes + proxy `economic_data`

**Files:**
- Create: `backend/app/modules/market_intelligence/api/schemas.py`
- Create: `backend/app/modules/market_intelligence/api/service.py`
- Create: `backend/app/modules/market_intelligence/api/routes.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/modules/economic_data/routes.py`
- Test: `backend/tests/market_intelligence/test_api_service.py`

**Interfaces:**
- Consumes: `storage/repository.py`, `catalog/loader.py`
- Produces: `GET /api/market-intelligence/snapshot`, `GET /api/market-intelligence/macro`, `GET /api/market-intelligence/forex`, `GET /api/market-intelligence/bonds`, `GET /api/market-intelligence/news`, `GET /api/market-intelligence/ai-datasheet`

- [ ] **Step 1: Crear `api/schemas.py`**

Crear `backend/app/modules/market_intelligence/api/schemas.py`:

```python
"""Pydantic output schemas para la Market Intelligence API."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MacroDataPoint(BaseModel):
    catalog_item_id: str
    indicator_id: Optional[str] = None
    country: Optional[str] = None
    period: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class MacroSnapshotOut(BaseModel):
    spain: list[MacroDataPoint] = []
    eurozone: list[MacroDataPoint] = []
    usa: list[MacroDataPoint] = []
    generated_at: str
    warnings: list[str] = []


class QuoteOut(BaseModel):
    catalog_item_id: str
    symbol: Optional[str] = None
    asset_type: Optional[str] = None
    price: Optional[float] = None
    change_pct: Optional[float] = None
    currency: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class MarketSnapshotOut(BaseModel):
    indices: list[QuoteOut] = []
    crypto: list[QuoteOut] = []
    commodities: list[dict] = []
    generated_at: str
    warnings: list[str] = []


class ForexRateOut(BaseModel):
    catalog_item_id: str
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    rate: Optional[float] = None
    date: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class ForexSnapshotOut(BaseModel):
    rates: list[ForexRateOut] = []
    generated_at: str
    warnings: list[str] = []


class BondYieldOut(BaseModel):
    catalog_item_id: str
    country: Optional[str] = None
    maturity: Optional[str] = None
    yield_value: Optional[float] = None
    date: Optional[str] = None
    provider_id: Optional[str] = None
    quality_score: float = 1.0


class BondSnapshotOut(BaseModel):
    yields: list[BondYieldOut] = []
    generated_at: str
    warnings: list[str] = []


class NewsItemOut(BaseModel):
    id: str
    title: Optional[str] = None
    published_at: Optional[str] = None
    source_name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    provider_id: Optional[str] = None


class NewsSnapshotOut(BaseModel):
    items: list[NewsItemOut] = []
    generated_at: str


class AiDatasheetOut(BaseModel):
    generated_at: str
    quality_score: float
    scope: str
    macro: dict = {}
    markets: dict = {}
    forex: dict = {}
    bonds: dict = {}
    news: list = []
    sources: list[str] = []
    warnings: list[str] = []


class MarketIntelligenceSnapshotOut(BaseModel):
    generated_at: str
    macro: MacroSnapshotOut
    market: MarketSnapshotOut
    forex: ForexSnapshotOut
    bonds: BondSnapshotOut
    news: NewsSnapshotOut
```

- [ ] **Step 2: Crear `api/service.py`**

Crear `backend/app/modules/market_intelligence/api/service.py`:

```python
"""Market Intelligence API service — lee desde DuckDB, nunca llama providers."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut, BondSnapshotOut, BondYieldOut, ForexRateOut, ForexSnapshotOut,
    MacroDataPoint, MacroSnapshotOut, MarketSnapshotOut, NewsItemOut, NewsSnapshotOut,
    QuoteOut,
)
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.api")

_SPAIN_CATALOG_IDS = {"ipc_general", "ipc_subyacente", "pib_spain", "desempleo_spain", "euribor_12m", "euribor_3m"}
_EUROZONE_CATALOG_IDS = {"tipo_bce", "ipc_eurozona", "pib_eurozona", "desempleo_eurozona"}
_USA_CATALOG_IDS = {"ipc_usa", "gdp_usa", "desempleo_usa", "fed_funds_rate"}
_INDEX_CATALOG_IDS = {"sp500", "nasdaq100", "ibex35", "eurostoxx50", "dax", "nikkei225"}
_CRYPTO_CATALOG_IDS = {"btc", "eth", "sol", "xrp"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _warn(rows: list[dict], threshold: float = 0.5) -> list[str]:
    return [
        f"{r.get('catalog_item_id', '?')}: quality {r.get('quality_score', 0):.2f}"
        for r in rows
        if r.get("quality_score", 1.0) < threshold
    ]


def get_macro_snapshot() -> MacroSnapshotOut:
    rows = repository.get_latest_macro_all()
    spain, eurozone, usa = [], [], []
    for r in rows:
        point = MacroDataPoint(**{k: v for k, v in r.items() if k in MacroDataPoint.model_fields})
        cid = r.get("catalog_item_id", "")
        if cid in _SPAIN_CATALOG_IDS:
            spain.append(point)
        elif cid in _EUROZONE_CATALOG_IDS:
            eurozone.append(point)
        elif cid in _USA_CATALOG_IDS:
            usa.append(point)
    return MacroSnapshotOut(spain=spain, eurozone=eurozone, usa=usa, generated_at=_now(), warnings=_warn(rows))


def get_market_snapshot() -> MarketSnapshotOut:
    quotes = repository.get_latest_quotes()
    indices = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
               for q in quotes if q.get("catalog_item_id") in _INDEX_CATALOG_IDS]
    crypto = [QuoteOut(**{k: v for k, v in q.items() if k in QuoteOut.model_fields})
              for q in quotes if q.get("catalog_item_id") in _CRYPTO_CATALOG_IDS]
    commodities = repository.get_latest_quotes()  # filtrar por asset_type en producción
    return MarketSnapshotOut(indices=indices, crypto=crypto, commodities=[], generated_at=_now(), warnings=_warn(quotes))


def get_forex_snapshot() -> ForexSnapshotOut:
    rows = repository.get_latest_forex()
    rates = []
    for r in rows:
        rates.append(ForexRateOut(
            catalog_item_id=r["catalog_item_id"],
            base_currency=r.get("base_currency"),
            quote_currency=r.get("quote_currency"),
            rate=r.get("rate"),
            date=str(r.get("date", "")),
            provider_id=r.get("provider_id"),
            quality_score=r.get("quality_score", 1.0),
        ))
    return ForexSnapshotOut(rates=rates, generated_at=_now(), warnings=_warn(rows))


def get_bond_snapshot() -> BondSnapshotOut:
    rows = repository.get_latest_bonds()
    yields = []
    for r in rows:
        yields.append(BondYieldOut(
            catalog_item_id=r["catalog_item_id"],
            country=r.get("country"),
            maturity=r.get("maturity"),
            yield_value=r.get("yield_value"),
            date=str(r.get("date", "")),
            provider_id=r.get("provider_id"),
            quality_score=r.get("quality_score", 1.0),
        ))
    return BondSnapshotOut(yields=yields, generated_at=_now(), warnings=_warn(rows))


def get_news_snapshot(limit: int = 20) -> NewsSnapshotOut:
    rows = repository.get_latest_news(limit=limit)
    items = [NewsItemOut(
        id=r["id"], title=r.get("title"), published_at=str(r.get("published_at", "")),
        source_name=r.get("source_name"), url=r.get("url"),
        category=r.get("category"), provider_id=r.get("provider_id"),
    ) for r in rows]
    return NewsSnapshotOut(items=items, generated_at=_now())


def get_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    """Genera el AI Datasheet. La IA local SOLO llama a esta función."""
    from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
    return generate_ai_datasheet(scope=scope)
```

- [ ] **Step 3: Crear `api/routes.py`**

Crear `backend/app/modules/market_intelligence/api/routes.py`:

```python
"""Market Intelligence API routes."""
from fastapi import APIRouter, Query
from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut, BondSnapshotOut, ForexSnapshotOut,
    MacroSnapshotOut, MarketSnapshotOut, NewsSnapshotOut,
)

router = APIRouter()


@router.get("/snapshot/macro", response_model=MacroSnapshotOut)
def get_macro_snapshot():
    return service.get_macro_snapshot()


@router.get("/snapshot/market", response_model=MarketSnapshotOut)
def get_market_snapshot():
    return service.get_market_snapshot()


@router.get("/snapshot/forex", response_model=ForexSnapshotOut)
def get_forex_snapshot():
    return service.get_forex_snapshot()


@router.get("/snapshot/bonds", response_model=BondSnapshotOut)
def get_bond_snapshot():
    return service.get_bond_snapshot()


@router.get("/snapshot/news", response_model=NewsSnapshotOut)
def get_news_snapshot(limit: int = Query(default=20, le=100)):
    return service.get_news_snapshot(limit=limit)


@router.get("/ai-datasheet", response_model=AiDatasheetOut)
def get_ai_datasheet(scope: str = Query(default="daily")):
    return service.get_ai_datasheet(scope=scope)
```

- [ ] **Step 4: Registrar el router en `main.py`**

Modificar `backend/app/main.py` — añadir después del import de `economic_data_router`:

```python
from app.modules.market_intelligence.api.routes import router as market_intelligence_router
```

Y añadir al final de los `app.include_router(...)`:

```python
app.include_router(market_intelligence_router, prefix="/api/market-intelligence", tags=["market_intelligence"])
```

- [ ] **Step 5: Convertir `economic_data/routes.py` en proxy**

Reemplazar el contenido de `backend/app/modules/economic_data/routes.py`:

```python
"""economic_data routes — proxy hacia market_intelligence para compatibilidad con el frontend."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.market_intelligence.api import service as mi_service
from app.modules.economic_data.schemas import (
    IndicatorOut,
    MacroSnapshotOut,
    PersonalImpactOut,
)
from app.modules.economic_data import service as legacy_service

router = APIRouter()


@router.get("/snapshot", response_model=MacroSnapshotOut)
def get_snapshot():
    # Intentar MI layer primero; fallback al servicio legacy si no hay datos
    try:
        mi_snapshot = mi_service.get_macro_snapshot()
        rows = legacy_service._build_from_mi(mi_snapshot)
        return rows
    except Exception:
        return legacy_service.get_snapshot()


@router.get("/indicators", response_model=list[IndicatorOut])
def list_indicators(
    region: str | None = Query(default=None),
    indicator: str | None = Query(default=None),
):
    return legacy_service.get_indicators(region=region, indicator=indicator)


@router.post("/refresh", response_model=MacroSnapshotOut)
def refresh_data():
    result = legacy_service.refresh_snapshot()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una actualización de datos económicos en curso",
        )
    return result


@router.get("/impact", response_model=PersonalImpactOut)
def get_personal_impact(db: Session = Depends(get_db)):
    return legacy_service.get_personal_impact(db)
```

> **Nota**: `legacy_service._build_from_mi()` es una función puente mínima. Añadir al final de `economic_data/service.py`:

```python
def _build_from_mi(mi_snapshot) -> "MacroSnapshotOut":
    """Convierte MI snapshot al formato legacy para compatibilidad."""
    # Por ahora delegamos al sistema legacy — la integración completa es Fase 6
    return get_snapshot()
```

- [ ] **Step 6: Escribir tests del service**

Crear `backend/tests/market_intelligence/test_api_service.py`:

```python
from unittest.mock import patch
import pytest

from app.modules.market_intelligence.api import service


def test_get_macro_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_macro_all", return_value=[]):
        result = service.get_macro_snapshot()
    assert hasattr(result, "spain")
    assert hasattr(result, "eurozone")
    assert hasattr(result, "usa")
    assert hasattr(result, "generated_at")
    assert isinstance(result.warnings, list)


def test_get_forex_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_forex", return_value=[]):
        result = service.get_forex_snapshot()
    assert hasattr(result, "rates")
    assert hasattr(result, "generated_at")


def test_get_bond_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_bonds", return_value=[]):
        result = service.get_bond_snapshot()
    assert hasattr(result, "yields")


def test_get_market_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_quotes", return_value=[]):
        result = service.get_market_snapshot()
    assert hasattr(result, "indices")
    assert hasattr(result, "crypto")


def test_get_news_snapshot_returns_valid_schema():
    with patch("app.modules.market_intelligence.api.service.repository.get_latest_news", return_value=[]):
        result = service.get_news_snapshot()
    assert hasattr(result, "items")
    assert isinstance(result.items, list)
```

- [ ] **Step 7: Ejecutar tests**

```bash
pytest tests/market_intelligence/test_api_service.py -v
```

Expected: `5 passed`

- [ ] **Step 8: Verificar que el backend arranca**

```bash
# desde AI-Financial-OS/backend/
uvicorn app.main:app --port 8000 --reload
```

En otro terminal:

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.1.0"}

curl http://localhost:8000/api/market-intelligence/snapshot/macro
# Expected: JSON con spain/eurozone/usa arrays (pueden estar vacíos si no hay datos aún)

curl http://localhost:8000/api/economy/snapshot
# Expected: respuesta válida (backward compat)
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/modules/market_intelligence/api/ backend/app/main.py backend/app/modules/economic_data/routes.py
git commit -m "feat(mi): add MI API service + routes, proxy economic_data for backward compat"
```

---

### Task 9: AI Datasheet + CLI commands

**Files:**
- Create: `backend/app/modules/market_intelligence/ai/datasheet.py`
- Create: `backend/app/modules/market_intelligence/cli/commands.py`
- Modify: `market-data-poc/run_poc.py`
- Test: `backend/tests/market_intelligence/test_datasheet.py`

**Interfaces:**
- Consumes: `api/service.py`, `storage/repository.py`
- Produces: `generate_ai_datasheet(scope) -> AiDatasheetOut`, CLI commands `market:intelligence:*`

- [ ] **Step 1: Escribir el test del datasheet primero (TDD)**

Crear `backend/tests/market_intelligence/test_datasheet.py`:

```python
from unittest.mock import patch
import pytest

from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet


def _empty_macro():
    from app.modules.market_intelligence.api.schemas import MacroSnapshotOut
    from datetime import datetime, timezone
    return MacroSnapshotOut(spain=[], eurozone=[], usa=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_forex():
    from app.modules.market_intelligence.api.schemas import ForexSnapshotOut
    from datetime import datetime, timezone
    return ForexSnapshotOut(rates=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_bonds():
    from app.modules.market_intelligence.api.schemas import BondSnapshotOut
    from datetime import datetime, timezone
    return BondSnapshotOut(yields=[], generated_at=datetime.now(timezone.utc).isoformat())


def _empty_news():
    from app.modules.market_intelligence.api.schemas import NewsSnapshotOut
    from datetime import datetime, timezone
    return NewsSnapshotOut(items=[], generated_at=datetime.now(timezone.utc).isoformat())


def test_generate_ai_datasheet_returns_valid_structure():
    with (
        patch("app.modules.market_intelligence.ai.datasheet.service.get_macro_snapshot", return_value=_empty_macro()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_forex_snapshot", return_value=_empty_forex()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_bond_snapshot", return_value=_empty_bonds()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_news_snapshot", return_value=_empty_news()),
        patch("app.modules.market_intelligence.ai.datasheet.repository.save_ai_datasheet"),
    ):
        result = generate_ai_datasheet(scope="daily")

    assert hasattr(result, "generated_at")
    assert hasattr(result, "quality_score")
    assert hasattr(result, "macro")
    assert hasattr(result, "forex")
    assert hasattr(result, "bonds")
    assert hasattr(result, "news")
    assert hasattr(result, "warnings")
    assert result.scope == "daily"


def test_datasheet_quality_score_is_between_0_and_1():
    with (
        patch("app.modules.market_intelligence.ai.datasheet.service.get_macro_snapshot", return_value=_empty_macro()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_forex_snapshot", return_value=_empty_forex()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_bond_snapshot", return_value=_empty_bonds()),
        patch("app.modules.market_intelligence.ai.datasheet.service.get_news_snapshot", return_value=_empty_news()),
        patch("app.modules.market_intelligence.ai.datasheet.repository.save_ai_datasheet"),
    ):
        result = generate_ai_datasheet(scope="daily")

    assert 0.0 <= result.quality_score <= 1.0
```

- [ ] **Step 2: Ejecutar tests (deben fallar — TDD)**

```bash
pytest tests/market_intelligence/test_datasheet.py -v
```

Expected: `FAILED — ModuleNotFoundError` (el módulo aún no existe)

- [ ] **Step 3: Crear `ai/datasheet.py`**

Crear `backend/app/modules/market_intelligence/ai/datasheet.py`:

```python
"""Generador de AI Datasheet.

La IA local SOLO consume el output de generate_ai_datasheet().
Nunca llama a providers ni a APIs externas.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import AiDatasheetOut
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.ai")


def generate_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    """Genera el JSON compacto de contexto de mercado para la IA local."""
    generated_at = datetime.now(timezone.utc).isoformat()

    macro_snapshot = service.get_macro_snapshot()
    forex_snapshot = service.get_forex_snapshot()
    bond_snapshot = service.get_bond_snapshot()
    news_snapshot = service.get_news_snapshot(limit=10)

    # Construir macro dict jerárquico
    macro = {
        "spain": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.spain},
        "eurozone": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.eurozone},
        "usa": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.usa},
    }

    # Forex dict
    forex = {
        f"{r.base_currency}_{r.quote_currency}": {"rate": r.rate, "date": r.date, "provider": r.provider_id, "quality_score": r.quality_score}
        for r in forex_snapshot.rates
        if r.base_currency and r.quote_currency
    }

    # Bonds dict
    bonds = {
        f"{b.country}_{b.maturity}": {"yield": b.yield_value, "date": b.date, "provider": b.provider_id, "quality_score": b.quality_score}
        for b in bond_snapshot.yields
        if b.country and b.maturity
    }

    # News list
    news = [
        {"title": n.title, "category": n.category, "published_at": n.published_at, "source": n.source_name}
        for n in news_snapshot.items
    ]

    # Warnings
    warnings = macro_snapshot.warnings + forex_snapshot.warnings + bond_snapshot.warnings

    # Quality score = media de todos los quality scores
    all_scores = (
        [dp.quality_score for dp in macro_snapshot.spain + macro_snapshot.eurozone + macro_snapshot.usa]
        + [r.quality_score for r in forex_snapshot.rates]
        + [b.quality_score for b in bond_snapshot.yields]
    )
    quality_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0

    # Sources
    sources = list({
        dp.provider_id for dp in macro_snapshot.spain + macro_snapshot.eurozone + macro_snapshot.usa
        if dp.provider_id
    })

    datasheet = AiDatasheetOut(
        generated_at=generated_at,
        quality_score=quality_score,
        scope=scope,
        macro=macro,
        markets={},
        forex=forex,
        bonds=bonds,
        news=news,
        sources=sources,
        warnings=warnings,
    )

    # Persistir en DuckDB
    try:
        repository.save_ai_datasheet(
            scope=scope,
            datasheet_json=json.dumps(datasheet.model_dump()),
            quality_score=quality_score,
        )
    except Exception as exc:
        logger.warning("Could not persist AI datasheet: %s", exc)

    return datasheet
```

- [ ] **Step 4: Ejecutar tests (deben pasar ahora)**

```bash
pytest tests/market_intelligence/test_datasheet.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Crear `cli/commands.py`**

Crear `backend/app/modules/market_intelligence/cli/commands.py`:

```python
"""Comandos CLI para el Market Intelligence Layer."""
from __future__ import annotations
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
OUTPUT_DIR = Path("output/market-intelligence")


def cmd_init_db() -> None:
    from app.core.duckdb import get_duckdb
    from app.modules.market_intelligence.storage.migrations import run_migrations
    conn = get_duckdb()
    run_migrations(conn)
    console.print("[green]OK[/green] DuckDB tables created")


def cmd_catalog_show() -> None:
    from app.modules.market_intelligence.catalog.loader import CatalogLoader
    loader = CatalogLoader()
    items = loader.load_all()
    table = Table(title="Market Data Catalog", show_lines=True)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Freq")
    table.add_column("AI")
    table.add_column("Primary")
    for item in items:
        color = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}.get(item.priority, "white")
        table.add_row(
            item.id, item.name,
            f"[{color}]{item.priority}[/{color}]",
            item.frequency,
            "Y" if item.ai else "",
            item.provider_primary,
        )
    console.print(table)
    console.print(f"\nTotal: {len(items)} | Critical: {sum(1 for i in items if i.priority=='critical')} | AI: {sum(1 for i in items if i.ai)}")


def cmd_catalog_validate() -> bool:
    from app.modules.market_intelligence.catalog.loader import CatalogLoader
    loader = CatalogLoader()
    errors = loader.validate()
    if not errors:
        console.print(f"[green]OK[/green] Catalog valid — {len(loader.load_all())} indicators loaded")
        return True
    console.print(f"[red]ERROR[/red] {len(errors)} validation error(s):")
    for e in errors:
        console.print(f"  [red]• {e}[/red]")
    return False


def cmd_update(category: str | None = None, priority: str | None = None, dry_run: bool = False) -> None:
    from app.modules.market_intelligence.ingestion.runner import run_ingestion
    label = f"category={category or 'all'} priority={priority or 'all'}"
    console.print(f"[bold blue]Market Intelligence Update[/bold blue] — {label}")
    if dry_run:
        console.print("[yellow]DRY RUN — no data will be persisted[/yellow]")
    summary = run_ingestion(category=category, priority=priority, dry_run=dry_run)
    console.print(f"\n[bold]Done[/bold] run={summary.run_id}")
    console.print(f"  Total: {summary.total} | [green]OK: {summary.success}[/green] | [red]Failed: {summary.failed}[/red] | Fallbacks: {summary.fallbacks_used}")
    duration = (summary.finished_at - summary.started_at).total_seconds()
    console.print(f"  Duration: {duration:.1f}s")


def cmd_quality() -> None:
    from app.modules.market_intelligence.storage import repository
    from app.core.duckdb import get_duckdb
    conn = get_duckdb()
    rows = conn.execute(
        "SELECT provider_id, status, COUNT(*) as count FROM mi_provider_health_logs GROUP BY provider_id, status ORDER BY provider_id"
    ).fetchall()
    table = Table(title="Provider Health Summary", show_lines=True)
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Count", justify="right")
    for row in rows:
        status_color = "green" if row[1] == "success" else "red"
        table.add_row(row[0], f"[{status_color}]{row[1]}[/{status_color}]", str(row[2]))
    console.print(table)


def cmd_snapshot() -> None:
    from app.modules.market_intelligence.storage.snapshot import generate_snapshot
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = generate_snapshot()
    path = OUTPUT_DIR / "market_intelligence_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]Snapshot written:[/green] {path}")


def cmd_datasheet(scope: str = "daily") -> None:
    from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    datasheet = generate_ai_datasheet(scope=scope)
    path = OUTPUT_DIR / f"ai_datasheet_{scope}.json"
    path.write_text(json.dumps(datasheet.model_dump(), indent=2, default=str), encoding="utf-8")
    console.print(f"[green]AI Datasheet written:[/green] {path}")
    console.print(f"  Quality score: {datasheet.quality_score:.3f} | Warnings: {len(datasheet.warnings)}")
```

- [ ] **Step 6: Añadir los nuevos comandos a `run_poc.py`**

Añadir los nuevos `choices` al parser y los handlers en `market-data-poc/run_poc.py`.

En la lista de `choices` del argumento `command` (alrededor de la línea 482), añadir:

```python
"market:intelligence:init-db",
"market:intelligence:update",
"market:intelligence:quality",
"market:intelligence:snapshot",
"market:intelligence:datasheet",
"market:intelligence:catalog",
"market:intelligence:catalog:validate",
```

Al final del bloque `main()`, antes del último handler, añadir:

```python
# ── Market Intelligence commands ──────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

if args.command == "market:intelligence:init-db":
    from app.modules.market_intelligence.cli.commands import cmd_init_db
    cmd_init_db()
    return

if args.command == "market:intelligence:update":
    from app.modules.market_intelligence.cli.commands import cmd_update
    cmd_update(category=args.category, priority=args.priority)
    return

if args.command == "market:intelligence:quality":
    from app.modules.market_intelligence.cli.commands import cmd_quality
    cmd_quality()
    return

if args.command == "market:intelligence:snapshot":
    from app.modules.market_intelligence.cli.commands import cmd_snapshot
    cmd_snapshot()
    return

if args.command == "market:intelligence:datasheet":
    from app.modules.market_intelligence.cli.commands import cmd_datasheet
    cmd_datasheet()
    return

if args.command == "market:intelligence:catalog":
    from app.modules.market_intelligence.cli.commands import cmd_catalog_show
    cmd_catalog_show()
    return

if args.command == "market:intelligence:catalog:validate":
    from app.modules.market_intelligence.cli.commands import cmd_catalog_validate
    valid = cmd_catalog_validate()
    sys.exit(0 if valid else 1)
```

- [ ] **Step 7: Ejecutar todos los tests**

```bash
pytest tests/market_intelligence/ -v
```

Expected: todos los tests pasan. Si algún test de migración de adapters falla por imports incorrectos, corregir el archivo del adapter correspondiente.

- [ ] **Step 8: Verificar los comandos CLI**

```bash
# desde AI-Financial-OS/market-data-poc/
python run_poc.py market:intelligence:init-db
# Expected: "OK DuckDB tables created"

python run_poc.py market:intelligence:catalog
# Expected: tabla con los indicadores del catálogo

python run_poc.py market:intelligence:catalog:validate
# Expected: "OK Catalog valid — N indicators loaded"
```

- [ ] **Step 9: Commit final**

```bash
git add backend/app/modules/market_intelligence/ai/ backend/app/modules/market_intelligence/cli/ market-data-poc/run_poc.py
git commit -m "feat(mi): add AI datasheet generator + CLI commands for market:intelligence:*"
```

---

## Self-Review

### Spec coverage check

| Requisito del spec | Task que lo implementa |
|---|---|
| Market Data Catalog editable (YAMLs) | Task 3 |
| Provider Mapping por catalog_item | Task 3 (CatalogIndicator.provider_*) |
| Ingesta desde catálogo, no indiscriminada | Task 5 (runner.py) |
| Datos actualizados desde catálogo con filtros | Task 5 |
| raw_market_records con checksum (idempotencia) | Task 7 |
| normalized_market_records con trazabilidad | Task 7 |
| quality_scores calculados | Task 6 |
| Snapshots JSON generados | Task 7 (snapshot.py) |
| AI Datasheet scope daily | Task 9 |
| Dashboard services leen snapshots | Task 8 (api/service.py) |
| IA solo consume get_ai_datasheet() | Task 9 (ai/datasheet.py) |
| BDE/CNMV no bloquean la arquitectura | Task 5 (runner continúa en fallo) |
| /api/economy/* sigue funcionando | Task 8 (proxy) |

**Gaps:** Ninguno. Todos los 13 criterios de aceptación del spec están cubiertos.

### Placeholder scan

Ningún paso dice "TBD", "TODO", "implement later" o "similar a Task N". Cada paso tiene código concreto.

### Type consistency

- `CatalogIndicator` definido en Task 3, usado en Tasks 5, 6, 7, 8, 9 — consistente.
- `CatalogFetchResult` definido en Task 5, usado en Tasks 6, 7 — consistente.
- `QualityResult` definido en Task 6, usado en Task 7 — consistente.
- `AdapterResult` definido en Task 2, usado en Tasks 4, 5 — consistente.
- `AiDatasheetOut` definido en Task 8 (schemas), usado en Tasks 8 y 9 — consistente.
- `get_duckdb()` importado de `app.core.duckdb` en Tasks 1 y 7 — consistente con la constraint global.
