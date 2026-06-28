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

## Fase 6.4 - Data Integrity & Core UX Repair

La app evita mostrar datos internos o enganosos: los UUID no se usan como nombres visibles, los datos demo/mock se marcan, los holdings pueden editarse con precio manual y los porcentajes de gastos se calculan contra el gasto total del periodo.

Pantallas reforzadas:

- Inversiones: CRUD basico de activos, distribucion por activo/broker/tipo/divisa/sector y exclusion visual de demo en repartos reales.
- Mercados: secciones claras para indices, cripto, materias primas, divisas y bonos con provider, calidad y estados parciales.
- Cuentas: resumen superior, cards con peso sobre liquidez, edicion y eliminacion.
- Gastos: selector de periodo, metricas superiores, donut y barras por categoria.
- Resumen: cards ejecutivas y secciones de salud financiera, flujo, patrimonio y proximas acciones.

## Fase 6.4.1 - Expense Drilldown & Investment Price Refresh UX Fix

- Gastos: las categorias se pueden abrir desde donut, lista y control visual para ver movimientos, total, peso, numero de transacciones y media.
- API: `GET /api/dashboard/spending/category-detail` devuelve el detalle por categoria para mes o ano.
- Inversiones: `Actualizar precios` intenta proveedores automaticos y devuelve actualizados, manuales, omitidos y errores.
- Precio manual se usa solo cuando no hay proveedor automatico; NAV queda reservado a fondos.
- Cuentas remuneradas, efectivo y savings/cash se omiten del refresco manual porque su valor viene del balance.

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.


Para usar la herramienta de capturas desde apps/desktop/:


npm run ux:snapshots        # captura 8 rutas en headless
npm run ux:snapshots:headed # ídem con navegador visible
npm run ux:report           # muestra resumen de la última capt
