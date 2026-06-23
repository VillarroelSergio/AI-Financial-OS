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

## Documentación

Ver `docs/` para arquitectura, modelo de datos, contrato API y roadmap.


Para usar la herramienta de capturas desde apps/desktop/:


npm run ux:snapshots        # captura 8 rutas en headless
npm run ux:snapshots:headed # ídem con navegador visible
npm run ux:report           # muestra resumen de la última capt
