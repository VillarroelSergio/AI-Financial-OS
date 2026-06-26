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

Para iniciar únicamente el backend en Windows:

```powershell
.\scripts\backend.ps1
```

El script usa `uv` cuando está disponible y, en caso contrario, reutiliza
`backend\.venv\Scripts\python.exe`.

Para iniciar backend y aplicación Tauri con un único comando desde la raíz:

```powershell
npm run dev
```

```powershell
.\scripts\dev.ps1
```

O por separado:

```powershell
# Backend
cd backend
uv run uvicorn app.main:app --reload

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

## Market Intelligence CLI

Comandos disponibles desde `market-data-poc/run_poc.py`:

```powershell
cd market-data-poc
uv run python run_poc.py market:intelligence:init-db       # crea tablas mi_* en DuckDB
uv run python run_poc.py market:intelligence:catalog       # lista indicadores del catálogo
uv run python run_poc.py market:intelligence:catalog:validate  # valida YAMLs
uv run python run_poc.py market:intelligence:update        # ingesta todos los indicadores
uv run python run_poc.py market:intelligence:quality       # muestra scores de calidad
uv run python run_poc.py market:intelligence:snapshot      # snapshot DuckDB → JSON
uv run python run_poc.py market:intelligence:datasheet     # genera AI datasheet
```

API endpoints bajo `/api/market-intelligence/`:

| Endpoint | Descripción |
|---|---|
| `GET /macro-snapshot` | Indicadores macro por región |
| `GET /market-quotes` | Cotizaciones de índices/acciones |
| `GET /forex-rates` | Tipos de cambio |
| `GET /bond-yields` | Rendimientos de bonos |
| `GET /news` | Noticias financieras |
| `GET /ai-datasheet` | Datasheet compacto para IA local |

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.


Para usar la herramienta de capturas desde apps/desktop/:


npm run ux:snapshots        # captura 8 rutas en headless
npm run ux:snapshots:headed # ídem con navegador visible
npm run ux:report           # muestra resumen de la última capt
