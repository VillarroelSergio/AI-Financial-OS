# 30 - Packaging & Release (Fase 11)

## Arquitectura de empaquetado

La aplicación se distribuye como instalador Windows (`.msi` y `.exe` NSIS) generado
por Tauri. El backend FastAPI se compila con PyInstaller a un directorio autocontenido
(`financial-backend/`, modo onedir) que se incluye como *resource* del bundle Tauri.
El usuario final no necesita Python, Node ni ninguna dependencia adicional.

### Arranque coordinado

1. El ejecutable Tauri arranca y, en `setup`, lanza `financial-backend.exe` como
   proceso hijo (sin ventana de consola, `CREATE_NO_WINDOW`).
2. Hace polling de `GET http://127.0.0.1:8010/health` cada 250 ms (timeout 60 s).
3. Solo cuando `/health` responde `200` se crea la ventana principal — la UI nunca
   es interactiva sin backend.
4. Al cerrar la aplicación (`RunEvent::Exit`), el proceso hijo se termina. No quedan
   backends huérfanos.
5. Si ya hay un backend sirviendo `/health` en el puerto 8010 (p. ej. sesión de
   desarrollo), no se lanza un duplicado.

Código: `apps/desktop/src-tauri/src/lib.rs`.

### Rutas de datos en producción

En modo empaquetado (`sys.frozen`), `backend/run_server.py` fija — antes de importar
la app — las variables de entorno de datos apuntando a `%APPDATA%\FinancialAgent\`:

| Recurso | Ruta |
|---|---|
| SQLite (financiero) | `%APPDATA%\FinancialAgent\financial.db` |
| DuckDB (analytics/MI) | `%APPDATA%\FinancialAgent\analytics.duckdb` |
| Backups | `%APPDATA%\FinancialAgent\backups\` |
| Insights descartados | `%APPDATA%\FinancialAgent\dismissed_insights.json` |

En desarrollo nada cambia: `./backend/data/` como siempre. La ruta se puede
sobrescribir con la variable de entorno `FINOS_DATA_DIR`.

## Cómo generar un release

Requisitos de la máquina de build: Rust (toolchain MSVC), Node 18+, `uv`.

```powershell
.\scripts\build-release.ps1
```

El script hace tres pasos:

1. `uv run --group build pyinstaller financial-backend.spec` en `backend/` —
   genera `backend/dist/financial-backend/`.
2. Copia el resultado a `apps/desktop/src-tauri/binaries/backend/` (dir ignorado
   por git; el bundle lo incluye vía `bundle.resources`).
3. `npm run tauri build` — compila frontend + Rust y genera los instaladores en
   `apps/desktop/src-tauri/target/release/bundle/msi/` y `...\bundle\nsis\`.

`-SkipBackend` reutiliza el `dist/` de PyInstaller existente (iteración rápida
sobre la parte Tauri).

## Verificación post-build (smoke test)

```powershell
.\scripts\smoke-test.ps1
```

Comprueba, contra el binario de `target/release`:

- La app arranca y `/health` responde `200` dentro del timeout (mide el tiempo).
- La ventana permanece estable tras el arranque.
- Al cerrar la ventana, el backend hijo muere (sin procesos huérfanos).

Requiere el puerto 8010 libre (cerrar cualquier backend de desarrollo antes).

## Instalación y primer arranque

1. Ejecutar el `.msi` (o el `-setup.exe` NSIS, instalación por usuario sin admin).
2. Lanzar "AI Financial OS" desde el menú Inicio.
3. Primer arranque: se crea `%APPDATA%\FinancialAgent\` con base de datos vacía y
   categorías/ajustes sembrados automáticamente. La ventana aparece cuando el
   backend está listo (objetivo <5 s en hardware i5/8GB).
4. La IA local es opcional: si Ollama/LM Studio no están instalados, el asistente
   lo indica de forma honesta (health check pre-flight de Fase 10.6).

### Desinstalación

El desinstalador elimina el programa pero **conserva los datos del usuario** en
`%APPDATA%\FinancialAgent\` (comportamiento por defecto de NSIS/MSI en Tauri v2:
solo borra lo que instaló). Para un borrado completo, eliminar esa carpeta
manualmente.

## Resolución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| La ventana no llega a abrirse | Backend no arrancó en 60 s | Revisar que el puerto 8010 no esté ocupado por otro proceso; reintentar |
| "Puerto 8010 ocupado" en smoke test | Backend de desarrollo activo | Cerrar `uvicorn`/`dev.ps1` antes del test |
| Antivirus bloquea el instalador | Binario sin firmar | Firmar el binario (pendiente, ver siguiente sección) o añadir excepción |
| Datos desaparecidos tras reinstalar | Se borró `%APPDATA%\FinancialAgent\` a mano | Restaurar desde `backups\` (Ajustes → Backups) |
| Arranque lento (>5 s) | Primer arranque siembra BD + ingesta MI en frío | Los arranques siguientes son más rápidos; la ingesta es asíncrona |

## Canal de actualización (preparado, no activo)

El auto-updater de Tauri queda **diferido a la primera release pública** porque
requiere infraestructura que aún no existe:

1. Generar par de claves: `npm run tauri signer generate`.
2. Añadir `tauri-plugin-updater` y en `tauri.conf.json` → `plugins.updater`:
   `pubkey` + `endpoints` (URL del manifiesto `latest.json`, p. ej. GitHub Releases).
3. Publicar cada release con sus artefactos firmados (`.sig`) y el manifiesto.

Hasta entonces, las actualizaciones son manuales: instalar el nuevo `.msi` encima
(los datos de usuario no se tocan).

## Estado de criterios de aceptación (Fase 11)

| Criterio | Estado |
|---|---|
| `tauri build` produce `.msi` sin errores | Implementado — pendiente de ejecutar build limpio |
| Sin dependencias externas para el usuario | Implementado (PyInstaller onedir embebido) |
| Arranque <5 s en i5/8GB | Medible con `smoke-test.ps1` (imprime el tiempo) |
| `/health` 200 antes de ventana interactiva | Implementado (bloqueo en `setup`) |
| Datos persisten en `%APPDATA%\FinancialAgent\` | Implementado (`run_server.py`) |
| Desinstalación sin residuos, datos conservados | Comportamiento por defecto del bundle Tauri v2 |
| Smoke test automatizado | `scripts/smoke-test.ps1` |
| Documentación de instalación | Este documento |
