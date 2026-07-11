# 03 — Architecture

## Principios

- Local-first.
- Modularidad estricta.
- Separación entre cálculo determinista e IA.
- Importación manual por seguridad.
- Datos personales en local.
- Datos de mercado y macro online opcionales con caché local.
- Backend como fuente de verdad.
- Frontend sin lógica financiera crítica.

## Stack

### Desktop

- Tauri.
- React.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- Recharts.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy o SQLModel.
- SQLite.
- DuckDB.
- ChromaDB futuro.

### IA

- Ollama.
- LM Studio.
- Qwen como modelo inicial.
- Abstracción multi-provider.

## Arquitectura lógica

```txt
Tauri Desktop App
 ├─ React UI
 ├─ API Client
 └─ Local runtime orchestration

FastAPI Backend
 ├─ Financial Core
 ├─ Import Center
 ├─ Analytics Engine
 ├─ Investment Module
 ├─ Market Intelligence Module (catalog + ingestion + quality + storage + AI datasheet)
 ├─ AI Service
 ├─ RAG Service future
 └─ Security / Settings

Storage
 ├─ SQLite: datos principales + Market Intelligence (`mi_*`, WAL, ECO-3b)
 ├─ DuckDB: analítica de financial_knowledge
 ├─ ChromaDB: embeddings y documentos futuros
 └─ File Storage: imports/documentos
```

## Estructura recomendada del repositorio

```txt
ai-financial-os/
  apps/
    desktop/
      src/
      src-tauri/
      package.json

  backend/
    app/
      main.py
      core/
      modules/
      services/
      infrastructure/
      tests/
    pyproject.toml

  docs/
  scripts/
  .env.example
  README.md
```

## Backend modules

```txt
backend/app/modules/
  accounts/
  categories/
  transactions/
  imports/
  dashboard/
  investments/
  market_intelligence/  # catalog/, ingestion/, quality/, storage/, api/, ai/, cli/
  goals/
  insights/
  ai/
  rag/
  settings/
```

Cada módulo debe incluir, cuando aplique:

```txt
models.py
schemas.py
repository.py
service.py
routes.py
```

## Frontend modules

```txt
apps/desktop/src/
  app/
    routes/
    layout/
    providers/

  features/
    overview/
    spending/
    transactions/
    accounts/
    imports/
    investments/
    economy/
    markets/
    goals/
    insights/
    assistant/
    settings/

  components/
    ui/
    layout/
    charts/
    financial/
    import/

  lib/
    api/
    formatters/
    hooks/
    types/
```

## Flujo de datos

```txt
CSV importado
 → Import Center
 → Parser específico
 → Normalización
 → Preview
 → Validación
 → Confirmación usuario
 → SQLite
 → Analytics Service
 → Dashboard API
 → React UI
```

## Uso de SQLite y DuckDB

SQLite será la fuente transaccional principal.

DuckDB queda restringido a `financial_knowledge` (analítica, consultas temporales, procesamiento de CSV, datasets para dashboards).

> **ECO-3b:** Market Intelligence (tablas `mi_*`) migró de DuckDB a **SQLite WAL** (`data/market_intelligence.db`).
> Motivo: DuckDB es mono-escritor y cae a memoria si un segundo proceso abre el archivo; WAL elimina esa fragilidad y el volumen (~72 indicadores, decenas de filas/día) hace irrelevante la ventaja columnar.

**Reglas Market Intelligence (SQLite):**
- Acceder via `app.modules.market_intelligence.storage.db.get_conn()` — conexión única compartida, WAL, autocommit.
- Upserts con DELETE + INSERT.
- Latest reads con subconsulta `ROW_NUMBER() OVER (...)` filtrando `rn = 1` (SQLite no tiene `QUALIFY`).

**Reglas DuckDB (solo financial_knowledge):**
- Acceder via el singleton `app.core.duckdb.get_duckdb()` — nunca `duckdb.connect()` directo en producción.

## Market Intelligence

`backend/app/modules/market_intelligence/` es la fuente vigente para contexto macro,
mercados, divisas, bonos, noticias y datasheets para IA local.

```txt
Catalog YAML
 → CatalogLoader
 → ProviderOrchestrator
 → AdapterResult
 → QualityEngine
 → Repository SQLite (`mi_*`)
 → API `/api/market-intelligence/*`
 → React UI / AI datasheet
```

El POC `market-data-poc/` se conserva como referencia tecnica y banco de pruebas, pero
no debe documentarse como ruta operativa principal.

## Fase 6.4 - Integridad de datos y UX core

Reglas vigentes:

- Los IDs internos y UUID no son labels de usuario. En inversiones, el backend entrega `display_name`, `symbol`, `is_mock`, `quality_score` y `warnings`.
- Un holding sin nombre ni simbolo se presenta como "Activo sin identificar".
- Los datos `mock`, `demo` o `seed` deben marcarse en UI y no mezclarse con totales reales sin accion explicita del usuario.
- Market Intelligence expone snapshots honestos por seccion: indices, crypto, commodities, forex y bonds. La UI muestra provider, quality score, ultima actualizacion y estado parcial cuando aplique.
- Gastos calcula porcentajes contra gasto total del periodo: `categoryAmount / totalExpense * 100`.
- Cada pantalla core debe tener loading, empty, partial/error state y copy que no prometa tiempo real cuando el dato sea baseline, stale o seed.

## Uso de IA

La IA no puede consultar SQL directamente. Debe usar tools expuestas por el backend.

```txt
Usuario pregunta
 → AI Panel
 → AI Service
 → Tool Router
 → Financial/Economic Services
 → Respuesta estructurada
 → LLM redacta explicación
 → UI muestra respuesta + datos usados
```

## No permitido

- Automatización bancaria.
- Scraping de bancos.
- Guardar credenciales bancarias.
- Cloud obligatorio.
- Cálculos financieros críticos hechos solo por el LLM.
- SQL generado libremente por el modelo contra datos personales.
