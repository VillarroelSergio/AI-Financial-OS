# 12 — Development Workflow

## Objetivo

Definir cómo se desarrolla el proyecto localmente con Visual Studio Code y Claude Code.

## Principios

- Desarrollo incremental.
- Fases pequeñas.
- Cambios revisables.
- No mezclar arquitectura, UI e IA en una misma tarea grande.
- Mantener documentación actualizada.
- Tests para importadores y cálculos.

## Orquestación local

El proyecto debe poder levantarse con scripts.

Comandos recomendados:

```txt
npm run dev
npm run dev:desktop
npm run dev:backend
npm run lint
npm run test
npm run build
```

## Backend

Gestor recomendado:

- `uv` o `poetry`.

Comandos internos:

```txt
uv run fastapi dev app/main.py
uv run pytest
uv run ruff check
```

## Frontend

```txt
npm install
npm run dev
npm run tauri dev
```

## Variables de entorno

Crear `.env.example` con:

```txt
APP_ENV=development
DATABASE_URL=sqlite:///./data/financial.db
DUCKDB_PATH=./data/analytics.duckdb
OLLAMA_BASE_URL=http://localhost:11434
LM_STUDIO_BASE_URL=http://localhost:1234/v1
DEFAULT_AI_MODEL=qwen
```

## Branching

Para vibe coding local, se recomienda trabajar por bloques:

```txt
feature/foundation
feature/financial-core
feature/import-center
feature/monefy-importer
feature/overview-dashboard
feature/economy-module
feature/ai-provider-abstraction
```

## Definition of Done

Una tarea se considera terminada si:

- Compila.
- No rompe rutas existentes.
- Tiene manejo de loading/error/empty state.
- Tiene tipos definidos.
- Tiene tests cuando hay lógica de parsing/cálculo.
- Actualiza documentación si cambia arquitectura o contrato.
- No introduce dependencias cloud obligatorias.

## Testing mínimo

### Backend

- Tests de servicios financieros.
- Tests de importación Monefy.
- Tests de validación CSV.
- Tests de duplicados.
- Tests de endpoints críticos.

### Frontend

- Tests ligeros de componentes críticos si procede.
- Validar navegación.
- Validar estados vacíos.

## Calidad

Frontend:

- TypeScript estricto.
- ESLint.
- Prettier.

Backend:

- Ruff.
- Pytest.
- Type hints.
- Pydantic.

## Reglas para Claude Code

Claude debe:

- Leer `/docs` antes de implementar.
- Respetar fases.
- No implementar IA si la tarea es de core financiero.
- No introducir automatización bancaria.
- No cambiar stack sin justificar.
- No crear pantallas sobrecargadas.
- Actualizar docs si cambia una decisión.

## Empaquetado futuro

El empaquetado Windows se deja para fases finales.

Debe incluir:

- Backend embebido o proceso local orquestado.
- Base de datos local.
- Configuración inicial.
- Ruta de datos clara.
