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

La capa de mercados y macro vive en `backend/app/modules/market_intelligence`.

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

## Document Intelligence / RAG

La Fase 9 permite indexar y consultar documentacion financiera local sin subirla a la nube.

Endpoints principales:

| Endpoint | Descripcion |
|---|---|
| `GET /api/rag/documents` | Lista documentos locales indexados |
| `POST /api/rag/documents` | Crea documento desde texto |
| `POST /api/rag/documents/upload` | Sube documento local `txt`, `md`, `csv` o `json` |
| `POST /api/rag/query` | Consulta documentos y devuelve fuentes |

## Security & Backups

La Fase 10 anade backups locales, validacion de integridad y estado de seguridad antes del empaquetado.

Endpoints principales:

| Endpoint | Descripcion |
|---|---|
| `GET /api/security/status` | Estado local de hardening |
| `GET /api/security/backups` | Lista backups locales |
| `POST /api/security/backups` | Crea backup SQLite local |
| `GET /api/security/integrity` | Ejecuta comprobacion de integridad |


## Instalación (usuario final)

Si recibes el instalador ya compilado (`.msi` en Windows):

1. Ejecuta el instalador y sigue el asistente.
2. Antes de arrancar la app por primera vez crea tu archivo de configuración:
   ```powershell
   # Desde la raíz del repositorio (solo para builds from source)
   copy backend\.env.example backend\.env
   ```
   Si usas el instalador empaquetado, la app crea `backend/.env` automáticamente la primera vez que arranca y usa valores por defecto (IA local, sin claves externas).
3. Los datos de la aplicación se almacenan localmente en `backend/data/`:
   - `financial.db` — base de datos SQLite principal
   - `analytics.duckdb` — caché analítica
4. **Troubleshooting**: si la app arranca pero el backend no responde, comprueba que el puerto 8000 esté libre. Puedes arrancar el backend manualmente con `.\scripts\backend.ps1` y revisar la consola.

## Configuración de entorno

Copia el archivo de ejemplo y edita las variables que necesites:

```powershell
copy backend\.env.example backend\.env
```

El archivo `backend/.env.example` documenta todas las opciones. Las más relevantes:

| Variable | Descripción | Requerida |
|---|---|---|
| `DATABASE_URL` | Ruta de la base de datos SQLite | Sí (default OK) |
| `OLLAMA_BASE_URL` | URL de tu instancia de Ollama | Solo si usas IA local |
| `LMSTUDIO_BASE_URL` | URL de tu instancia de LM Studio | Solo si usas LM Studio |
| `ALPHA_VANTAGE_API_KEY` | Clave API para datos de mercado | Opcional (free tier) |
| `FINNHUB_API_KEY` | Clave API Finnhub | Opcional (free tier) |
| `FRED_API_KEY` | Clave API FRED (datos macro EE.UU.) | Opcional (free tier) |

Para IA local, el proveedor por defecto es Ollama. Ajusta `AI_DEFAULT_PROVIDER` y `AI_DEFAULT_MODEL` según tu setup.

## Build de distribución

Requisitos previos adicionales para generar el instalador:

- **Rust stable** (se instala con `rustup`)
- **WiX Toolset 3.x** (solo Windows, para generar `.msi`) — [descargar aquí](https://wixtoolset.org/)

```powershell
# Instala dependencias y compila frontend + backend Rust
cd apps/desktop
npm run tauri build
```

El instalador resultante aparece en `apps/desktop/src-tauri/target/release/bundle/`:
- `msi/` — instalador Windows `.msi`
- `nsis/` — instalador NSIS alternativo

La build de release deshabilita las DevTools de Tauri y aplica la CSP de producción definida en `tauri.conf.json`.

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.


## Licencia

MIT — ver [LICENSE](LICENSE)

---

## UX Snapshots (Capturas automatizadas)

La herramienta de snapshots genera capturas de pantalla de todas las funcionalidades principales. Se ejecuta desde `apps/desktop/`:

### Modo Mock (datos ficticios)
Genera capturas sin tocar el backend. Los datos son ficticios (útil para layouts y regresiones visuales):

```powershell
cd apps/desktop
npm run ux:snapshots        # headless, salida en ux-snapshots/latest/
npm run ux:snapshots:headed # con navegador visible
```

### Modo Real (datos del usuario)
Captura la app con tus **datos reales** de `backend/data/financial.db`. Requiere que el backend esté corriendo en puerto 8010:

```powershell
# Terminal 1: inicia el backend
cd backend
python run_server.py

# Terminal 2: captura con datos reales
cd apps/desktop
npm run ux:snapshots:real        # headless, salida en ux-snapshots/real/
npm run ux:snapshots:real:headed # con navegador visible
```

**Diferencias:**
- Mock: Vite + datos ficticios, puerto 1422, salida `ux-snapshots/latest/`
- Real: Vite + backend real en 8010, puerto 1420, salida `ux-snapshots/real/`

Ambos modos capturan 21 rutas principales (dashboard, inversiones, mercados, transacciones, etc.) y generan `metadata.json` + `UX_REVIEW_CONTEXT.md`.

```powershell
npm run ux:report           # muestra resumen de la última captura
```
