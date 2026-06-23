# Design: AI Financial OS — Fase 0 Foundation Structure

**Date:** 2026-06-22  
**Phase:** 0 — Foundation  
**Approach chosen:** Opción B — Fase 0 funcional completa

---

## Objetivo

Crear la estructura base del monorepo AI-Financial-OS con código mínimo funcional para que la aplicación arranque: backend FastAPI respondiendo `/health` y frontend Tauri+React con navegación base. No se implementa lógica financiera (Fase 1+).

---

## Estructura de directorios

```
AI-Financial-OS/
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── app/
│       │   │   ├── routes/
│       │   │   ├── layout/
│       │   │   └── providers/
│       │   ├── features/
│       │   │   ├── overview/
│       │   │   ├── spending/
│       │   │   ├── transactions/
│       │   │   ├── accounts/
│       │   │   ├── imports/
│       │   │   ├── investments/
│       │   │   ├── economy/
│       │   │   ├── markets/
│       │   │   ├── goals/
│       │   │   ├── insights/
│       │   │   ├── assistant/
│       │   │   └── settings/
│       │   ├── components/
│       │   │   ├── ui/
│       │   │   ├── layout/
│       │   │   ├── charts/
│       │   │   ├── financial/
│       │   │   └── import/
│       │   └── lib/
│       │       ├── api/
│       │       ├── formatters/
│       │       ├── hooks/
│       │       └── types/
│       ├── src-tauri/
│       ├── index.html
│       ├── package.json
│       ├── tsconfig.json
│       └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── modules/
│   │   │   ├── accounts/
│   │   │   ├── categories/
│   │   │   ├── transactions/
│   │   │   ├── imports/
│   │   │   ├── dashboard/
│   │   │   ├── investments/
│   │   │   ├── market_data/
│   │   │   ├── economic_data/
│   │   │   ├── goals/
│   │   │   ├── insights/
│   │   │   ├── ai/
│   │   │   ├── rag/
│   │   │   └── settings/
│   │   ├── services/
│   │   ├── infrastructure/
│   │   └── tests/
│   └── pyproject.toml
│
├── docs/
├── scripts/
│   ├── dev.ps1
│   └── setup.ps1
├── data/
├── .env.example
├── .gitignore
└── README.md
```

---

## Archivos con código real (mínimo funcional)

### Backend

| Archivo | Contenido |
|---|---|
| `backend/app/main.py` | FastAPI app, CORS para localhost, `GET /health`, include de routers |
| `backend/app/core/config.py` | `Settings` con Pydantic-settings desde `.env` |
| `backend/app/core/database.py` | SQLAlchemy engine SQLite + DuckDB connection factory |
| `backend/pyproject.toml` | fastapi, uvicorn, sqlalchemy, pydantic-settings, duckdb, ruff, pytest |
| `backend/app/modules/*/routes.py` | Router vacío registrado en main (13 módulos) |
| `backend/app/modules/*/__init__.py` | Vacío |

### Frontend

| Archivo | Contenido |
|---|---|
| `apps/desktop/package.json` | Tauri v2, React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Router |
| `apps/desktop/vite.config.ts` | Configuración Vite para Tauri |
| `apps/desktop/tsconfig.json` | TypeScript strict mode, path aliases |
| `apps/desktop/index.html` | Entry HTML mínimo |
| `apps/desktop/src/main.tsx` | ReactDOM.createRoot entry point |
| `apps/desktop/src/App.tsx` | React Router con rutas placeholder para cada feature |
| `apps/desktop/src/app/layout/RootLayout.tsx` | Sidebar izquierdo + área de contenido, dark theme |
| `apps/desktop/src/lib/api/client.ts` | fetch wrapper apuntando a `http://127.0.0.1:8000` |
| `apps/desktop/src/lib/types/index.ts` | Tipos base TypeScript (Account, Transaction, Category, etc.) |
| `apps/desktop/src-tauri/tauri.conf.json` | Configuración Tauri mínima |
| `apps/desktop/src-tauri/Cargo.toml` | Dependencias Rust Tauri |
| `apps/desktop/src-tauri/src/main.rs` | Entry point Tauri |

### Scripts y configuración raíz

| Archivo | Contenido |
|---|---|
| `.env.example` | Variables del doc 12 (DATABASE_URL, OLLAMA_BASE_URL, etc.) |
| `.gitignore` | node_modules, __pycache__, .venv, data/*.db, data/*.duckdb |
| `scripts/dev.ps1` | Lanza backend con `uv run` + desktop con `npm run tauri dev` en paralelo |
| `scripts/setup.ps1` | Instala dependencias Python (uv) y Node (npm) |
| `README.md` | Instrucciones de setup y comandos principales |

---

## Archivos solo con estructura vacía (Fase 1+)

- Todos los archivos dentro de `features/*/`
- Componentes de `components/charts/`, `components/financial/`, `components/import/`
- Servicios de `backend/app/services/` e `infrastructure/`
- Modelos y schemas de cada módulo backend

---

## Sistema de diseño — Base Revolut adaptada

La Fase 0 establece los design tokens visuales inspirados en el sistema Revolut (`DESIGN-revolut.md`), adaptados a una app de escritorio financiero (no marketing site). Estos tokens se implementan en `tailwind.config.ts` y en variables CSS globales.

### Adaptaciones clave respecto al original

| Decisión Revolut | Adaptación AI Financial OS |
|---|---|
| Aeonik Pro (propietaria) | **Inter** para todo (display + body). Inter Display para headings grandes si disponible. |
| Canvas full-bleed marketing | Sidebar fijo + área de contenido scrollable |
| Dos modos luz/oscuro | **Solo dark** en V1 (decisión cerrada en doc 00) |
| CTAs pill blancos sobre negro | Mismo patrón para botones primarios |
| Breakpoints web responsive | Ventana desktop fija, sin responsive web |

### Tokens de color (CSS custom properties + Tailwind)

```
canvas-dark:       #000000   ← fondo principal de la app
surface-deep:      #0a0a0a   ← sidebar
surface-elevated:  #16181a   ← cards, paneles
surface-card:      #1e2124   ← cards secundarias
primary:           #494fdf   ← accent brand (cobalt violet)
primary-bright:    #4f55f1
on-primary:        #ffffff
on-dark:           #ffffff
on-dark-mute:      rgba(255,255,255,0.72)
hairline-dark:     rgba(255,255,255,0.12)
divider-soft:      rgba(255,255,255,0.06)
stone:             #8d969e   ← texto terciario / labels
mute:              #505a63   ← texto secundario
accent-teal:       #00a87e   ← valores positivos / ganancias
accent-danger:     #e23b4a   ← valores negativos / pérdidas
accent-warning:    #ec7e00   ← alertas
accent-yellow:     #b09000   ← pendiente / neutro
```

### Tokens de tipografía

```
font-family:  Inter (system fallback: ui-sans-serif, sans-serif)

display-lg:   32px / weight 600 / tracking -0.32px   ← títulos de página
heading-md:   24px / weight 600 / tracking 0          ← títulos de sección
heading-sm:   20px / weight 500 / tracking 0          ← subtítulos
body-md:      16px / weight 400 / tracking 0.24px     ← texto base
body-sm:      14px / weight 400 / tracking 0          ← captions, metadata
button-md:    16px / weight 600 / tracking 0.24px     ← labels de botones
caption:      13px / weight 400 / tracking 0          ← texto de apoyo
```

### Tokens de forma y espaciado

```
rounded-sm:   8px    ← chips, badges
rounded-md:   12px   ← inputs, tiles pequeños
rounded-lg:   20px   ← cards principales
rounded-xl:   28px   ← paneles modales
rounded-full: 9999px ← botones, pills

spacing-xs:   6px
spacing-sm:   8px
spacing-md:   14px
spacing-lg:   16px
spacing-xl:   24px
spacing-2xl:  32px
spacing-3xl:  48px
```

### Patrones de componente base (Fase 0)

- **Botón primario**: fondo `on-dark` (#fff), texto `canvas-dark` (#000), `rounded-full`, height 40px. Igual al patrón Revolut white-pill-on-dark.
- **Botón secundario**: fondo `surface-elevated`, texto `on-dark`, `rounded-full`.
- **Card**: fondo `surface-elevated` (#16181a), borde `hairline-dark`, `rounded-lg`.
- **Sidebar**: fondo `surface-deep` (#0a0a0a), ancho 240px fijo.
- **Área de contenido**: fondo `canvas-dark` (#000000).
- **Sin sombras**: la profundidad se logra únicamente por diferencia de luminancia entre superficies (principio Revolut).

### Archivos nuevos en Fase 0

| Archivo | Contenido |
|---|---|
| `apps/desktop/src/lib/design-tokens.ts` | Export de todos los tokens como constantes TypeScript |
| `apps/desktop/tailwind.config.ts` | Extensión de Tailwind con los tokens de color, tipografía, spacing y rounded |
| `apps/desktop/src/index.css` | Variables CSS custom properties + @import Inter + reset base dark |

---

## Restricciones

- Sin lógica financiera (Fase 1).
- Sin importadores CSV (Fase 2).
- Sin IA (Fase 6).
- CORS permitido solo a `localhost` y `tauri://localhost`.
- No introducir dependencias cloud.
- Idioma de la UI: español.
- Tema: dark premium.

---

## Criterio de éxito (Definition of Done — Fase 0)

- `uv run fastapi dev app/main.py` arranca sin errores y `GET /health` devuelve `{"status":"ok","version":"0.1.0"}`.
- `npm run tauri dev` abre la ventana desktop con sidebar y navegación base.
- Todos los módulos backend tienen su router registrado (sin endpoints reales aún).
- Todas las rutas frontend tienen su página placeholder.
- El repo compila sin errores de TypeScript ni de Python.
