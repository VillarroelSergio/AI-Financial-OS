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
 ├─ Market Data Module (providers + ConsensusEngine + RequestBudget + DuckDB cache)
 ├─ Economic Intelligence Module
 ├─ AI Service
 ├─ RAG Service future
 └─ Security / Settings

Storage
 ├─ SQLite: datos principales
 ├─ DuckDB: analítica y consultas agregadas
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
  market_data/          # providers/, consensus.py, budget.py, router.py, cache.py
  economic_data/
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

DuckDB se usará para:

- Agregaciones analíticas.
- Consultas temporales complejas.
- Procesamiento de CSV.
- Preparación de datasets para dashboards.

Regla: no duplicar lógica de negocio en DuckDB si ya existe en servicios deterministas.

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
