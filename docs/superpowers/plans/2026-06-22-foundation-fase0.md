# AI Financial OS — Fase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold el monorepo AI Financial OS completo con FastAPI respondiendo `/health` y una app Tauri+React con sidebar, navegación base y design tokens del sistema Revolut adaptado.

**Architecture:** Monorepo con `apps/desktop` (Tauri v2 + React 18 + TypeScript + Tailwind) y `backend` (FastAPI + SQLite + DuckDB). El backend escucha en `http://127.0.0.1:8000`; el servidor Vite de Tauri en el puerto 1420. No hay lógica financiera — solo estructura, routing, design tokens y un endpoint `/health`. Los 13 módulos backend existen como routers vacíos registrados en `main.py`.

**Tech Stack:** Tauri v2, React 18, TypeScript 5.6, Vite 6, Tailwind CSS 3, React Router v6, lucide-react, FastAPI 0.115+, SQLAlchemy 2, DuckDB 1.1+, pydantic-settings 2, uv (Python package manager), Rust stable

## Global Constraints

- OS: Windows 11; scripts en PowerShell 5.1
- Python ≥ 3.11 — gestor: `uv` (no pip, no poetry)
- Node.js ≥ 20; npm como package manager del frontend
- Rust stable — requerido por Tauri (puede tardar minutos en compilar por primera vez)
- Sin dependencias cloud; todo local
- Sin lógica financiera (Fase 1+); sin IA (Fase 6+)
- Idioma UI: español
- Tema: dark únicamente — sin light mode en V1
- TypeScript en modo strict (noUnusedLocals, noUnusedParameters activados)
- CORS permitido solo a: `http://localhost:1420`, `tauri://localhost`, `http://tauri.localhost`
- Importes en API siempre como `string` decimal, nunca `float`
- Fechas ISO `YYYY-MM-DD`
- Sin comentarios de código a menos que el WHY sea no obvio

---

## File Map

### Raíz del monorepo
| Archivo | Acción |
|---|---|
| `.gitignore` | Crear |
| `.env.example` | Crear |
| `README.md` | Crear |
| `data/.gitkeep` | Crear (directorio de runtime, nunca commitear .db) |

### Backend
| Archivo | Acción |
|---|---|
| `backend/pyproject.toml` | Crear |
| `backend/app/__init__.py` | Crear (vacío) |
| `backend/app/main.py` | Crear |
| `backend/app/core/__init__.py` | Crear (vacío) |
| `backend/app/core/config.py` | Crear |
| `backend/app/core/database.py` | Crear |
| `backend/app/modules/{13}/__init__.py` | Crear (vacío × 13) |
| `backend/app/modules/{13}/routes.py` | Crear (router vacío × 13) |
| `backend/app/services/__init__.py` | Crear (vacío) |
| `backend/app/infrastructure/__init__.py` | Crear (vacío) |
| `backend/app/tests/__init__.py` | Crear (vacío) |
| `backend/app/tests/conftest.py` | Crear |
| `backend/app/tests/test_health.py` | Crear |

Los 13 módulos: `accounts`, `categories`, `transactions`, `imports`, `dashboard`, `investments`, `market_data`, `economic_data`, `goals`, `insights`, `ai`, `rag`, `settings`

### Frontend
| Archivo | Acción |
|---|---|
| `apps/desktop/package.json` | Crear |
| `apps/desktop/vite.config.ts` | Crear |
| `apps/desktop/tsconfig.json` | Crear |
| `apps/desktop/postcss.config.js` | Crear |
| `apps/desktop/tailwind.config.ts` | Crear |
| `apps/desktop/index.html` | Crear |
| `apps/desktop/src/index.css` | Crear |
| `apps/desktop/src/main.tsx` | Crear |
| `apps/desktop/src/App.tsx` | Crear |
| `apps/desktop/src/lib/design-tokens.ts` | Crear |
| `apps/desktop/src/lib/api/client.ts` | Crear |
| `apps/desktop/src/lib/types/index.ts` | Crear |
| `apps/desktop/src/app/layout/RootLayout.tsx` | Crear |
| `apps/desktop/src/features/{12}/...Page.tsx` | Crear (× 12) |
| `apps/desktop/src-tauri/Cargo.toml` | Crear |
| `apps/desktop/src-tauri/build.rs` | Crear |
| `apps/desktop/src-tauri/tauri.conf.json` | Crear |
| `apps/desktop/src-tauri/capabilities/default.json` | Crear |
| `apps/desktop/src-tauri/src/main.rs` | Crear |
| `apps/desktop/src-tauri/src/lib.rs` | Crear |

Las 12 features: `overview`, `spending`, `transactions`, `accounts`, `imports`, `investments`, `economy`, `markets`, `goals`, `insights`, `assistant`, `settings`

### Scripts
| Archivo | Acción |
|---|---|
| `scripts/dev.ps1` | Crear |
| `scripts/setup.ps1` | Crear |

---

## Task 1: Root monorepo scaffold

**Files:**
- Crear: `.gitignore`
- Crear: `.env.example`
- Crear: `README.md`
- Crear: `data/.gitkeep`

**Interfaces:**
- Produce: estructura raíz lista para que los demás tasks añadan sus carpetas

- [ ] **Step 1: Crear `.gitignore`**

```
# Dependencies
node_modules/
.pnp
.pnp.js

# Build outputs
dist/
dist-ssr/
*.local

# Tauri
apps/desktop/src-tauri/target/

# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Data local — nunca commitear bases de datos personales
data/*.db
data/*.sqlite
data/*.duckdb

# Entorno
.env
*.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Crear `.env.example`**

```
APP_ENV=development
DATABASE_URL=sqlite:///./data/financial.db
DUCKDB_PATH=./data/analytics.duckdb
OLLAMA_BASE_URL=http://localhost:11434
LM_STUDIO_BASE_URL=http://localhost:1234/v1
DEFAULT_AI_MODEL=qwen
```

- [ ] **Step 3: Crear `data/.gitkeep`**

Archivo vacío. El directorio `data/` se necesita en runtime pero no debe estar en git excepto por este placeholder.

- [ ] **Step 4: Crear `README.md`**

````markdown
# AI Financial OS

Centro de control financiero personal. Local-first, dark premium, IA local.

## Requisitos previos

- [Node.js 20+](https://nodejs.org/)
- [Rust stable](https://tauri.app/start/prerequisites/) — requerido por Tauri
- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestor de paquetes Python

## Setup inicial

```powershell
.\scripts\setup.ps1
```

## Desarrollo

```powershell
.\scripts\dev.ps1
```

O por separado:

```powershell
# Backend
cd backend
uv run fastapi dev app/main.py

# Desktop (en otra terminal)
cd apps/desktop
npm run tauri dev
```

> La primera compilación de Tauri puede tardar varios minutos mientras Rust descarga y compila dependencias.

## Tests

```powershell
# Backend
cd backend
uv run pytest

# TypeScript check
cd apps/desktop
npx tsc --noEmit
```

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.
````

- [ ] **Step 5: Commit**

```bash
git add .gitignore .env.example README.md data/.gitkeep
git commit -m "chore: root monorepo scaffold"
```

---

## Task 2: Backend — pyproject.toml y core

**Files:**
- Crear: `backend/pyproject.toml`
- Crear: `backend/app/__init__.py`
- Crear: `backend/app/core/__init__.py`
- Crear: `backend/app/core/config.py`
- Crear: `backend/app/core/database.py`
- Crear: `backend/app/services/__init__.py`
- Crear: `backend/app/infrastructure/__init__.py`

**Interfaces:**
- Produce: `Settings` (pydantic-settings), `engine`, `SessionLocal`, `Base`, `get_db()`, `get_duckdb()`
- Consumes: variables de `.env.example`

- [ ] **Step 1: Crear `backend/pyproject.toml`**

```toml
[project]
name = "ai-financial-os-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.0",
    "pydantic-settings>=2.6.0",
    "duckdb>=1.1.0",
    "python-multipart>=0.0.12",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "ruff>=0.8.0",
]

[tool.pytest.ini_options]
testpaths = ["app/tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Instalar dependencias**

```powershell
cd backend
uv sync
```

Resultado esperado: crea `.venv/` y resuelve todas las dependencias sin errores.

- [ ] **Step 3: Crear `backend/app/__init__.py`**

Archivo vacío.

- [ ] **Step 4: Crear `backend/app/core/__init__.py`**

Archivo vacío.

- [ ] **Step 5: Crear `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/financial.db"
    DUCKDB_PATH: str = "./data/analytics.duckdb"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    DEFAULT_AI_MODEL: str = "qwen"


settings = Settings()
```

- [ ] **Step 6: Crear `backend/app/core/database.py`**

```python
from collections.abc import Generator

import duckdb
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_duckdb() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = duckdb.connect(settings.DUCKDB_PATH)
    try:
        yield conn
    finally:
        conn.close()
```

- [ ] **Step 7: Crear `backend/app/services/__init__.py` y `backend/app/infrastructure/__init__.py`**

Ambos archivos vacíos.

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat(backend): pyproject.toml, config y database core"
```

---

## Task 3: Backend — health endpoint (TDD)

**Files:**
- Crear: `backend/app/main.py`
- Crear: `backend/app/tests/__init__.py`
- Crear: `backend/app/tests/conftest.py`
- Crear: `backend/app/tests/test_health.py`

**Interfaces:**
- Consumes: `Settings` de `app.core.config`
- Produce: `app` (instancia FastAPI), `GET /health → {"status": "ok", "version": "0.1.0"}`

- [ ] **Step 1: Crear `backend/app/tests/__init__.py`**

Archivo vacío.

- [ ] **Step 2: Crear `backend/app/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 3: Escribir el test fallido en `backend/app/tests/test_health.py`**

```python
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_health_cors_headers(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:1420"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
```

- [ ] **Step 4: Ejecutar test para confirmar que falla**

```powershell
cd backend
uv run pytest app/tests/test_health.py -v
```

Resultado esperado: `ERROR` — `ImportError: cannot import name 'app' from 'app.main'` (el archivo no existe aún).

- [ ] **Step 5: Crear `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Financial OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 6: Ejecutar test para confirmar que pasa**

```powershell
cd backend
uv run pytest app/tests/test_health.py -v
```

Resultado esperado:
```
PASSED app/tests/test_health.py::test_health_returns_ok
PASSED app/tests/test_health.py::test_health_cors_headers
2 passed in 0.XXs
```

- [ ] **Step 7: Verificar que el servidor arranca**

```powershell
cd backend
uv run fastapi dev app/main.py
```

En otra terminal:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Resultado esperado: `@{status=ok; version=0.1.0}`

Parar el servidor con Ctrl+C.

- [ ] **Step 8: Commit**

```bash
git add backend/app/main.py backend/app/tests/
git commit -m "feat(backend): health endpoint con tests"
```

---

## Task 4: Backend — 13 módulos scaffold

**Files:**
- Crear: `backend/app/modules/{module}/__init__.py` (× 13, vacíos)
- Crear: `backend/app/modules/{module}/routes.py` (× 13)
- Modificar: `backend/app/main.py` (include_router × 13)

Los 13 módulos con sus prefijos de API:

| Módulo | Prefijo |
|---|---|
| `accounts` | `/api/accounts` |
| `categories` | `/api/categories` |
| `transactions` | `/api/transactions` |
| `imports` | `/api/imports` |
| `dashboard` | `/api/dashboard` |
| `investments` | `/api/investments` |
| `market_data` | `/api/markets` |
| `economic_data` | `/api/economy` |
| `goals` | `/api/goals` |
| `insights` | `/api/insights` |
| `ai` | `/api/ai` |
| `rag` | `/api/rag` |
| `settings` | `/api/settings` |

**Interfaces:**
- Produce: 13 APIRouter vacíos registrados en `app`; `GET /api/{prefix}` devuelve 404 (no hay endpoints aún — correcto)
- Consumes: `app` de `app.main`

- [ ] **Step 1: Crear `backend/app/modules/__init__.py`**

Archivo vacío.

- [ ] **Step 2: Crear los 13 `__init__.py` de módulo**

Crear un archivo vacío en cada una de estas rutas:
```
backend/app/modules/accounts/__init__.py
backend/app/modules/categories/__init__.py
backend/app/modules/transactions/__init__.py
backend/app/modules/imports/__init__.py
backend/app/modules/dashboard/__init__.py
backend/app/modules/investments/__init__.py
backend/app/modules/market_data/__init__.py
backend/app/modules/economic_data/__init__.py
backend/app/modules/goals/__init__.py
backend/app/modules/insights/__init__.py
backend/app/modules/ai/__init__.py
backend/app/modules/rag/__init__.py
backend/app/modules/settings/__init__.py
```

- [ ] **Step 3: Crear los 13 `routes.py` de módulo**

Cada archivo sigue exactamente este patrón (sustituye `accounts` por el nombre del módulo):

`backend/app/modules/accounts/routes.py`:
```python
from fastapi import APIRouter

router = APIRouter()
```

Crear el mismo patrón para los 12 módulos restantes:
- `backend/app/modules/categories/routes.py`
- `backend/app/modules/transactions/routes.py`
- `backend/app/modules/imports/routes.py`
- `backend/app/modules/dashboard/routes.py`
- `backend/app/modules/investments/routes.py`
- `backend/app/modules/market_data/routes.py`
- `backend/app/modules/economic_data/routes.py`
- `backend/app/modules/goals/routes.py`
- `backend/app/modules/insights/routes.py`
- `backend/app/modules/ai/routes.py`
- `backend/app/modules/rag/routes.py`
- `backend/app/modules/settings/routes.py`

- [ ] **Step 4: Actualizar `backend/app/main.py` para registrar los 13 routers**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.accounts.routes import router as accounts_router
from app.modules.ai.routes import router as ai_router
from app.modules.categories.routes import router as categories_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.economic_data.routes import router as economic_data_router
from app.modules.goals.routes import router as goals_router
from app.modules.imports.routes import router as imports_router
from app.modules.insights.routes import router as insights_router
from app.modules.investments.routes import router as investments_router
from app.modules.market_data.routes import router as market_data_router
from app.modules.rag.routes import router as rag_router
from app.modules.settings.routes import router as settings_router
from app.modules.transactions.routes import router as transactions_router

app = FastAPI(title="AI Financial OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(categories_router, prefix="/api/categories", tags=["categories"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(imports_router, prefix="/api/imports", tags=["imports"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(investments_router, prefix="/api/investments", tags=["investments"])
app.include_router(market_data_router, prefix="/api/markets", tags=["market_data"])
app.include_router(economic_data_router, prefix="/api/economy", tags=["economic_data"])
app.include_router(goals_router, prefix="/api/goals", tags=["goals"])
app.include_router(insights_router, prefix="/api/insights", tags=["insights"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
```

- [ ] **Step 5: Ejecutar todos los tests para confirmar que nada se rompió**

```powershell
cd backend
uv run pytest -v
```

Resultado esperado:
```
PASSED app/tests/test_health.py::test_health_returns_ok
PASSED app/tests/test_health.py::test_health_cors_headers
2 passed in 0.XXs
```

- [ ] **Step 6: Verificar que los 13 módulos aparecen en la doc de FastAPI**

```powershell
uv run fastapi dev app/main.py
```

Abrir `http://127.0.0.1:8000/docs` en el navegador. Deben aparecer 13 secciones de tags (accounts, categories, etc.) aunque vacías. Parar el servidor con Ctrl+C.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/ backend/app/main.py
git commit -m "feat(backend): scaffold 13 módulos con routers vacíos"
```

---

## Task 5: Frontend — project config files

**Files:**
- Crear: `apps/desktop/package.json`
- Crear: `apps/desktop/vite.config.ts`
- Crear: `apps/desktop/tsconfig.json`
- Crear: `apps/desktop/postcss.config.js`
- Crear: `apps/desktop/index.html`

**Interfaces:**
- Produce: proyecto Node configurado, listo para `npm install`
- El servidor Vite escucha en el puerto 1420 (requerido por Tauri)

- [ ] **Step 1: Crear `apps/desktop/package.json`**

```json
{
  "name": "ai-financial-os-desktop",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.1.1",
    "@tauri-apps/plugin-shell": "^2.0.2",
    "lucide-react": "^0.468.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.1.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.6.3",
    "vite": "^6.0.3"
  }
}
```

- [ ] **Step 2: Instalar dependencias Node**

```powershell
cd apps/desktop
npm install
```

Resultado esperado: `node_modules/` creado sin errores.

- [ ] **Step 3: Crear `apps/desktop/vite.config.ts`**

```typescript
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? { protocol: "ws", host, port: 1421 }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

- [ ] **Step 4: Crear `apps/desktop/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "vite.config.ts", "tailwind.config.ts"]
}
```

- [ ] **Step 5: Crear `apps/desktop/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 6: Crear `apps/desktop/index.html`**

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Financial OS</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Commit**

```bash
git add apps/desktop/package.json apps/desktop/vite.config.ts apps/desktop/tsconfig.json apps/desktop/postcss.config.js apps/desktop/index.html
git commit -m "feat(desktop): project config — Vite, TypeScript, Tailwind"
```

---

## Task 6: Frontend — design tokens

**Files:**
- Crear: `apps/desktop/tailwind.config.ts`
- Crear: `apps/desktop/src/lib/design-tokens.ts`
- Crear: `apps/desktop/src/index.css`

**Interfaces:**
- Produce: clases Tailwind con tokens del sistema Revolut adaptado; variables CSS custom properties; export `colors`, `spacing`, `rounded` como constantes TypeScript
- Los tokens de `design-tokens.ts` son la fuente de verdad; `tailwind.config.ts` los refleja

- [ ] **Step 1: Crear `apps/desktop/src/lib/design-tokens.ts`**

```typescript
export const colors = {
  canvasDark: "#000000",
  surfaceDeep: "#0a0a0a",
  surfaceElevated: "#16181a",
  surfaceCard: "#1e2124",
  primary: "#494fdf",
  primaryBright: "#4f55f1",
  onPrimary: "#ffffff",
  onDark: "#ffffff",
  onDarkMute: "rgba(255,255,255,0.72)",
  hairlineDark: "rgba(255,255,255,0.12)",
  dividerSoft: "rgba(255,255,255,0.06)",
  stone: "#8d969e",
  mute: "#505a63",
  accentTeal: "#00a87e",
  accentDanger: "#e23b4a",
  accentWarning: "#ec7e00",
  accentYellow: "#b09000",
} as const;

export const spacing = {
  xs: "6px",
  sm: "8px",
  md: "14px",
  lg: "16px",
  xl: "24px",
  "2xl": "32px",
  "3xl": "48px",
} as const;

export const rounded = {
  sm: "8px",
  md: "12px",
  lg: "20px",
  xl: "28px",
  full: "9999px",
} as const;
```

- [ ] **Step 2: Crear `apps/desktop/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "canvas-dark": "#000000",
        "surface-deep": "#0a0a0a",
        "surface-elevated": "#16181a",
        "surface-card": "#1e2124",
        primary: {
          DEFAULT: "#494fdf",
          bright: "#4f55f1",
        },
        "on-dark": {
          DEFAULT: "#ffffff",
          mute: "rgba(255,255,255,0.72)",
        },
        hairline: {
          dark: "rgba(255,255,255,0.12)",
          soft: "rgba(255,255,255,0.06)",
        },
        stone: "#8d969e",
        mute: "#505a63",
        accent: {
          teal: "#00a87e",
          danger: "#e23b4a",
          warning: "#ec7e00",
          yellow: "#b09000",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "sans-serif"],
      },
      fontSize: {
        "display-lg": ["32px", { lineHeight: "1.19", fontWeight: "600", letterSpacing: "-0.32px" }],
        "heading-md": ["24px", { lineHeight: "1.33", fontWeight: "600" }],
        "heading-sm": ["20px", { lineHeight: "1.4", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "1.5", fontWeight: "400", letterSpacing: "0.24px" }],
        "body-sm": ["14px", { lineHeight: "1.43", fontWeight: "400" }],
        "button-md": ["16px", { lineHeight: "1.5", fontWeight: "600", letterSpacing: "0.24px" }],
        caption: ["13px", { lineHeight: "1.4", fontWeight: "400" }],
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "20px",
        xl: "28px",
      },
      spacing: {
        xs: "6px",
        sm: "8px",
        md: "14px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
        "3xl": "48px",
      },
    },
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 3: Crear `apps/desktop/src/index.css`**

```css
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap");
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --canvas-dark: #000000;
  --surface-deep: #0a0a0a;
  --surface-elevated: #16181a;
  --surface-card: #1e2124;
  --primary: #494fdf;
  --primary-bright: #4f55f1;
  --on-dark: #ffffff;
  --on-dark-mute: rgba(255, 255, 255, 0.72);
  --hairline-dark: rgba(255, 255, 255, 0.12);
  --divider-soft: rgba(255, 255, 255, 0.06);
  --stone: #8d969e;
  --mute: #505a63;
  --accent-teal: #00a87e;
  --accent-danger: #e23b4a;
  --accent-warning: #ec7e00;
  --accent-yellow: #b09000;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body,
#root {
  height: 100%;
  margin: 0;
  padding: 0;
  background-color: var(--canvas-dark);
  color: var(--on-dark);
  font-family: "Inter", ui-sans-serif, sans-serif;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--surface-deep);
}

::-webkit-scrollbar-thumb {
  background: var(--hairline-dark);
  border-radius: 9999px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--mute);
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/tailwind.config.ts apps/desktop/src/lib/design-tokens.ts apps/desktop/src/index.css
git commit -m "feat(desktop): design tokens sistema Revolut adaptado"
```

---

## Task 7: Frontend — app shell

**Files:**
- Crear: `apps/desktop/src/main.tsx`
- Crear: `apps/desktop/src/App.tsx`
- Crear: `apps/desktop/src/app/layout/RootLayout.tsx`
- Crear: `apps/desktop/src/app/routes/.gitkeep`
- Crear: `apps/desktop/src/app/providers/.gitkeep`
- Crear: `apps/desktop/src/components/ui/.gitkeep`
- Crear: `apps/desktop/src/components/layout/.gitkeep`
- Crear: `apps/desktop/src/components/charts/.gitkeep`
- Crear: `apps/desktop/src/components/financial/.gitkeep`
- Crear: `apps/desktop/src/components/import/.gitkeep`
- Crear: `apps/desktop/src/lib/formatters/.gitkeep`
- Crear: `apps/desktop/src/lib/hooks/.gitkeep`

**Interfaces:**
- Consumes: feature pages de Task 8 (se añaden al App.tsx después)
- Produce: app React con React Router, sidebar funcional de 12 rutas, layout dark

> Nota: `App.tsx` en este task importa las feature pages que se crean en Task 8. Para que TypeScript no falle, crear Task 8 justo después de este task antes de hacer `tsc --noEmit`.

- [ ] **Step 1: Crear los directorios estructurales vacíos**

Crear archivos `.gitkeep` vacíos en:
```
apps/desktop/src/app/routes/.gitkeep
apps/desktop/src/app/providers/.gitkeep
apps/desktop/src/components/ui/.gitkeep
apps/desktop/src/components/layout/.gitkeep
apps/desktop/src/components/charts/.gitkeep
apps/desktop/src/components/financial/.gitkeep
apps/desktop/src/components/import/.gitkeep
apps/desktop/src/lib/formatters/.gitkeep
apps/desktop/src/lib/hooks/.gitkeep
```

- [ ] **Step 2: Crear `apps/desktop/src/main.tsx`**

```typescript
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 3: Crear `apps/desktop/src/app/layout/RootLayout.tsx`**

```typescript
import {
  Activity,
  ArrowLeftRight,
  BarChart2,
  Bot,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Settings,
  Target,
  TrendingDown,
  Upload,
  Wallet,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Resumen", end: true },
  { to: "/spending", icon: TrendingDown, label: "Gastos" },
  { to: "/transactions", icon: ArrowLeftRight, label: "Movimientos" },
  { to: "/accounts", icon: Wallet, label: "Cuentas" },
  { to: "/imports", icon: Upload, label: "Importar" },
  { to: "/investments", icon: BarChart2, label: "Inversiones" },
  { to: "/economy", icon: Globe, label: "Economía" },
  { to: "/markets", icon: Activity, label: "Mercados" },
  { to: "/goals", icon: Target, label: "Objetivos" },
  { to: "/insights", icon: Lightbulb, label: "Insights" },
  { to: "/assistant", icon: Bot, label: "Asistente" },
  { to: "/settings", icon: Settings, label: "Ajustes" },
] as const;

export default function RootLayout() {
  return (
    <div className="flex h-full">
      <aside className="w-60 flex-shrink-0 bg-surface-deep border-r border-hairline-dark flex flex-col">
        <div className="h-14 flex items-center px-6 border-b border-hairline-dark">
          <span className="text-heading-sm text-on-dark font-semibold tracking-tight">
            Financial OS
          </span>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 px-3 py-2 rounded-md text-body-sm transition-colors duration-150",
                  isActive
                    ? "bg-surface-elevated text-on-dark"
                    : "text-stone hover:text-on-dark hover:bg-surface-elevated/50",
                ].join(" ")
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto bg-canvas-dark">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Crear `apps/desktop/src/App.tsx`** (escribir después de Task 8)

> No crear este archivo todavía — esperar a que existan las páginas de features (Task 8). Se muestra aquí el contenido final:

```typescript
import { Route, Routes } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import AccountsPage from "@/features/accounts/AccountsPage";
import AssistantPage from "@/features/assistant/AssistantPage";
import EconomyPage from "@/features/economy/EconomyPage";
import GoalsPage from "@/features/goals/GoalsPage";
import ImportsPage from "@/features/imports/ImportsPage";
import InsightsPage from "@/features/insights/InsightsPage";
import InvestmentsPage from "@/features/investments/InvestmentsPage";
import MarketsPage from "@/features/markets/MarketsPage";
import OverviewPage from "@/features/overview/OverviewPage";
import SettingsPage from "@/features/settings/SettingsPage";
import SpendingPage from "@/features/spending/SpendingPage";
import TransactionsPage from "@/features/transactions/TransactionsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="spending" element={<SpendingPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="imports" element={<ImportsPage />} />
        <Route path="investments" element={<InvestmentsPage />} />
        <Route path="economy" element={<EconomyPage />} />
        <Route path="markets" element={<MarketsPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 5: Commit (sin App.tsx todavía)**

```bash
git add apps/desktop/src/main.tsx apps/desktop/src/app/ apps/desktop/src/components/ apps/desktop/src/lib/formatters/ apps/desktop/src/lib/hooks/
git commit -m "feat(desktop): app shell — main.tsx, RootLayout con sidebar"
```

---

## Task 8: Frontend — feature placeholder pages

**Files:**
- Crear: `apps/desktop/src/features/overview/OverviewPage.tsx`
- Crear: `apps/desktop/src/features/spending/SpendingPage.tsx`
- Crear: `apps/desktop/src/features/transactions/TransactionsPage.tsx`
- Crear: `apps/desktop/src/features/accounts/AccountsPage.tsx`
- Crear: `apps/desktop/src/features/imports/ImportsPage.tsx`
- Crear: `apps/desktop/src/features/investments/InvestmentsPage.tsx`
- Crear: `apps/desktop/src/features/economy/EconomyPage.tsx`
- Crear: `apps/desktop/src/features/markets/MarketsPage.tsx`
- Crear: `apps/desktop/src/features/goals/GoalsPage.tsx`
- Crear: `apps/desktop/src/features/insights/InsightsPage.tsx`
- Crear: `apps/desktop/src/features/assistant/AssistantPage.tsx`
- Crear: `apps/desktop/src/features/settings/SettingsPage.tsx`
- Crear: `apps/desktop/src/App.tsx`

**Interfaces:**
- Produce: 12 componentes React exportados por defecto; cada uno renderiza un heading con el nombre de la sección y un subtítulo en español

- [ ] **Step 1: Crear las 12 páginas placeholder**

Cada página sigue exactamente este patrón. Crear una por una con el nombre y label correspondiente:

`apps/desktop/src/features/overview/OverviewPage.tsx`:
```typescript
export default function OverviewPage() {
  return (
    <div className="p-8">
      <h1 className="text-display-lg text-on-dark">Resumen</h1>
      <p className="text-body-md text-stone mt-2">Dashboard financiero — Fase 1</p>
    </div>
  );
}
```

Crear el mismo patrón para las 11 páginas restantes con estos valores:

| Archivo | Función | H1 | Subtítulo |
|---|---|---|---|
| `spending/SpendingPage.tsx` | `SpendingPage` | `Gastos` | `Análisis de gastos — Fase 1` |
| `transactions/TransactionsPage.tsx` | `TransactionsPage` | `Movimientos` | `Historial de transacciones — Fase 1` |
| `accounts/AccountsPage.tsx` | `AccountsPage` | `Cuentas` | `Gestión de cuentas — Fase 1` |
| `imports/ImportsPage.tsx` | `ImportsPage` | `Importar` | `Centro de importación CSV — Fase 2` |
| `investments/InvestmentsPage.tsx` | `InvestmentsPage` | `Inversiones` | `Cartera de inversiones — Fase 3` |
| `economy/EconomyPage.tsx` | `EconomyPage` | `Economía` | `Indicadores macroeconómicos — Fase 5` |
| `markets/MarketsPage.tsx` | `MarketsPage` | `Mercados` | `Datos de mercado — Fase 4` |
| `goals/GoalsPage.tsx` | `GoalsPage` | `Objetivos` | `Objetivos financieros — Fase 8` |
| `insights/InsightsPage.tsx` | `InsightsPage` | `Insights` | `Motor de insights — Fase 7` |
| `assistant/AssistantPage.tsx` | `AssistantPage` | `Asistente` | `Asistente IA local — Fase 6` |
| `settings/SettingsPage.tsx` | `SettingsPage` | `Ajustes` | `Configuración de la aplicación — Fase 1` |

- [ ] **Step 2: Crear `apps/desktop/src/App.tsx`**

Usar exactamente el contenido del Step 4 de Task 7 (repetido aquí para evitar referencias cruzadas):

```typescript
import { Route, Routes } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import AccountsPage from "@/features/accounts/AccountsPage";
import AssistantPage from "@/features/assistant/AssistantPage";
import EconomyPage from "@/features/economy/EconomyPage";
import GoalsPage from "@/features/goals/GoalsPage";
import ImportsPage from "@/features/imports/ImportsPage";
import InsightsPage from "@/features/insights/InsightsPage";
import InvestmentsPage from "@/features/investments/InvestmentsPage";
import MarketsPage from "@/features/markets/MarketsPage";
import OverviewPage from "@/features/overview/OverviewPage";
import SettingsPage from "@/features/settings/SettingsPage";
import SpendingPage from "@/features/spending/SpendingPage";
import TransactionsPage from "@/features/transactions/TransactionsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="spending" element={<SpendingPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="imports" element={<ImportsPage />} />
        <Route path="investments" element={<InvestmentsPage />} />
        <Route path="economy" element={<EconomyPage />} />
        <Route path="markets" element={<MarketsPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 3: Verificar TypeScript sin errores**

```powershell
cd apps/desktop
npx tsc --noEmit
```

Resultado esperado: sin output (0 errores).

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/features/ apps/desktop/src/App.tsx
git commit -m "feat(desktop): 12 feature pages placeholder + App router"
```

---

## Task 9: Frontend — API client y tipos

**Files:**
- Crear: `apps/desktop/src/lib/api/client.ts`
- Crear: `apps/desktop/src/lib/types/index.ts`

**Interfaces:**
- Produce: `api.get<T>()`, `api.post<T>()`, `api.patch<T>()`, `api.delete<T>()`; clase `ApiError`; tipos `Account`, `Category`, `Transaction`, `HealthResponse`, `DashboardOverview`, `ApiErrorResponse`

- [ ] **Step 1: Crear `apps/desktop/src/lib/api/client.ts`**

```typescript
const BASE_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ error: { code: "UNKNOWN", message: response.statusText } }));
    throw new ApiError(
      response.status,
      body.error?.code ?? "UNKNOWN",
      body.error?.message ?? response.statusText,
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
```

- [ ] **Step 2: Crear `apps/desktop/src/lib/types/index.ts`**

```typescript
export type AccountType =
  | "cash"
  | "bank"
  | "broker"
  | "savings"
  | "investment"
  | "mortgage"
  | "other";

export type TransactionType = "income" | "expense" | "transfer" | "investment";

export type CategoryType = "income" | "expense" | "transfer" | "investment";

export type TransactionSource = "manual" | "csv" | "pdf" | "system";

export type ImportStatus =
  | "pending"
  | "validated"
  | "imported"
  | "failed"
  | "rolled_back";

export interface Account {
  id: string;
  name: string;
  type: AccountType;
  institution: string | null;
  currency: string;
  current_balance: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  type: CategoryType;
  icon: string | null;
  color: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  category_id: string | null;
  date: string;
  description: string;
  amount: string;
  currency: string;
  converted_amount: string | null;
  converted_currency: string | null;
  type: TransactionType;
  source: TransactionSource;
  source_name: string | null;
  external_id: string | null;
  import_batch_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface DashboardOverview {
  net_worth: string;
  liquidity: string;
  investments: string;
  monthly_income: string;
  monthly_expense: string;
  monthly_savings: string;
  savings_rate: number;
  currency: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}
```

- [ ] **Step 3: Verificar TypeScript sin errores**

```powershell
cd apps/desktop
npx tsc --noEmit
```

Resultado esperado: sin output.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/lib/api/client.ts apps/desktop/src/lib/types/index.ts
git commit -m "feat(desktop): API client y tipos base del modelo de datos"
```

---

## Task 10: Tauri config

**Files:**
- Crear: `apps/desktop/src-tauri/Cargo.toml`
- Crear: `apps/desktop/src-tauri/build.rs`
- Crear: `apps/desktop/src-tauri/tauri.conf.json`
- Crear: `apps/desktop/src-tauri/capabilities/default.json`
- Crear: `apps/desktop/src-tauri/src/main.rs`
- Crear: `apps/desktop/src-tauri/src/lib.rs`

**Interfaces:**
- Produce: app Tauri v2 que sirve el frontend Vite desde el puerto 1420

> Prerrequisito: Rust stable instalado (`rustup show` debe mostrar una toolchain activa).

- [ ] **Step 1: Verificar Rust**

```powershell
rustup show
```

Resultado esperado: línea con `stable-x86_64-pc-windows-msvc (default)`. Si no aparece, instalar desde https://tauri.app/start/prerequisites/ antes de continuar.

- [ ] **Step 2: Crear `apps/desktop/src-tauri/Cargo.toml`**

```toml
[package]
name = "ai-financial-os"
version = "0.1.0"
edition = "2021"

[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

- [ ] **Step 3: Crear `apps/desktop/src-tauri/build.rs`**

```rust
fn main() {
    tauri_build::build()
}
```

- [ ] **Step 4: Crear `apps/desktop/src-tauri/src/lib.rs`**

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 5: Crear `apps/desktop/src-tauri/src/main.rs`**

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    app_lib::run();
}
```

- [ ] **Step 6: Crear `apps/desktop/src-tauri/tauri.conf.json`**

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "AI Financial OS",
  "version": "0.1.0",
  "identifier": "com.aifinancialos.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "AI Financial OS",
        "width": 1440,
        "height": 900,
        "minWidth": 1024,
        "minHeight": 768
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": []
  }
}
```

- [ ] **Step 7: Crear `apps/desktop/src-tauri/capabilities/default.json`**

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open"
  ]
}
```

- [ ] **Step 8: Commit**

```bash
git add apps/desktop/src-tauri/
git commit -m "feat(tauri): configuración Tauri v2 para Windows desktop"
```

---

## Task 11: Scripts de desarrollo

**Files:**
- Crear: `scripts/dev.ps1`
- Crear: `scripts/setup.ps1`

**Interfaces:**
- `dev.ps1`: arranca backend (puerto 8000) y desktop (Tauri dev) como procesos independientes
- `setup.ps1`: instala dependencias Python y Node, crea `data/` y `.env` si no existen

- [ ] **Step 1: Crear `scripts/setup.ps1`**

```powershell
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

Write-Host "AI Financial OS — Setup" -ForegroundColor Cyan

# Directorio data
if (-not (Test-Path "$root\data")) {
    New-Item -ItemType Directory -Path "$root\data" | Out-Null
    Write-Host "  Creado: data/" -ForegroundColor Gray
}

# .env
if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
    Write-Host "  Creado: .env desde .env.example" -ForegroundColor Gray
}

# Python
Write-Host "Instalando dependencias Python..." -ForegroundColor Yellow
Set-Location "$root\backend"
uv sync
Write-Host "  Backend OK" -ForegroundColor Green

# Node
Write-Host "Instalando dependencias Node..." -ForegroundColor Yellow
Set-Location "$root\apps\desktop"
npm install
Write-Host "  Desktop OK" -ForegroundColor Green

Write-Host "Setup completado. Ejecuta .\scripts\dev.ps1 para iniciar." -ForegroundColor Cyan
```

- [ ] **Step 2: Crear `scripts/dev.ps1`**

```powershell
$root = Split-Path $PSScriptRoot -Parent

Write-Host "Iniciando AI Financial OS..." -ForegroundColor Cyan

$backend = Start-Process -FilePath "uv" `
    -ArgumentList "run", "fastapi", "dev", "app/main.py", "--port", "8000" `
    -WorkingDirectory "$root\backend" `
    -PassThru `
    -NoNewWindow

Write-Host "  Backend iniciado en http://127.0.0.1:8000 (PID $($backend.Id))" -ForegroundColor Green

Start-Sleep -Seconds 2

$frontend = Start-Process -FilePath "npm" `
    -ArgumentList "run", "tauri", "dev" `
    -WorkingDirectory "$root\apps\desktop" `
    -PassThru `
    -NoNewWindow

Write-Host "  Desktop iniciando... (primera vez puede tardar varios minutos)" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener." -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Wait-Process -Id $frontend.Id -ErrorAction SilentlyContinue
} finally {
    if (-not $backend.HasExited) { $backend.Kill() }
    if (-not $frontend.HasExited) { $frontend.Kill() }
    Write-Host "Procesos detenidos." -ForegroundColor Gray
}
```

- [ ] **Step 3: Commit**

```bash
git add scripts/
git commit -m "feat: scripts PowerShell dev y setup"
```

---

## Task 12: Verificación final

**Files:** Ninguno (solo verificación)

**Interfaces:**
- Consume: todos los tasks anteriores
- Produce: confirmación de que backend arranca, tests pasan y TypeScript compila

- [ ] **Step 1: Ejecutar tests del backend**

```powershell
cd backend
uv run pytest -v
```

Resultado esperado:
```
PASSED app/tests/test_health.py::test_health_returns_ok
PASSED app/tests/test_health.py::test_health_cors_headers
2 passed
```

- [ ] **Step 2: Verificar TypeScript del frontend**

```powershell
cd apps/desktop
npx tsc --noEmit
```

Resultado esperado: sin output (0 errores).

- [ ] **Step 3: Verificar que el backend arranca y responde**

```powershell
cd backend
uv run fastapi dev app/main.py &
Start-Sleep 3
Invoke-RestMethod http://127.0.0.1:8000/health
```

Resultado esperado: `@{status=ok; version=0.1.0}`

- [ ] **Step 4: Verificar que Vite (sin Tauri) arranca**

```powershell
cd apps/desktop
npm run dev
```

Abrir `http://localhost:1420` en el navegador. Debe mostrar el sidebar con 12 ítems de navegación. Parar con Ctrl+C.

- [ ] **Step 5: Commit final**

```bash
git add -A
git commit -m "chore: verificación Fase 0 completada — backend + desktop funcionando"
```

---

## Self-Review

**Cobertura del spec:**

| Requisito spec | Task que lo implementa |
|---|---|
| Monorepo `apps/desktop` + `backend` | Task 1, 2, 5 |
| `GET /health` con `{"status":"ok","version":"0.1.0"}` | Task 3 |
| CORS solo a localhost/tauri | Task 3 |
| 13 módulos backend con routers vacíos | Task 4 |
| `pyproject.toml` con uv | Task 2 |
| Tauri v2 + React 18 + TypeScript | Task 5, 10 |
| Tailwind + design tokens Revolut adaptado | Task 6 |
| Sidebar + 12 rutas frontend | Task 7, 8 |
| `lib/api/client.ts` → 127.0.0.1:8000 | Task 9 |
| `lib/types/index.ts` alineado con modelo de datos | Task 9 |
| `.env.example` con variables del doc 12 | Task 1 |
| Scripts `dev.ps1` y `setup.ps1` | Task 11 |
| `data/` para SQLite/DuckDB | Task 1, 2 |
| TypeScript strict | Task 5 |
| Tema dark | Task 6 (index.css) |
| Sin lógica financiera | Cumplido — solo placeholders |
| Sin IA | Cumplido — AssistantPage es placeholder |
| Tests backend | Task 3 |

**Sin placeholders ni TBDs.** ✓  
**Consistencia de tipos:** `Account`, `Category`, `Transaction` definidos en Task 9 y referenciados en `App.tsx` solo como imports de páginas. No hay referencias cruzadas de tipos entre tasks. ✓  
**Sin referencias a tasks anteriores como "similar a Task N"** ✓
