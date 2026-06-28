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

## Market Intelligence

La capa vigente de mercados y macro vive en `backend/app/modules/market_intelligence`.
El antiguo `market-data-poc/` queda como banco de pruebas legado y no debe usarse como
fuente principal de documentacion ni de comandos operativos.

API endpoints bajo `/api/market-intelligence/`:

| Endpoint | Descripción |
|---|---|
| `GET /snapshot/macro` | Indicadores macro por región |
| `GET /snapshot/market` | Cotizaciones de índices, cripto y commodities |
| `GET /snapshot/forex` | Tipos de cambio |
| `GET /snapshot/bonds` | Rendimientos de bonos |
| `GET /snapshot/news` | Noticias financieras |
| `GET /personal-impact` | Comparativas entre contexto macro/mercado y datos personales |
| `GET /ingest-status` | Estado de la ingesta automática de arranque |
| `GET /ai-datasheet` | Datasheet compacto para IA local |

## Local AI Assistant

La Fase 6 esta implementada y la Fase 6.1 estabiliza el asistente antes de Fase 7.
La IA local usa Ollama o LM Studio, no consulta Internet y no ejecuta SQL libre.

Las tools del asistente consumen solamente:

- `market_intelligence` para macro, mercados, forex, bonos y calidad de proveedores.
- `financial_knowledge` para regimen de mercado, senales, impacto personal y AI datasheet.
- Servicios controlados de finanzas personales para patrimonio, ahorro, gastos y objetivos.

Endpoints principales:

| Endpoint | Descripcion |
|---|---|
| `GET /api/ai/status` | Estado de IA, provider por defecto y healthchecks |
| `GET /api/ai/providers` | Providers locales disponibles |
| `GET /api/ai/tools` | Tools registradas |
| `POST /api/ai/chat` | Chat con tool-calling |
| `GET /api/ai/conversations` | Conversaciones |

Para probar Ollama:

```powershell
ollama serve
ollama pull qwen3-coder:30b
```

Para probar LM Studio, inicia el servidor OpenAI-compatible y configura `LMSTUDIO_BASE_URL`.
Las respuestas del chat conservan `tool_calls`, `sources` y `quality_score`; el frontend puede abrir "Ver datos usados".

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.


Para usar la herramienta de capturas desde apps/desktop/:


npm run ux:snapshots        # captura 8 rutas en headless
npm run ux:snapshots:headed # ídem con navegador visible
npm run ux:report           # muestra resumen de la última capt
