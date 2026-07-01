# AI-Financial-OS — Pre-Release 1.0 Audit Report

**Fecha:** 2026-06-30
**Rama:** fix/corrections-and-stabilization
**Auditor:** Claude Code (análisis automatizado multi-agente)

---

## Resumen Ejecutivo

Auditoría pre-release completada en 5 dominios: Seguridad, Código Muerto Frontend, Código Muerto Backend, Higiene del Repositorio y Documentación. Se identificaron **46 hallazgos** en total:

| Severidad | Cantidad |
|-----------|----------|
| CRÍTICO   | 1        |
| ALTO      | 12       |
| MEDIO     | 16       |
| BAJO      | 17       |
| **TOTAL** | **46**   |

El dominio con mayor deuda es **Documentación** (15 hallazgos, incluido el único CRÍTICO). Seguridad, Backend e Higiene presentan 3 hallazgos ALTO cada uno. Frontend y Seguridad no tienen CRÍTICOS.

### Blockers de Release (CRÍTICO + ALTO)

Los siguientes 13 hallazgos **deben resolverse antes de taggear 1.0**:

1. **DOC-0 [CRÍTICO]** — README sin documentación de instalación para usuario final (primer arranque post `.msi`). Los criterios de aceptación de Fase 11 lo exigen explícitamente.
2. **SEC-1 [ALTO]** — CSP nula en `tauri.conf.json`. Una app de finanzas personales con `csp: null` permite XSS sin barrera de política en la ventana Tauri.
3. **SEC-2 [ALTO]** — Rutas absolutas del sistema de archivos expuestas en `GET /api/security/status` y `GET /api/security/backups` (p. ej. `C:\Users\Sergio Villa\...\financial.db`).
4. **SEC-3 [ALTO]** — `*.json` en `.gitignore` es una regla demasiado amplia que silenciosamente bloqueará cualquier nuevo JSON legítimo. Debe ser reemplazada por reglas scoped antes del release.
5. **BE-1 [ALTO]** — Ghost modules `economic_data/` e `investments/market_data/` con solo `__pycache__` y sin fuente `.py`. Riesgo de importación como namespace package y confusión de desarrolladores.
6. **BE-2 [ALTO]** — `backend/tests/market_intelligence/` (13 archivos, 400+ líneas) fuera del `testpaths` de pytest. Regresiones de `market_intelligence` no se detectan en el ciclo CI/CD.
7. **BE-3 [ALTO]** — 49 imports F401 (no utilizados) detectados por ruff en producción y tests. Al menos 11 casos en módulos de producción críticos.
8. **HYG-1 [ALTO]** — `market-data-poc/` (99 archivos, ~458 KB) rastreado en git. PoC excluida del release 1.0 sin dependencias activas desde producción.
9. **HYG-2 [ALTO]** — `graphify-out/` parcialmente rastreado: 6 archivos de control en índice git; `graph.html` (~587 KB) sin cobertura de ignore.
10. **HYG-3 [ALTO]** — Mismo hallazgo que SEC-3: regla `*.json` global en `.gitignore` (línea 42) debe reemplazarse por reglas scoped a `graphify-out/`.
11. **DOC-1 [ALTO]** — README sin instrucciones de configuración de `.env` / `.env.example`.
12. **DOC-2 [ALTO]** — README sin instrucciones de build para distribución (`tauri build`, generación de `.msi`/`.exe`).
13. **DOC-3 [ALTO]** — No existe archivo `LICENSE` ni mención de licencia en el README.

> **Nota:** SEC-3 y HYG-3 son el mismo hallazgo estructural visto desde dos dominios. La acción de remediación es única: editar `.gitignore` para reemplazar la línea `*.json` por reglas scoped.

### Deuda Técnica Aceptada (MEDIO + BAJO)

33 hallazgos de severidad MEDIO (16) y BAJO (17) pueden diferirse al roadmap post-1.0 sin riesgo de bloqueo funcional o de seguridad. Incluyen: limpieza de código muerto frontend (FE-1 a FE-8), mejoras defensivas de seguridad (SEC-4, SEC-5), módulos vacíos de backend (BE-4 a BE-9), higiene documental (HYG-4 a HYG-7), reorganización de docs internos (DOC-4 a DOC-15), y completado del API Contract.

---

## Seguridad

**Fecha de auditoría:** 2026-06-30
**Auditor:** Security Analysis Agent
**Rama:** HEAD (main)
**Alcance:** Historial git, configuración de entorno, CORS, Tauri, validación de inputs en endpoints críticos

### Resumen de Seguridad

| Severidad | Cantidad |
|-----------|----------|
| CRÍTICO   | 0        |
| ALTO      | 3        |
| MEDIO     | 2        |
| BAJO      | 2        |

No se encontraron secretos reales en el historial de git ni en los archivos `.env.example`. Los hallazgos más relevantes son la CSP nula en Tauri, la ruta completa del sistema de archivos expuesta en la API de seguridad, y el patrón `*.json` en `.gitignore` que podría silenciosamente ignorar nuevos archivos JSON rastreados.

### Hallazgos de Seguridad

#### SEC-1: CSP nula en Tauri — sin Content Security Policy
- **Severidad:** ALTO
- **Archivo:** `apps/desktop/src-tauri/tauri.conf.json:23`
- **Descripción:** El campo `app.security.csp` está explícitamente establecido como `null`. Esto deshabilita la Content Security Policy de Tauri, lo que permite que cualquier script inline, recurso externo o frame arbitrario se ejecute en la ventana de la aplicación. En una app de finanzas personales con datos sensibles, un XSS (por ejemplo, a través de contenido importado o respuestas del AI) podría leer el DOM sin ninguna barrera de política.
- **Acción:** Definir una CSP restrictiva. Ejemplo mínimo para una app Tauri + Vite local:
  ```json
  "csp": "default-src 'self'; script-src 'self'; connect-src 'self' http://localhost:8000 http://localhost:11434 http://localhost:1234; img-src 'self' data:; style-src 'self' 'unsafe-inline'"
  ```
  Ajustar `connect-src` a los orígenes reales del backend y los modelos AI locales.

---

#### SEC-2: Ruta absoluta del sistema de archivos expuesta en la API pública
- **Severidad:** ALTO
- **Archivo:** `backend/app/modules/security/routes.py:21` y `backend/app/modules/security/service.py:39,52`
- **Descripción:** El endpoint `GET /api/security/status` devuelve el campo `database_path` con la ruta absoluta resuelta de la base de datos en el sistema de archivos del host (por ejemplo, `C:\Users\Sergio Villa\...\financial.db`). Los endpoints `GET /api/security/backups` y `POST /api/security/backups` también retornan el campo `path` con rutas absolutas completas de los ficheros de backup. Esta información revela la estructura de directorios del usuario al frontend (y a cualquiera que intercepte el tráfico HTTP local).
- **Acción:** En los schemas de respuesta (`SecurityStatusOut`, `BackupOut`), reemplazar las rutas absolutas por rutas relativas o simplemente el nombre de archivo. Eliminar el campo `path` de `BackupOut` o sustituirlo por un identificador opaco. En `SecurityStatusOut`, sustituir `database_path` por un estado booleano o un identificador de perfil.

---

#### SEC-3: El patrón `*.json` en `.gitignore` puede silenciar silenciosamente el tracking de nuevos archivos JSON
- **Severidad:** ALTO
- **Archivo:** `.gitignore:42`
- **Descripción:** La última línea del `.gitignore` es `*.json`, que aplica recursivamente a todo el repositorio. Aunque los archivos JSON ya rastreados siguen apareciendo en git, **cualquier nuevo archivo JSON que se cree y no haya sido rastreado previamente quedará ignorado automáticamente sin aviso**. La intención probable era ignorar solo los artefactos de `graphify-out/`, no todos los JSON.
- **Acción:** Reemplazar la línea `*.json` por patrones más precisos:
  ```
  # Data exports / generated JSON
  graphify-out/
  graphify-out/**/*.json
  ```
  Si la intención era ignorar archivos locales de configuración IDE, usar `*.local.json` en su lugar.

---

#### SEC-4: `AI_ENABLE_TOOL_TRACE` habilitado por defecto en producción
- **Severidad:** MEDIO
- **Archivo:** `backend/app/core/config.py:26`
- **Descripción:** La variable `AI_ENABLE_TOOL_TRACE` tiene valor por defecto `True`. Si este trace se registra en logs o se devuelve en respuestas de API, puede exponer información sobre transacciones, balances u otras operaciones financieras del usuario en entornos de producción.
- **Acción:** Cambiar el valor por defecto a `False` en `config.py`. Activarlo explícitamente solo en entornos de desarrollo (`APP_ENV=development`).

---

#### SEC-5: El endpoint `/api/rag/documents/upload` no valida el `Content-Type` (MIME sniffing)
- **Severidad:** MEDIO
- **Archivo:** `backend/app/modules/rag/routes.py:41-63`
- **Descripción:** La validación de tipo MIME se basa únicamente en `file.content_type`, que proviene del header `Content-Type` de la petición HTTP —valor que el cliente puede falsificar libremente. Un atacante podría subir un archivo con extensión `.txt` pero contenido arbitrario. El contenido se almacena en la base de datos y se devuelve como fragmentos en consultas RAG, lo que podría usarse para envenenar el contexto del asistente AI.
- **Acción:** Añadir validación de contenido real en `extract_text()`: verificar que el contenido decodificado es texto plano válido UTF-8 y no contiene caracteres nulos (`\x00`) ni secuencias binarias. Para CSV y JSON, intentar parsear el contenido y rechazar si falla.

---

#### SEC-6: La variable `OPENCORPORATES_API_KEY` está en `.env.example` raíz pero no en `backend/.env.example`
- **Severidad:** BAJO
- **Archivo:** `.env.example:16`
- **Descripción:** Los dos archivos `.env.example` del proyecto están desincronizados. Esta inconsistencia puede llevar a que un desarrollador configure las claves en un archivo y no en el otro.
- **Acción:** Unificar ambos archivos `.env.example`. Considerar eliminar el `.env.example` de la raíz y usar únicamente `backend/.env.example` como fuente de verdad.

---

#### SEC-7: `shell:allow-open` en capabilities de Tauri sin restricción de esquema
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src-tauri/capabilities/default.json:8`
- **Descripción:** La capability `shell:allow-open` permite invocar `shell.open()` para abrir URLs o rutas sin una lista de esquemas permitidos explícita. Podría ser posible abrir URLs con esquemas arbitrarios como `file://` o protocolos de aplicación locales.
- **Acción:** Restringir `shell:allow-open` a esquemas seguros: `https`, `http`, `mailto`.

---

### Verificaciones que pasaron sin hallazgos

- **Historial git:** No se encontraron secretos reales. Las variables `ALPHA_VANTAGE_API_KEY`, `FINNHUB_API_KEY`, `POLYGON_API_KEY` y `FRED_API_KEY` aparecen en el historial únicamente como nombres de variable (con valor vacío), no como claves reales.
- **`.env.example`:** Ambos archivos contienen exclusivamente placeholders vacíos para todas las claves de API.
- **`.gitignore` rutas sensibles:** `.env`, `backend/.env`, `market-data-poc/.env`, `backend/data/` y `data/` están correctamente ignorados.
- **CORS:** `allow_origins` restringido a `["http://localhost:1420", "tauri://localhost", "http://tauri.localhost"]`. No usa `["*"]`.
- **Tauri permissions:** No se encontraron permisos de `fs:read-all`, `fs:write-all`, ni `shell:execute` sin restricciones.

---

## Código Muerto — Frontend (TypeScript/React)

**Fecha de auditoría:** 2026-06-30
**Fuente auditada:** `apps/desktop/src/`
**Pasos ejecutados:** Step 1 (gitkeep vacíos), Step 2 (exports sin importadores), Step 3 (dist en git), Step 4 (rutas App.tsx), Step 5 (console.log/TODO), Step 6 (tailwind/postcss config)

### Resumen Frontend

| Severidad | Cantidad | Hallazgos |
|-----------|----------|-----------|
| CRÍTICO   | 0        | — |
| ALTO      | 0        | — |
| MEDIO     | 3        | FE-1, FE-2, FE-3 |
| BAJO      | 5        | FE-4, FE-5, FE-6, FE-7, FE-8 |

### Hallazgos Frontend

#### FE-1: Directorios vacíos con solo .gitkeep — 5 carpetas estructurales nunca pobladas
- **Severidad:** MEDIO
- **Archivos:** `apps/desktop/src/app/providers/`, `apps/desktop/src/app/routes/`, `apps/desktop/src/components/charts/`, `apps/desktop/src/components/financial/`, `apps/desktop/src/components/import/`
- **Descripción:** Cinco directorios contienen únicamente un `.gitkeep` y cero archivos de código. Fueron creados como scaffolding arquitectónico pero nunca se desarrolló el contenido prometido. El directorio `components/import/` es especialmente confuso porque existe `features/investments/import/` con componentes reales.
- **Acción:** Decidir si estas carpetas son parte de la arquitectura planeada (mantener con comentario en ARCHITECTURE.md) o eliminarlas junto con sus `.gitkeep`.

---

#### FE-2: `lib/design-tokens.ts` — módulo exportado sin ningún importador
- **Severidad:** MEDIO
- **Archivo:** `apps/desktop/src/lib/design-tokens.ts:1`
- **Descripción:** El archivo exporta `colors`, `spacing` y `rounded` como tokens de diseño programáticos. Sin embargo, ningún archivo `.tsx` o `.ts` en `src/` lo importa. Todos los componentes usan clases Tailwind definidas en `tailwind.config.ts` directamente. El módulo es código muerto completo.
- **Acción:** Eliminar `apps/desktop/src/lib/design-tokens.ts`. La paleta está correctamente centralizada en `tailwind.config.ts`.

---

#### FE-3: `lib/hooks/useFinancialKnowledge.ts` — hook completo sin ningún consumidor
- **Severidad:** MEDIO
- **Archivo:** `apps/desktop/src/lib/hooks/useFinancialKnowledge.ts:44`
- **Descripción:** El archivo exporta 6 hooks que envuelven `lib/api/financial-knowledge.ts`. Ninguna página ni componente importa este módulo. La cadena completa `financial-knowledge.ts` (api) → `useFinancialKnowledge.ts` (hook) → `lib/types/financial-knowledge.ts` (tipos) existe únicamente como código muerto.
- **Acción:** Determinar si la feature "Financial Knowledge" está planificada. Si no hay página destino en el roadmap inmediato, mover los tres archivos a una carpeta `_wip/` o eliminarlos.

---

#### FE-4: `components/ui/EmptyState.tsx` — wrapper redundante que duplica `Dashboard.EmptyState`
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src/components/ui/EmptyState.tsx:9`
- **Descripción:** Este archivo es un thin wrapper de 11 líneas que simplemente re-exporta `EmptyState` de `Dashboard.tsx`. Existen dos rutas de importación para el mismo componente, creando inconsistencia.
- **Acción:** Eliminar `EmptyState.tsx` y migrar los 3 importadores a `import { EmptyState } from "@/components/ui/Dashboard"`.

---

#### FE-5: `Dashboard.tsx` — `DataSourceBadge` y `MetricDelta` exportados sin consumidores externos
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src/components/ui/Dashboard.tsx:28` y `:137`
- **Descripción:** `MetricDelta` solo se usa internamente dentro de `Dashboard.tsx`. `DataSourceBadge` no tiene ningún importador en todo el codebase.
- **Acción:** Convertir `MetricDelta` a función privada (quitar `export`). Evaluar si `DataSourceBadge` se usa en algún milestone próximo; si no, eliminar.

---

#### FE-6: `CoverageStatus` definido dos veces en módulos de tipos distintos
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src/lib/types/price-coverage.ts:1` y `apps/desktop/src/lib/types/portfolio-import.ts:24`
- **Descripción:** El tipo `CoverageStatus = "OK" | "FX_PENDING" | "AMBIGUOUS" | "UNAVAILABLE" | "MANUAL" | "ERROR"` está declarado con valores idénticos en dos archivos de tipos independientes.
- **Acción:** Consolidar en `lib/types/price-coverage.ts` y en `portfolio-import.ts` reemplazar la declaración por `import type { CoverageStatus } from "./price-coverage"`.

---

#### FE-7: `lib/api/mock-data.ts` — importado activamente en producción vía `client.ts`
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src/lib/api/client.ts:1`
- **Descripción:** `client.ts` importa `getMockResponse` de `mock-data.ts` incondicionalmente (import estático). El bundle de producción siempre incluirá `mock-data.ts` (~400 líneas de datos de muestra) aunque `VITE_USE_MOCK_DATA` sea `false`.
- **Acción:** Convertir el import a dinámico dentro del bloque `if (USE_MOCK)`, o usar code-splitting con `/* @vite-ignore */`.

---

#### FE-8: `pages/PlanificacionPage.tsx` — ubicada fuera del patrón `features/`
- **Severidad:** BAJO
- **Archivo:** `apps/desktop/src/pages/PlanificacionPage.tsx:17`
- **Descripción:** Todas las páginas siguen el patrón `features/<nombre>/<Nombre>Page.tsx`. Esta es la única página en `src/pages/`, una carpeta que existe solo para este archivo.
- **Acción:** Mover a `apps/desktop/src/features/planning/PlanificacionPage.tsx`, actualizar el import en `App.tsx`, y eliminar el directorio `src/pages/`.

---

### Verificaciones Frontend que pasaron sin hallazgos

- **dist/ en git:** `git ls-files apps/desktop/dist/` devolvió vacío. No hay build output en git.
- **console.log/TODO/debugger:** Cero ocurrencias de `console.log`, `console.error`, `debugger`, `TODO`, `FIXME`, `HACK` o `XXX` en el código fuente.
- **Tailwind config:** El glob `./src/**/*.{ts,tsx}` cubre todos los directorios activos. El `postcss.config.js` es estándar.
- **App.tsx routes:** Todas las 14 rutas definidas apuntan a componentes existentes e importables. Ninguna ruta está comentada ni apunta a componentes inexistentes.

---

## Código Muerto — Backend (Python)

**Fecha:** 2026-06-30
**Auditor:** Backend Dead Code Analysis Agent
**Scope:** `backend/app/` + `backend/tests/` + `backend/cli.py` + `backend/pyproject.toml`

### Resumen Backend

| Severidad | Hallazgos |
|-----------|-----------|
| CRÍTICO   | 0         |
| ALTO      | 3         |
| MEDIO     | 3         |
| BAJO      | 3         |
| **Total** | **9**     |

### Hallazgos Backend ALTO

#### BE-1: Ghost modules — `economic_data` y `investments/market_data` sin fuente Python
- **Severidad:** ALTO
- **Archivo:** `backend/app/modules/economic_data/` y `backend/app/modules/investments/market_data/`
- **Descripción:** Ambos directorios contienen únicamente carpetas `__pycache__/` con `.pyc` compilados (de una versión anterior del módulo) pero **no tienen ningún archivo `.py` fuente** ni `__init__.py`. En Python 3.3+ los namespace packages pueden hacer que un directorio sin `__init__.py` sea importable bajo ciertas condiciones; además, confunden a cualquier desarrollador nuevo que vea `__pycache__/fred_provider.cpython-314.pyc` existir sin fuente visible.
- **Acción:** Eliminar por completo ambos directorios: `git rm -r backend/app/modules/economic_data/` y `git rm -r backend/app/modules/investments/market_data/`. Confirmar que `test_no_legacy_modules.py` sigue pasando después.

---

#### BE-2: `backend/tests/market_intelligence/` fuera del `testpaths` de pytest
- **Severidad:** ALTO
- **Archivo:** `backend/pyproject.toml:27` — `testpaths = ["app/tests"]`
- **Descripción:** El directorio `backend/tests/market_intelligence/` contiene 13 archivos de test (más de 400 líneas de assertions) que NO se ejecutan en el ciclo CI/CD estándar. Todas sus regresiones pasan desapercibidas en el ciclo normal de pytest.
- **Acción:** Si `market_intelligence` es parte de release 1.0, mover los tests a `backend/app/modules/market_intelligence/tests/` o añadir `"tests"` a `testpaths`. Si se excluye del release, marcar los tests como `pytest.mark.skip` con razón explícita.

---

#### BE-3: 49 imports F401 detectados por ruff en código de producción y tests
- **Severidad:** ALTO
- **Archivo:** Múltiples — ver detalle
- **Descripción:** Ruff (F401) detecta **49 imports no utilizados**. Los más relevantes en módulos de **producción** incluyen:
  - `backend/app/modules/ai/memory/conversation_repository.py:11` — `app.core.config.settings` importado pero no usado
  - `backend/app/modules/ai/service.py:16` — `ConversationOut` importado pero no usado
  - `backend/app/modules/ai/tools/portfolio_tools.py:5` — `Decimal` importado pero no usado
  - `backend/app/modules/cashflow/routes.py:5` — `typing.Any` importado pero no usado
  - `backend/app/modules/financial_knowledge/engines/ai_datasheet_generator.py:6,12` — `asdict` y `Severity` importados pero no usados
  - `backend/app/modules/goals/routes.py:4` — `datetime.date` importado pero no usado
  - `backend/app/modules/goals/simulation_service.py:26,27,28` — `math`, `field`, `timedelta` importados pero no usados
  - `backend/app/modules/investments/asset_resolution.py:23` — `field` importado pero no usado
  - `backend/app/modules/investments/portfolio_import_routes.py:20` — `RawPosition` importado pero no usado
  - `backend/app/modules/market_intelligence/ingestion/adapters/global_/*.py` — `ProviderMetadata` sin uso en 8 adaptadores
  - (Tests: 20+ casos adicionales)
- **Acción:** Ejecutar `uv run ruff check app/ --select F401 --fix` desde `backend/`. Revisar manualmente los casos en módulos de producción antes de commitear, especialmente `conversation_repository.py`.

---

### Hallazgos Backend MEDIO

#### BE-4: `backend/app/infrastructure/` — directorio vacío sin propósito
- **Severidad:** MEDIO
- **Archivo:** `backend/app/infrastructure/__init__.py` (0 bytes)
- **Descripción:** El módulo `infrastructure` contiene únicamente un `__init__.py` vacío. Ningún módulo del proyecto importa desde `app.infrastructure`.
- **Acción:** Eliminar el directorio completo (`git rm -r backend/app/infrastructure/`).

---

#### BE-5: Módulos stub vacíos — `ai/prompts` sin contenido útil en `__init__.py`
- **Severidad:** MEDIO
- **Archivo:** `backend/app/modules/ai/prompts/__init__.py` (0 bytes)
- **Descripción:** `backend/app/modules/ai/prompts/` tiene un `__init__.py` vacío que no re-exporta nada de `system_prompt.py`. Los consumidores deben importar directamente desde el submodulo, mientras que el módulo hermano `ai/providers/__init__.py` sí re-exporta correctamente.
- **Acción:** Añadir re-exports al `__init__.py`: `from app.modules.ai.prompts.system_prompt import SYSTEM_PROMPT`. Alternativamente, documentar explícitamente que el import directo es intencional.

---

#### BE-6: `backend/tests/market_intelligence/` sin `conftest.py` propio
- **Severidad:** MEDIO
- **Archivo:** `backend/tests/market_intelligence/` (directorio)
- **Descripción:** El directorio de tests de market_intelligence no tiene `conftest.py`, por lo que al ejecutarse con `pytest tests/` no tendrán acceso a fixtures compartidos.
- **Acción:** Crear `backend/tests/market_intelligence/conftest.py` con los fixtures necesarios (DuckDB in-memory, mocks de CatalogLoader), o documentar el pre-requisito de ejecución explícita.

---

### Hallazgos Backend BAJO

#### BE-7: `backend/cli.py` — no documentado ni referenciado en scripts de dev/producción
- **Severidad:** BAJO
- **Archivo:** `backend/cli.py`
- **Descripción:** `cli.py` es el CLI principal del backend con 12 comandos para Market Intelligence y Financial Knowledge. No hay ninguna referencia en los scripts de dev, en `README.md`, ni entry point en `pyproject.toml`.
- **Acción:** Añadir un entry point en `pyproject.toml`: `[project.scripts] financial-os = "cli:main"`, y documentar los comandos en `README.md` o en `docs/07_ECONOMIC_INTELLIGENCE.md`.

---

#### BE-8: Seeds en producción — `seed_categories` y `seed_settings` en `lifespan()`
- **Severidad:** BAJO
- **Archivo:** `backend/app/main.py:37-40`
- **Descripción:** Las funciones de seed se ejecutan en el `lifespan()` de FastAPI en cada arranque en producción. Aunque son idempotentes, añaden latencia innecesaria a arranques en caliente.
- **Acción:** Mantener para release 1.0 (seguro y funcional). Post-release: mover a un comando CLI separado con variable `AUTO_SEED=true` opcional.

---

#### BE-9: Endpoints de `market_intelligence` sin consumidor frontend
- **Severidad:** BAJO
- **Archivo:** `backend/app/modules/market_intelligence/api/routes.py:52` y `:47`
- **Descripción:** `GET /api/market-intelligence/ai-datasheet` y `GET /api/market-intelligence/snapshot/news` no tienen consumidor en el frontend actual.
- **Acción:** No eliminar antes del release. Documentar en `docs/11_API_CONTRACT.md` como "reserved for CLI / future use".

---

### Notas de Contexto Backend

- Los tests de `backend/tests/market_intelligence/` NO importan de `market-data-poc/`. Todos importan de `app.modules.market_intelligence.*`. El riesgo por imports rotos es NULO.
- `backend/tests/test_no_legacy_modules.py` verifica que `economic_data` e `investments.market_data` NO son importables. Actualmente debería pasar; los directorios con `__pycache__` son residuos a limpiar (BE-1).
- La mayoría de módulos usan `__init__.py` vacíos, convención Python moderna válida. Solo `infrastructure/` (BE-4) y `ai/prompts` (BE-5) tienen consecuencias específicas por el vacío.

---

## Higiene del Repositorio

**Fecha:** 2026-06-30
**Repositorio:** `D:/FinancialAgent/AI-Financial-OS`
**Total archivos rastreados:** 581
**Tamaño total rastreado:** ~3.2 MB

### Resumen Higiene

| Severidad | Hallazgos |
|-----------|-----------|
| CRÍTICO   | 0         |
| ALTO      | 3         |
| MEDIO     | 2         |
| BAJO      | 2         |
| **TOTAL** | **7**     |

**Reducción estimada aplicando ALTO+:**
- `market-data-poc/`: ~458 KB rastreados (99 archivos); directorio en disco ~136 MB (ignorado en futuro)
- `graphify-out/` parcial: ~163 KB rastreados (6 archivos de control/chunk)
- `docs/superpowers/`: ~372 KB rastreados (10 MD de planes/specs)
- **Total reducción en índice git:** ~0.99 MB de archivos rastreados eliminados

### Hallazgos Higiene

#### HYG-1: market-data-poc/ rastreado en git — PoC excluida del release 1.0
- **Severidad:** ALTO
- **Archivos afectados:** 99 archivos — `market-data-poc/**` (Python adapters, scrapers, services, tests, validators, `uv.lock`)
- **Descripción:** El directorio `market-data-poc/` es un prototipo de exploración cuyo código relevante fue portado a `backend/app/modules/market_intelligence/`. Las referencias en el backend son solo comentarios de origen (`# Adaptado de market-data-poc/...`), no imports activos. El PoC puede excluirse del repo sin romper el build.
- **Remediación:**
  ```bash
  git rm -r --cached market-data-poc/
  echo "market-data-poc/" >> .gitignore
  git commit -m "chore: untrack market-data-poc (PoC excluded from release 1.0)"
  ```

---

#### HYG-2: graphify-out/ — archivos de control rastreados; archivos grandes fuera de ignore parcial
- **Severidad:** ALTO
- **Archivos afectados:**
  - Rastreados (6): `graphify-out/.chunk1_files.txt`, `.chunk2_files.txt`, `.chunk3_files.txt`, `.graphify_python`, `.graphify_root`, `GRAPH_REPORT.md`
  - No rastreados pero SIN cobertura de ignore: `graphify-out/graph.html` (~587 KB)
  - No rastreados, ya cubiertos por `*.json`: `graph.json` (13 MB), `manifest.json` (440 KB)
- **Descripción:** Los archivos `.chunk*_files.txt`, `.graphify_python`, `.graphify_root` son metadatos de estado de la herramienta graphify, regenerables automáticamente. `GRAPH_REPORT.md` (~166 KB) es un reporte generado, no documentación del producto. `graph.html` (~587 KB) podría añadirse accidentalmente al git.
- **Remediación:**
  ```bash
  git rm -r --cached graphify-out/
  echo "graphify-out/" >> .gitignore
  git commit -m "chore: untrack graphify-out (tool output, fully regenerable)"
  ```
  > Si se quiere conservar `GRAPH_REPORT.md` como documentación de arquitectura, moverlo a `docs/architecture/GRAPH_REPORT.md` antes de aplicar el `git rm`.

---

#### HYG-3: *.json en .gitignore — regla demasiado amplia, bloquea nuevos JSON legítimos
- **Severidad:** ALTO
- **Archivos afectados:** `.gitignore` línea 42 (`*.json`); archivos actualmente rastreados: `apps/desktop/package.json`, `apps/desktop/package-lock.json`, `apps/desktop/src-tauri/capabilities/default.json`, `apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/tsconfig.json`, `package.json`, `tools/ux-snapshot/package.json`, `tools/ux-snapshot/package-lock.json`, `tools/ux-snapshot/tsconfig.json`
- **Descripción:** La regla `*.json` no afecta los 9 JSON ya rastreados pero **sí bloquea** cualquier nuevo JSON que se quiera añadir al repo (nuevos `tsconfig.json`, configs, fixtures de test, etc.). Es una trampa operacional silenciosa.
- **Remediación:**
  Reemplazar la regla `*.json` global por reglas específicas en `.gitignore`:
  ```
  # Eliminar línea: *.json
  # Añadir en sección "graphify / tool artifacts":
  graphify-out/
  graphify-out/**/*.json
  graphify-out/cache/
  ```

---

#### HYG-4: docs/superpowers/ — planes y specs de desarrollo rastreados como documentación de producto
- **Severidad:** MEDIO
- **Archivos afectados:** 10 archivos Markdown (planes e implementación AI-asistida)
- **Descripción:** Estos son artefactos del proceso de desarrollo AI-asistido (planes de implementación y specs de diseño generados por superpowers). No son documentación del producto. Su presencia en `docs/` viola la "Regla documental" del propio `02_ROADMAP.md`.
- **Remediación (Opción A — excluir):**
  ```bash
  git rm -r --cached docs/superpowers/
  echo "docs/superpowers/" >> .gitignore
  git commit -m "chore: untrack docs/superpowers (internal AI development artifacts)"
  ```
  **Opción B (conservar):** Mover a `docs/internal/` y documentar que son artefactos internos.

---

#### HYG-5: Directorio duplicado data/ — root/data vs backend/data
- **Severidad:** MEDIO
- **Archivos afectados:** `data/` (root con `analytics.duckdb` 7.1 MB desactualizado), `backend/data/` (activo con `analytics.duckdb` 17.8 MB)
- **Descripción:** El backend usa `backend/data/` (directorio activo). El `data/` del root es una reliquia de una configuración anterior. Ambos están en `.gitignore` correctamente; solo el `.gitkeep` en `data/` está rastreado. El directorio duplicado desperdicia ~7.3 MB de disco.
- **Remediación:**
  ```bash
  git rm data/.gitkeep
  # rm -rf data/  (eliminar el directorio físico con datos desactualizados)
  ```

---

#### HYG-6: ux-snapshots/ — solo metadatos rastreados (PNGs ignorados por .gitignore local)
- **Severidad:** BAJO
- **Archivos afectados:** `ux-snapshots/.gitignore`, `ux-snapshots/latest/UX_REVIEW_CONTEXT.md`
- **Descripción:** Solo 2 archivos rastreados. El `UX_REVIEW_CONTEXT.md` es un artefacto del proceso de revisión visual, no documentación de producto. El riesgo actual es bajo.
- **Remediación (opcional):**
  ```bash
  git rm -r --cached ux-snapshots/
  echo "ux-snapshots/" >> .gitignore
  ```

---

#### HYG-7: .superpowers/sdd/ — artefactos de desarrollo AI protegidos por .gitignore local
- **Severidad:** BAJO
- **Archivos afectados:** 0 archivos rastreados — protegidos por `.superpowers/sdd/.gitignore: *`
- **Descripción:** El directorio `.superpowers/sdd/` está correctamente protegido. La situación es correcta pero la protección depende únicamente del `.gitignore` local. Si alguien elimina ese archivo, los artefactos quedarían expuestos.
- **Remediación:**
  ```bash
  echo ".superpowers/" >> .gitignore
  ```

---

### Comandos de Remediación (Higiene)

Ejecutar en el siguiente orden seguro para evitar conflictos:

**1. Primero: corregir `.gitignore` (HYG-3 / SEC-3)**
```bash
# Editar .gitignore: eliminar la línea "*.json" (línea 42) y añadir reglas específicas
# El archivo debe quedar con estas líneas en la sección de artefactos de herramientas:

# Tool artifacts — graphify
graphify-out/
graphify-out/**/*.json
graphify-out/cache/

# PoC excluida de release 1.0
market-data-poc/

# Artefactos de proceso AI-asistido (belt-and-suspenders)
.superpowers/

# Snapshots de UI (generados on-demand)
ux-snapshots/
```

**2. Segundo: untrack market-data-poc/ (HYG-1)**
```bash
git -C d:/FinancialAgent/AI-Financial-OS rm -r --cached market-data-poc/
```

**3. Tercero: untrack graphify-out/ (HYG-2)**
```bash
git -C d:/FinancialAgent/AI-Financial-OS rm -r --cached graphify-out/
```

**4. Cuarto: eliminar ghost modules (BE-1)**
```bash
git -C d:/FinancialAgent/AI-Financial-OS rm -r backend/app/modules/economic_data/
git -C d:/FinancialAgent/AI-Financial-OS rm -r backend/app/modules/investments/market_data/
```

---

## Documentación

**Fecha:** 2026-06-30
**Auditor:** Agent Task 5
**Scope:** `docs/`, `README.md`

### Resumen Documentación

| Severidad | Hallazgos |
|-----------|-----------|
| CRÍTICO   | 1         |
| ALTO      | 3         |
| MEDIO     | 6         |
| BAJO      | 5         |
| **Total** | **15**    |

**README readiness:** NO listo para release 1.0. Faltan secciones críticas (instalación usuario final, `.env`, build de distribución, licencia).

### Hallazgos Documentación

#### DOC-0: README sin instrucciones de primer arranque tras instalación (release 1.0)
- **Severidad:** CRÍTICO
- **Archivo:** `README.md`
- **Descripción:** El README actual solo documenta el flujo de desarrollo. No incluye ninguna sección dirigida al usuario final que instale el `.msi`/`.exe` del release: cómo arrancar la aplicación instalada, dónde se almacenan los datos (`%APPDATA%\FinancialAgent\`), cómo gestionar el primer uso o cómo resolver problemas comunes de arranque. Los criterios de aceptación de Fase 11 exigen explícitamente "Documentación de instalación, primer arranque y resolución de problemas comunes". Esta sección no existe en ningún doc actual.
- **Acción:** Añadir sección "## Instalación (usuario final)" al README (o crear `docs/INSTALL.md`) con: enlace al instalador, pasos de primer arranque, ubicación de datos, y sección de troubleshooting mínimo.

---

#### DOC-1: README sin instrucciones de configuración de `.env`
- **Severidad:** ALTO
- **Archivo:** `README.md`
- **Descripción:** El README documenta cómo arrancar en desarrollo pero no menciona ni referencia ningún archivo `.env` o `.env.example`. El usuario que clone el proyecto no sabrá qué variables de entorno son necesarias para el backend.
- **Acción:** Crear `backend/.env.example` con las variables necesarias y añadir sección "Configuración de entorno" al README que lo referencie.

---

#### DOC-2: README sin instrucciones de build para distribución
- **Severidad:** ALTO
- **Archivo:** `README.md`
- **Descripción:** El README explica cómo correr el proyecto en modo desarrollo pero no incluye ninguna sección sobre cómo hacer el build instalable (`tauri build`, generación del `.msi`/`.exe`). Los criterios de aceptación de Fase 11 exigen "Documentación de instalación revisada y publicada".
- **Acción:** Añadir sección "## Build de distribución" al README con `cd apps/desktop && npm run tauri build` y las condiciones previas necesarias.

---

#### DOC-3: README sin información de licencia
- **Severidad:** ALTO
- **Archivo:** `README.md`
- **Descripción:** No existe archivo `LICENSE` en la raíz ni mención de licencia en el README. Para un producto instalable (release 1.0) es requisito básico declarar bajo qué términos se distribuye.
- **Acción:** Añadir archivo `LICENSE` en la raíz del repositorio y añadir sección "## Licencia" al README.

---

#### DOC-4: `docs/02_ROADMAP.md` — Fase 6.4 marcada "En curso" cuando fases posteriores ya están completas
- **Severidad:** MEDIO
- **Archivo:** `docs/02_ROADMAP.md`
- **Descripción:** La tabla de estado muestra Fase 6.4 "Data Integrity & Core UX Repair" como `En curso`, mientras que fases 8, 8.5, 8.6, 9, 10, 10.5 y 10.6 están marcadas como completadas. La sección "Próximas fases" incluye Fases 6.4 y 6.4.1 en tiempo futuro como si aún no existieran.
- **Acción:** Actualizar la tabla de estado: marcar Fase 6.4 como completada. Corregir el formato de Fases 9 y 10. Mover las secciones de fases 6.x a un bloque "Historial".

---

#### DOC-5: `docs/13_CLAUDE_CODE_GUIDE.md` — Documento de proceso interno de desarrollo
- **Severidad:** BAJO
- **Archivo:** `docs/13_CLAUDE_CODE_GUIDE.md`
- **Descripción:** Describe cómo Claude Code debe comportarse como implementador del proyecto. Es documentación de proceso interno de desarrollo con IA, no documentación de producto. Referencias dos documentos inexistentes: `08_UX_UI_GUIDELINES.md` y `09_DESIGN_SYSTEM.md`.
- **Acción:** Mover a `docs/internal/13_CLAUDE_CODE_GUIDE.md`. Crear docs 08 y 09 o eliminar las referencias.

---

#### DOC-6: `docs/Styles/DESIGN.md` y `docs/Styles/variables.css` — Artefactos de diseño sin referencias activas
- **Severidad:** BAJO
- **Archivo:** `docs/Styles/DESIGN.md`, `docs/Styles/variables.css`
- **Descripción:** Ninguna referencia desde `apps/`. Son artefactos del proceso de diseño del frontend.
- **Acción:** Mover a `docs/internal/Styles/` o a `.superpowers/` como material de referencia de diseño.

---

#### DOC-7: `docs/28_PHASE_10_5_RELEASE_READINESS_REPORT.md` — Informe de sprint
- **Severidad:** MEDIO
- **Archivo:** `docs/28_PHASE_10_5_RELEASE_READINESS_REPORT.md`
- **Descripción:** Informe de evaluación de estado al finalizar Fase 10.5. Historial de sprint/proceso, no documentación de producto.
- **Acción:** Mover a `docs/internal/`.

---

#### DOC-8: `docs/29_PHASE_10_5_UX_TEST_BATTERY.md` — Batería de pruebas de fase
- **Severidad:** MEDIO
- **Archivo:** `docs/29_PHASE_10_5_UX_TEST_BATTERY.md`
- **Descripción:** Registra resultados de la batería de pruebas de Fase 10.5. El resultado QA manual end-to-end está marcado como "pendiente con datos reales", indicando un artefacto incompleto de proceso.
- **Acción:** Mover a `docs/internal/`.

---

#### DOC-9: `docs/31_PHASE_10_6_RELEASE_CANDIDATE_STABILIZATION.md` — Informe de sprint de Fase 10.6
- **Severidad:** MEDIO
- **Archivo:** `docs/31_PHASE_10_6_RELEASE_CANDIDATE_STABILIZATION.md`
- **Descripción:** Informe de cierre de Fase 10.6: P0/P1 corregidos, estadísticas de tests (206/206), veredicto GO para Fase 11. Documentación de proceso interno.
- **Acción:** Mover a `docs/internal/`.

---

#### DOC-10: `docs/30_RELEASE_CANDIDATE_QA_TEST_PLAN.md` — Plan de QA de proceso interno
- **Severidad:** MEDIO
- **Archivo:** `docs/30_RELEASE_CANDIDATE_QA_TEST_PLAN.md`
- **Descripción:** Define la batería de pruebas para validar Fase 10.6 antes de Packaging. Documento de proceso de desarrollo, no de producto.
- **Acción:** Mover a `docs/internal/`.

---

#### DOC-11: `docs/26_UX_FUNCTIONAL_QA_PRODUCT_INTELLIGENCE_REPAIR.md` — Mezcla de spec de fase y documentación de producto
- **Severidad:** BAJO
- **Archivo:** `docs/26_UX_FUNCTIONAL_QA_PRODUCT_INTELLIGENCE_REPAIR.md`
- **Descripción:** Mezcla objetivos de fase con tabla de puntos completados (changelog de sprint). Limítrofe entre proceso y producto.
- **Acción:** Extraer información de feature a docs correspondientes (20–25). Mover el resto a `docs/internal/`.

---

#### DOC-12: `docs/27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md` — Spec de UI Polish de Fase 10.5
- **Severidad:** BAJO
- **Archivo:** `docs/27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`
- **Descripción:** Spec/guía de implementación de diseño de Fase 10.5. Solapamiento conceptual con `docs/Styles/DESIGN.md`.
- **Acción:** Consolidar en `docs/Styles/DESIGN.md` como design system vigente, y mover a `docs/internal/` como spec de implementación de fase.

---

#### DOC-13: `docs/11_API_CONTRACT.md` — Endpoints implementados no documentados
- **Severidad:** MEDIO
- **Archivo:** `docs/11_API_CONTRACT.md`
- **Descripción:** El contrato omite los siguientes grupos que sí existen en el código:
  - `/api/investments/assets` (CRUD de InvestmentAsset)
  - `/api/investments/operations` (GET, POST)
  - `/api/investments/prices/refresh` y `/api/investments/refresh-prices`
  - `/api/investments/import/price-coverage/*`
  - `/api/ai/status`, `/api/ai/tools`, `/api/ai/conversations`
  - `/api/insights/*` (GET, monthly-review, anomalies, data-quality, refresh, dismiss)
  - `/api/settings` (GET, PATCH)
  - `/api/financial-knowledge/*` (snapshot, regime, signals, personal-impact, datasheet, recompute)
  El contrato declara `/api/ai/health` pero el código implementa `/api/ai/status`.
- **Acción:** Añadir secciones para: `Insights`, `Settings`, `Financial Knowledge`, completar `AI` con conversaciones y status/tools, y completar `Investments` con assets, operations y price coverage.

---

#### DOC-14: `docs/07_ECONOMIC_INTELLIGENCE.md` — Doc desactualizado, módulo migrado
- **Severidad:** MEDIO
- **Archivo:** `docs/07_ECONOMIC_INTELLIGENCE.md`
- **Descripción:** El documento reconoce que "la inteligencia económica ya no vive en un módulo independiente `economic_data`" y que ahora forma parte de `market_intelligence`. Sin embargo, describe un estado arquitectónico pasado sin describir el estado actual.
- **Acción:** Actualizar para describir el estado actual (qué quedó en `economic_data`, qué migró a `market_intelligence`) y añadir referencias cruzadas a `docs/15_MARKET_PROVIDERS.md`. Alternativamente, archivar en `docs/internal/`.

---

#### DOC-15: `docs/superpowers/` — Artefactos de proceso de IA en directorio de docs de producto
- **Severidad:** BAJO
- **Archivo:** `docs/superpowers/` (plans y specs)
- **Descripción:** Planes de implementación y specs generados durante el desarrollo con Claude Code. Su presencia bajo `docs/` viola la "Regla documental" del propio `02_ROADMAP.md` que establece que los planes y specs deben separarse de la documentación viva de producto.
- **Acción:** Mover `docs/superpowers/` a `.superpowers/docs/` o mantener en `.superpowers/sdd/`.

---

### Notas de Contexto Documentación

- **Docs de feature (20–25):** Los documentos `20_PORTFOLIO_IMPORT_ASSISTANT.md`, `21_GOALS_SIMULATIONS.md`, `22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`, `23_BUDGETS_RECURRING_CASHFLOW.md`, `24_DOCUMENT_INTELLIGENCE_RAG.md`, y `25_HARDENING_SECURITY_BACKUPS.md` son documentación de producto válida. No son documentos huérfanos.
- **Docs de producto core (00–07, 10–12, 15–16):** Válidos. Excepciones anotadas: `07` (DOC-14, desactualizado) y `13` (DOC-5, proceso interno).

---

## Plan de Acción Pre-Release

### Inmediato — Blockers (antes del tag 1.0)

| # | ID | Dominio | Hallazgo | Archivo/Ruta | Acción | Est. |
|---|-----|---------|----------|--------------|--------|------|
| 1 | DOC-0 | Documentación | README sin instrucciones de instalación para usuario final | `README.md` | Añadir sección "## Instalación (usuario final)" con pasos post-.msi, ubicación de datos, troubleshooting | 2h |
| 2 | SEC-1 | Seguridad | CSP nula en Tauri | `apps/desktop/src-tauri/tauri.conf.json:23` | Definir CSP restrictiva con `default-src 'self'`, `connect-src` a localhost:8000/11434/1234 | 30min |
| 3 | SEC-2 | Seguridad | Rutas absolutas del host expuestas en API de seguridad | `backend/app/modules/security/routes.py:21`, `service.py:39,52` | Reemplazar rutas absolutas por identificadores opacos o nombres de archivo en `SecurityStatusOut` y `BackupOut` | 30min |
| 4 | SEC-3 / HYG-3 | Seguridad / Higiene | `*.json` global en .gitignore bloquea nuevos JSON legítimos | `.gitignore:42` | Reemplazar línea `*.json` por reglas scoped a `graphify-out/` | 5min |
| 5 | HYG-1 | Higiene | `market-data-poc/` rastreado en git (99 archivos, PoC excluida de 1.0) | `market-data-poc/` | `git rm -r --cached market-data-poc/` + añadir a .gitignore | 5min |
| 6 | HYG-2 | Higiene | `graphify-out/` con archivos de control rastreados y `graph.html` sin ignore | `graphify-out/` | `git rm -r --cached graphify-out/` + añadir `graphify-out/` a .gitignore | 5min |
| 7 | BE-1 | Backend | Ghost modules con solo `__pycache__` sin fuente .py | `backend/app/modules/economic_data/`, `backend/app/modules/investments/market_data/` | `git rm -r` ambos directorios; verificar que `test_no_legacy_modules.py` sigue pasando | 5min |
| 8 | BE-2 | Backend | 13 archivos de test de `market_intelligence` fuera del ciclo pytest estándar | `backend/pyproject.toml:27`, `backend/tests/market_intelligence/` | Añadir `"tests"` a `testpaths` en `pyproject.toml` O mover tests a `backend/app/modules/market_intelligence/tests/` | 30min |
| 9 | BE-3 | Backend | 49 imports F401 no utilizados (11 en producción) | Múltiples módulos — ver listado en hallazgo | `uv run ruff check app/ --select F401 --fix` desde `backend/`; revisión manual de producción antes de commit | 30min |
| 10 | DOC-1 | Documentación | README sin referencia a `.env` / `.env.example` | `README.md` | Añadir sección "Configuración de entorno" referenciando `backend/.env.example` | 30min |
| 11 | DOC-2 | Documentación | README sin instrucciones de build de distribución | `README.md` | Añadir sección "## Build de distribución" con `npm run tauri build` y prerequisitos | 30min |
| 12 | DOC-3 | Documentación | Sin archivo LICENSE ni mención de licencia | `README.md` (raíz) | Añadir archivo `LICENSE` en raíz + sección "## Licencia" en README | 30min |

**Tiempo total estimado de blockers:** ~6.5 horas

---

### Post-Release 1.0 — Deuda Técnica

| # | ID | Dominio | Hallazgo | Acción |
|---|-----|---------|----------|--------|
| 1 | SEC-4 | Seguridad | `AI_ENABLE_TOOL_TRACE` habilitado por defecto en producción | Cambiar default a `False`; activar solo con `APP_ENV=development` |
| 2 | SEC-5 | Seguridad | MIME sniffing en endpoint `/api/rag/documents/upload` | Añadir validación de contenido real (UTF-8, no-null bytes, parse CSV/JSON) |
| 3 | SEC-6 | Seguridad | `.env.example` raíz y `backend/.env.example` desincronizados | Unificar y usar `backend/.env.example` como única fuente de verdad |
| 4 | SEC-7 | Seguridad | `shell:allow-open` sin restricción de esquema en Tauri | Restringir a esquemas `https`, `http`, `mailto` |
| 5 | FE-1 | Frontend | 5 directorios vacíos con solo `.gitkeep` | Eliminar o documentar en ARCHITECTURE.md con milestone target |
| 6 | FE-2 | Frontend | `lib/design-tokens.ts` — módulo completo sin importadores | Eliminar; paleta centralizada en `tailwind.config.ts` |
| 7 | FE-3 | Frontend | `lib/hooks/useFinancialKnowledge.ts` — cadena completa de código muerto | Mover a `_wip/` o eliminar si no hay página destino en roadmap inmediato |
| 8 | FE-4 | Frontend | `EmptyState.tsx` — wrapper redundante de `Dashboard.EmptyState` | Eliminar y migrar 3 importadores a `@/components/ui/Dashboard` |
| 9 | FE-5 | Frontend | `DataSourceBadge` y `MetricDelta` exportados sin consumidores externos | Quitar `export` de `MetricDelta`; evaluar eliminar `DataSourceBadge` |
| 10 | FE-6 | Frontend | `CoverageStatus` duplicado en dos archivos de tipos | Consolidar en `price-coverage.ts`; importar desde `portfolio-import.ts` |
| 11 | FE-7 | Frontend | `mock-data.ts` importado estáticamente en bundle de producción | Convertir a import dinámico dentro de bloque `if (USE_MOCK)` |
| 12 | FE-8 | Frontend | `PlanificacionPage.tsx` fuera del patrón `features/` | Mover a `features/planning/`; eliminar directorio `src/pages/` |
| 13 | BE-4 | Backend | `backend/app/infrastructure/` — directorio vacío sin propósito | `git rm -r backend/app/infrastructure/` |
| 14 | BE-5 | Backend | `ai/prompts/__init__.py` vacío sin re-exports | Añadir `from app.modules.ai.prompts.system_prompt import SYSTEM_PROMPT` |
| 15 | BE-6 | Backend | `backend/tests/market_intelligence/` sin `conftest.py` | Crear `conftest.py` con fixtures DuckDB in-memory |
| 16 | BE-7 | Backend | `cli.py` no documentado ni referenciado | Añadir entry point en `pyproject.toml` y documentar en README |
| 17 | BE-8 | Backend | Seeds en `lifespan()` de FastAPI en cada arranque | Mover a comando CLI con `AUTO_SEED=true` opcional |
| 18 | BE-9 | Backend | Endpoints `/ai-datasheet` y `/snapshot/news` sin consumidor frontend | Documentar en `docs/11_API_CONTRACT.md` como "reserved for CLI / future use" |
| 19 | HYG-4 | Higiene | `docs/superpowers/` (10 archivos de planes/specs) rastreados como docs de producto | Untrack + añadir a .gitignore, o mover a `docs/internal/` |
| 20 | HYG-5 | Higiene | Directorio duplicado `data/` en root con datos desactualizados | `git rm data/.gitkeep`; eliminar directorio físico `data/` |
| 21 | HYG-6 | Higiene | `ux-snapshots/` con metadatos rastreados | Opcional: `git rm -r --cached ux-snapshots/` + añadir a .gitignore |
| 22 | HYG-7 | Higiene | `.superpowers/` sin cobertura en root `.gitignore` | `echo ".superpowers/" >> .gitignore` |
| 23 | DOC-4 | Documentación | `02_ROADMAP.md` con Fase 6.4 marcada "En curso" | Actualizar tabla: Fase 6.4 → completada; mover secciones 6.x a "Historial" |
| 24 | DOC-5 | Documentación | `13_CLAUDE_CODE_GUIDE.md` — guía de proceso interno en docs/ | Mover a `docs/internal/` |
| 25 | DOC-6 | Documentación | `docs/Styles/` sin referencias activas desde código | Mover a `docs/internal/Styles/` |
| 26 | DOC-7 | Documentación | `docs/28_*` — informe de sprint Fase 10.5 | Mover a `docs/internal/` |
| 27 | DOC-8 | Documentación | `docs/29_*` — batería de pruebas Fase 10.5 | Mover a `docs/internal/` |
| 28 | DOC-9 | Documentación | `docs/31_*` — informe de cierre Fase 10.6 | Mover a `docs/internal/` |
| 29 | DOC-10 | Documentación | `docs/30_*` — plan de QA Fase 10.6 | Mover a `docs/internal/` |
| 30 | DOC-11 | Documentación | `docs/26_*` — mezcla spec/producto Fase 10.5 | Extraer info de feature a docs 20–25; mover resto a `docs/internal/` |
| 31 | DOC-12 | Documentación | `docs/27_*` — spec de UI Polish Fase 10.5 | Consolidar en `docs/Styles/DESIGN.md`; mover a `docs/internal/` |
| 32 | DOC-13 | Documentación | `docs/11_API_CONTRACT.md` incompleto | Añadir secciones para Insights, Settings, Financial Knowledge, AI conversations, Investments assets/operations |
| 33 | DOC-14 | Documentación | `docs/07_ECONOMIC_INTELLIGENCE.md` desactualizado | Actualizar para reflejar migración a `market_intelligence`; añadir cross-refs a `15_MARKET_PROVIDERS.md` |
| 34 | DOC-15 | Documentación | `docs/superpowers/` — artefactos de proceso en docs/ | Mover a `.superpowers/docs/` (viola regla documental del roadmap) |
