# Pre-Release 1.0 Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Producir el informe `docs/PRE_RELEASE_AUDIT.md` con todos los hallazgos de seguridad, código muerto, higiene de repositorio y documentación previos al release 1.0.

**Architecture:** 5 tareas de análisis independientes (Tasks 1–5), cada una produce un bloque de hallazgos en Markdown. Task 6 consolida todos los bloques en el informe final. Las Tasks 1–5 pueden ejecutarse en paralelo; Task 6 depende de que todas ellas hayan finalizado.

**Tech Stack:** Python FastAPI, TypeScript/React, Tauri/Rust, SQLite, DuckDB, git, uv, npm.

## Global Constraints

- Repo root: `d:/FinancialAgent/AI-Financial-OS/` (en adelante `$ROOT`)
- NO modificar código en este plan — solo analizar y documentar hallazgos
- NO hacer commits — solo stage si el usuario lo aprueba explícitamente
- `market-data-poc/` está confirmado para exclusión del release
- `.env` con claves reales existe localmente, NO está en historial git (verificado)
- Severidades: CRÍTICO (bloquea release), ALTO (debe resolverse antes de release), MEDIO (deseable antes de release), BAJO (deuda técnica aceptada)

---

## Task 1: Análisis de Seguridad

**Files:**
- Read: `.gitignore`, `backend/.env.example`, `.env.example`
- Read: `apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/src-tauri/capabilities/default.json`
- Read: `backend/app/main.py`, `backend/app/core/config.py`
- Read: `backend/app/modules/` (todos los routers)
- Produce: bloque `## Seguridad` para Task 6

**Interfaces:**
- Produce: string Markdown con hallazgos de seguridad, clasificados por severidad, listo para pegar en `PRE_RELEASE_AUDIT.md`

- [ ] **Step 1: Escanear historial git completo buscando secretos**

```bash
# Buscar patrones de API keys, tokens y passwords en TODO el historial
git -C "$ROOT" log --all --full-history -p -- '*.env*' '*.json' '*.py' '*.ts' '*.toml' 2>/dev/null \
  | grep -iE "(api_key|apikey|secret|password|token|bearer|private_key)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}" \
  | head -50

# Buscar específicamente las claves del .env en historial
git -C "$ROOT" log --all -S "ALPHA_VANTAGE_API_KEY" --oneline 2>/dev/null
git -C "$ROOT" log --all -S "FINNHUB_API_KEY" --oneline 2>/dev/null
git -C "$ROOT" log --all -S "POLYGON_API_KEY" --oneline 2>/dev/null
git -C "$ROOT" log --all -S "FRED_API_KEY" --oneline 2>/dev/null
```

Resultado esperado: sin output (claves no en historial). Si hay output → hallazgo CRÍTICO.

- [ ] **Step 2: Validar que .env.example NO contiene claves reales**

```bash
# Leer ambos .env.example y verificar que los valores son placeholders
cat "$ROOT/.env.example"
cat "$ROOT/backend/.env.example"
```

Verificar que todos los valores de API keys sean `your_key_here`, `<TU_CLAVE>`, vacíos, o similares. Si contienen valores reales → hallazgo CRÍTICO.

- [ ] **Step 3: Validar .gitignore para rutas sensibles**

```bash
# Comprobar que estas rutas están gitignoreadas
git -C "$ROOT" check-ignore -v .env backend/.env market-data-poc/.env 2>/dev/null
git -C "$ROOT" check-ignore -v backend/data/ data/ 2>/dev/null

# Verificar el problema de *.json al final del .gitignore
cat "$ROOT/.gitignore"
# Comprobar si *.json ignoraría archivos JSON rastreados
git -C "$ROOT" check-ignore -v apps/desktop/package.json apps/desktop/tsconfig.json 2>/dev/null
```

Si `package.json` o `tsconfig.json` aparecen como ignorados → hallazgo ALTO (el `*.json` rompe tracking de nuevos JSON).

- [ ] **Step 4: Auditar configuración CORS del backend**

```bash
cat "$ROOT/backend/app/main.py"
```

Buscar `CORSMiddleware`. Verificar:
- `allow_origins` no es `["*"]` en producción, o si lo es que esté condicionado al entorno (`APP_ENV`)
- `allow_credentials=True` no se combina con `allow_origins=["*"]` (violación de seguridad OWASP)

- [ ] **Step 5: Auditar permisos Tauri**

```bash
cat "$ROOT/apps/desktop/src-tauri/tauri.conf.json"
cat "$ROOT/apps/desktop/src-tauri/capabilities/default.json"
```

Verificar:
- `allowlist` o `permissions` no otorgan acceso a `fs:read-all` o `shell:execute` sin restricciones
- `csp` (Content Security Policy) está definido y no es `null`
- `dangerousDisableAssetCspModification` no es `true`

- [ ] **Step 6: Auditar validación de inputs en endpoints críticos**

```bash
# Listar todos los archivos de routers
find "$ROOT/backend/app/modules" -name "router.py" -o -name "routes.py" | head -20
```

Leer los routers de `imports` y `documents` (manejo de archivos subidos). Verificar:
- Validación de extensión de archivo
- Límite de tamaño de archivo
- No hay path traversal (e.g., `open(filename)` sin sanitizar)

- [ ] **Step 7: Documentar hallazgos de seguridad**

Guardar los resultados en un archivo temporal:
```
$ROOT/.superpowers/sdd/audit-security.md
```

Formato de cada hallazgo:
```markdown
### SEC-N: [Título]
- **Severidad:** CRÍTICO / ALTO / MEDIO / BAJO
- **Archivo:** `ruta/al/archivo.py:línea`
- **Descripción:** Qué está mal
- **Acción:** Qué hacer para corregirlo
```

---

## Task 2: Código Muerto Frontend (TypeScript/React)

**Files:**
- Read: `apps/desktop/src/` (todos los archivos `.tsx`, `.ts`)
- Produce: bloque `## Código Muerto Frontend` para Task 6

**Interfaces:**
- Produce: string Markdown con hallazgos de dead code TypeScript, clasificados por severidad

- [ ] **Step 1: Detectar directorios con solo .gitkeep**

```bash
# Encontrar todos los .gitkeep y verificar si el directorio sigue vacío
find "$ROOT/apps/desktop/src" -name ".gitkeep" -exec sh -c 'dir=$(dirname "$1"); count=$(find "$dir" -not -name ".gitkeep" -type f | wc -l); echo "$count $dir"' _ {} \;
```

Si `count == 0` → el directorio sigue vacío. Listar para posible eliminación o confirmación de que son placeholders intencionales.

- [ ] **Step 2: Detectar componentes exportados sin importadores**

```bash
# Listar todos los exports del frontend
grep -rn "^export " "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts" | grep -v "node_modules" | grep -v "dist/"

# Para cada export, buscar si hay algún import que lo consuma
# Ejemplo para un componente concreto:
grep -rn "import.*Dashboard" "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts"
grep -rn "import.*EmptyState" "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts"
grep -rn "import.*MetricCard" "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts"
grep -rn "import.*Spinner" "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts"
grep -rn "import.*TypeBadge" "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts"
```

Cualquier export sin ningún import → hallazgo MEDIO (posible dead code).

- [ ] **Step 3: Verificar dist/ en git**

```bash
git -C "$ROOT" ls-files apps/desktop/dist/ 2>/dev/null
```

Si devuelve archivos → hallazgo ALTO (build output en git, debe gitignorarse).

- [ ] **Step 4: Auditar App.tsx y rutas para features sin página**

```bash
cat "$ROOT/apps/desktop/src/App.tsx"
```

Listar todas las rutas definidas. Verificar que cada ruta apunta a un componente de página que existe. Rutas comentadas o que apuntan a componentes no existentes → hallazgo MEDIO.

- [ ] **Step 5: Buscar TODOs y código comentado en frontend**

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|console\.log\|console\.error\|debugger" \
  "$ROOT/apps/desktop/src" --include="*.tsx" --include="*.ts" | grep -v "node_modules"
```

Listar todos. `console.log` en producción → hallazgo ALTO. TODOs → hallazgo MEDIO.

- [ ] **Step 6: Verificar tailwind.config.ts y postcss.config.js**

```bash
cat "$ROOT/apps/desktop/tailwind.config.ts"
cat "$ROOT/apps/desktop/postcss.config.js"
```

Verificar que el `content` glob de Tailwind cubre todos los directorios de componentes activos.

- [ ] **Step 7: Documentar hallazgos frontend**

Guardar en: `$ROOT/.superpowers/sdd/audit-frontend.md`

Mismo formato que Task 1 Step 7, prefijo `FE-N`.

---

## Task 3: Código Muerto Backend (Python)

**Files:**
- Read: `backend/app/` (todos los módulos Python)
- Read: `backend/pyproject.toml`
- Read: `backend/tests/market_intelligence/` (tests huérfanos)
- Produce: bloque `## Código Muerto Backend` para Task 6

**Interfaces:**
- Produce: string Markdown con hallazgos de dead code Python, clasificados por severidad

- [ ] **Step 1: Listar todos los módulos del backend**

```bash
find "$ROOT/backend/app" -name "*.py" | sort
find "$ROOT/backend/app/modules" -type d | sort
```

Mapear la estructura completa de módulos para el análisis subsiguiente.

- [ ] **Step 2: Detectar módulos con solo __init__.py vacío**

```bash
# Buscar __init__.py vacíos o con solo un comentario
find "$ROOT/backend/app" -name "__init__.py" -exec sh -c \
  'lines=$(grep -c "." "$1" 2>/dev/null || echo 0); [ "$lines" -le 2 ] && echo "$1 ($lines lines)"' _ {} \;
```

`backend/app/infrastructure/__init__.py` en particular. Si el módulo `infrastructure` solo tiene `__init__.py` vacío → hallazgo MEDIO (directorio vacío innecesario).

- [ ] **Step 3: Auditar tests huérfanos de market_intelligence**

```bash
ls "$ROOT/backend/tests/market_intelligence/"
# Verificar si estos tests importan desde market-data-poc o desde el backend
grep -rn "^from\|^import" "$ROOT/backend/tests/market_intelligence/" | head -30
```

Si importan desde `market-data-poc/` → hallazgo ALTO (tests que se romperán cuando se excluya el POC).
Si importan desde `backend/app/modules/market_intelligence/` → son tests del backend, no huérfanos.

- [ ] **Step 4: Auditar cli.py**

```bash
cat "$ROOT/backend/cli.py"
# Buscar referencias a cli.py en scripts y documentación
grep -rn "cli.py\|python cli" "$ROOT/scripts/" "$ROOT/docs/" "$ROOT/README.md" 2>/dev/null
```

Si no hay referencias → hallazgo BAJO (código no documentado ni accesible).

- [ ] **Step 5: Auditar seeds — ¿se ejecutan en producción?**

```bash
cat "$ROOT/backend/app/seeds/categories.py"
cat "$ROOT/backend/app/seeds/settings.py"
# Buscar dónde se llaman estos seeds
grep -rn "seeds\|seed_" "$ROOT/backend/app/" --include="*.py" | grep -v "seeds/"
```

Si los seeds se llaman en `startup` de producción → documentar si son idempotentes. Si solo son para dev → hallazgo BAJO (debería estar en un comando separado).

- [ ] **Step 6: Buscar imports no utilizados con ruff**

```bash
cd "$ROOT/backend"
# Usar ruff para detectar F401 (unused imports) en todo el módulo
uv run ruff check app/ --select F401 --output-format=text 2>/dev/null | head -50
```

Listar todos los F401. Más de 10 en módulos de producción → hallazgo MEDIO.

- [ ] **Step 7: Verificar endpoints sin consumidor frontend**

```bash
# Listar todos los endpoints del backend
grep -rn "@router\.\(get\|post\|put\|patch\|delete\)" "$ROOT/backend/app/modules/" --include="*.py" | head -60

# Buscar cuáles son referenciados desde el frontend
grep -rn "fetch\|axios\|api\." "$ROOT/apps/desktop/src" --include="*.ts" --include="*.tsx" | \
  grep -v "node_modules" | head -40
```

Endpoints de backend sin ningún consumidor en frontend → hallazgo BAJO (puede ser usado por CLI o futura feature).

- [ ] **Step 8: Documentar hallazgos backend**

Guardar en: `$ROOT/.superpowers/sdd/audit-backend.md`

Mismo formato, prefijo `BE-N`.

---

## Task 4: Higiene del Repositorio

**Files:**
- Read: `.gitignore`, `backend/pyproject.toml`
- Run: varios comandos git
- Produce: bloque `## Higiene del Repositorio` para Task 6

**Interfaces:**
- Produce: string Markdown con hallazgos de repo hygiene + comandos exactos de remediación

- [ ] **Step 1: Inventariar market-data-poc en git**

```bash
# Cuántos archivos de market-data-poc están rastreados
git -C "$ROOT" ls-files market-data-poc/ | wc -l

# ¿Hay dependencias desde backend hacia market-data-poc?
grep -rn "market.data.poc\|from market_data" "$ROOT/backend/app/" --include="*.py"
grep -rn "market.data.poc\|from market_data" "$ROOT/apps/desktop/src/" --include="*.ts" --include="*.tsx"
```

Si hay dependencias → hallazgo CRÍTICO (no se puede excluir sin romper el build).
Si no hay dependencias → documentar el comando de exclusión exacto:
```bash
# Comando para excluir market-data-poc del repo (NO ejecutar aún — para informe)
git rm -r --cached market-data-poc/
echo "market-data-poc/" >> .gitignore
```

- [ ] **Step 2: Auditar graphify-out en git**

```bash
git -C "$ROOT" ls-files graphify-out/ | wc -l
git -C "$ROOT" ls-files graphify-out/ | head -20
# Tamaño total de archivos rastreados de graphify-out
git -C "$ROOT" ls-files graphify-out/ -z | xargs -0 du -sh 2>/dev/null | tail -1
```

Los `cache/semantic/*.json` son cache semántico de embeddings — no deben estar en git.
Determinar qué archivos de `graphify-out/` son esenciales (`GRAPH_REPORT.md`, `.graphify_root`, `.graphify_python`, `.graphify_labels.json`) vs. cache eliminable.

- [ ] **Step 3: Auditar .superpowers/sdd en git**

```bash
git -C "$ROOT" ls-files .superpowers/ | wc -l
git -C "$ROOT" ls-files .superpowers/ | head -20
```

Los archivos `review-*.diff`, `task-*-brief.md`, `task-*-report.md` son artefactos del proceso de desarrollo AI-asistido. Determinar si deben estar en el release o moverse a `.gitignore`.

- [ ] **Step 4: Auditar docs/superpowers en git**

```bash
git -C "$ROOT" ls-files docs/superpowers/ | head -20
```

Los planes y specs son documentación del proceso de desarrollo. Evaluar si forman parte de la documentación del producto (y deben permanecer) o son artefactos internos (y deben excluirse o moverse a `docs/internal/`).

- [ ] **Step 5: Auditar ux-snapshots en git**

```bash
git -C "$ROOT" ls-files ux-snapshots/ | wc -l
# Tamaño total
git -C "$ROOT" ls-files ux-snapshots/ -z | xargs -0 du -ch 2>/dev/null | tail -1
```

80+ imágenes PNG en git incrementan el tamaño del repositorio significativamente. Evaluar si deben gitignorarse (se generan on-demand) o mantenerse para CI visual.

- [ ] **Step 6: Verificar problema *.json en .gitignore**

```bash
# ¿Qué archivos JSON NO rastreados actualmente serían afectados?
git -C "$ROOT" status --short | grep "\.json$"

# ¿Existe algún JSON sin trackear que debería estar en git?
git -C "$ROOT" ls-files --others --exclude-standard | grep "\.json$"

# ¿Los JSON ya rastreados siguen apareciendo en git ls-files?
git -C "$ROOT" ls-files | grep "\.json$" | head -10
```

La regla `*.json` en `.gitignore` NO afecta archivos ya rastreados, pero SÍ impide que nuevos JSON se añadan al repo. Si hay nuevos JSON que deberían estar rastreados → hallazgo ALTO.

- [ ] **Step 7: Auditar .ruff_cache y .pytest_cache en git**

```bash
git -C "$ROOT" ls-files backend/.ruff_cache/ backend/.pytest_cache/ 2>/dev/null
```

Si aparecen archivos → hallazgo ALTO (cache de herramientas en git). Añadir a `.gitignore` y `git rm --cached`.

- [ ] **Step 8: Auditar apps/desktop/dist en git**

```bash
git -C "$ROOT" ls-files apps/desktop/dist/ 2>/dev/null
```

Si hay archivos → hallazgo ALTO (build output en git).

- [ ] **Step 9: Verificar datos duplicados (root/data vs backend/data)**

```bash
ls -la "$ROOT/data/"
ls -la "$ROOT/backend/data/"
# ¿Qué rutas usa el backend realmente?
grep -n "DATABASE_URL\|DUCKDB_PATH" "$ROOT/backend/app/core/config.py"
```

Determinar cuál de los dos directorios es el que usa el backend activo, y si `data/` en root es una reliquia.

- [ ] **Step 10: Documentar hallazgos de higiene**

Guardar en: `$ROOT/.superpowers/sdd/audit-hygiene.md`

Para cada hallazgo de higiene que tenga remediación clara, incluir el comando exacto (git rm --cached, echo >> .gitignore, etc.).
Prefijo `HYG-N`.

---

## Task 5: Auditoría de Documentación

**Files:**
- Read: `docs/` (todos los archivos .md)
- Read: `README.md`
- Produce: bloque `## Documentación` para Task 6

**Interfaces:**
- Produce: string Markdown con hallazgos de documentación, clasificados por severidad

- [ ] **Step 1: Mapear docs a features del código**

```bash
ls "$ROOT/docs/"
```

Para cada doc numerada, verificar si el módulo de código correspondiente existe:
- `docs/20_PORTFOLIO_IMPORT_ASSISTANT.md` → `backend/app/modules/` tiene módulo de portfolio/imports?
- `docs/21_GOALS_SIMULATIONS.md` → módulo de goals?
- `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md` → módulo de reconciliation?
- `docs/23_BUDGETS_RECURRING_CASHFLOW.md` → módulo de planning/budgets?
- `docs/24_DOCUMENT_INTELLIGENCE_RAG.md` → módulo de RAG/documentos?

```bash
find "$ROOT/backend/app/modules" -type d | sort
```

Docs sin módulo correspondiente → hallazgo MEDIO (documentación huérfana).

- [ ] **Step 2: Auditar docs de fase (20–31) — ¿valor de producto o historial de sprint?**

Leer el primer párrafo de cada una:
```bash
for f in "$ROOT/docs/2"*.md "$ROOT/docs/3"*.md; do
  echo "=== $f ==="; head -5 "$f"; echo
done
```

Clasificar cada una como:
- **Documentación de feature** (explica qué hace, cómo usar) → mantener
- **Informe de sprint/proceso** (tareas completadas, decisiones tomadas) → mover a `docs/internal/` o eliminar del release

- [ ] **Step 3: Auditar docs/13_CLAUDE_CODE_GUIDE.md**

```bash
head -20 "$ROOT/docs/13_CLAUDE_CODE_GUIDE.md"
```

Si es una guía sobre cómo usar Claude Code para desarrollar el proyecto → es documentación de proceso interno, no de producto. Hallazgo BAJO (mover a `docs/internal/`).

- [ ] **Step 4: Auditar docs/Styles/**

```bash
cat "$ROOT/docs/Styles/DESIGN.md"
# ¿Es referenciado desde algún otro doc o componente?
grep -rn "Styles/DESIGN\|Styles/variables\|docs/Styles" "$ROOT/docs/" "$ROOT/apps/" 2>/dev/null
```

Si no hay referencias → hallazgo BAJO (artefacto suelto del proceso de diseño).

- [ ] **Step 5: Auditar API contract vs endpoints reales**

```bash
# Leer la sección de endpoints del API contract
head -100 "$ROOT/docs/11_API_CONTRACT.md"

# Listar los endpoints reales del backend
grep -rn "@router\.\(get\|post\|put\|patch\|delete\).*path=" "$ROOT/backend/app/modules/" --include="*.py" | head -40
# o
grep -rn "@app\.\(get\|post\|put\|patch\|delete\)\|@router\.\(get\|post\)" "$ROOT/backend/app/modules/" --include="*.py" | head -40
```

Endpoints en el contrato que no existen en el código → hallazgo MEDIO (doc desactualizada).
Endpoints en el código que no están en el contrato → hallazgo BAJO (doc incompleta).

- [ ] **Step 6: Auditar README.md para release readiness**

```bash
cat "$ROOT/README.md"
```

Verificar que el README incluye:
- [ ] Descripción del proyecto
- [ ] Requisitos de instalación (Node, Rust/Tauri, Python/uv)
- [ ] Instrucciones de configuración del `.env` (referencia a `.env.example`)
- [ ] Cómo arrancar en desarrollo
- [ ] Cómo hacer build para distribución
- [ ] Información de licencia

Cualquier sección faltante o desactualizada → hallazgo ALTO (README incompleto para release 1.0).

- [ ] **Step 7: Verificar docs/02_ROADMAP.md estado actual**

```bash
cat "$ROOT/docs/02_ROADMAP.md"
```

Verificar que el roadmap refleja el estado actual (fase 10.6 completada) y no tiene features marcadas como "pendientes" que ya están implementadas.

- [ ] **Step 8: Documentar hallazgos de documentación**

Guardar en: `$ROOT/.superpowers/sdd/audit-docs.md`

Prefijo `DOC-N`.

---

## Task 6: Consolidación del Informe PRE_RELEASE_AUDIT.md

**Files:**
- Read: `$ROOT/.superpowers/sdd/audit-security.md`
- Read: `$ROOT/.superpowers/sdd/audit-frontend.md`
- Read: `$ROOT/.superpowers/sdd/audit-backend.md`
- Read: `$ROOT/.superpowers/sdd/audit-hygiene.md`
- Read: `$ROOT/.superpowers/sdd/audit-docs.md`
- Create: `docs/PRE_RELEASE_AUDIT.md`

**Interfaces:**
- Consumes: los 5 archivos de hallazgos de Tasks 1–5
- Produces: `docs/PRE_RELEASE_AUDIT.md` — informe final completo

**Prerequisito:** Tasks 1–5 completadas.

- [ ] **Step 1: Leer todos los bloques de hallazgos**

```bash
cat "$ROOT/.superpowers/sdd/audit-security.md"
cat "$ROOT/.superpowers/sdd/audit-frontend.md"
cat "$ROOT/.superpowers/sdd/audit-backend.md"
cat "$ROOT/.superpowers/sdd/audit-hygiene.md"
cat "$ROOT/.superpowers/sdd/audit-docs.md"
```

- [ ] **Step 2: Crear PRE_RELEASE_AUDIT.md con estructura completa**

Crear `$ROOT/docs/PRE_RELEASE_AUDIT.md` con la siguiente estructura:

```markdown
# AI-Financial-OS — Pre-Release 1.0 Audit Report

**Fecha:** 2026-06-30  
**Rama:** fix/corrections-and-stabilization  
**Auditor:** Claude Code (análisis automatizado multi-agente)

---

## Resumen Ejecutivo

[N hallazgos totales: X críticos, Y altos, Z medios, W bajos]

### Blockers de Release (CRÍTICO + ALTO)
[Lista numerada de los ítems que DEBEN resolverse antes del tag 1.0]

### Deuda Técnica Aceptada (MEDIO + BAJO)
[Lista de ítems que pueden irse a post-release sin riesgo]

---

## Seguridad

[Pegar contenido de audit-security.md]

---

## Código Muerto — Frontend (TypeScript/React)

[Pegar contenido de audit-frontend.md]

---

## Código Muerto — Backend (Python)

[Pegar contenido de audit-backend.md]

---

## Higiene del Repositorio

[Pegar contenido de audit-hygiene.md]

### Comandos de Remediación

[Lista de comandos git exactos para ejecutar, en orden seguro]

---

## Documentación

[Pegar contenido de audit-docs.md]

---

## Plan de Acción Pre-Release

### Inmediato (antes del tag 1.0)
| # | Dominio | Acción | Archivo/Ruta | Tiempo Est. |
|---|---------|--------|--------------|-------------|
...

### Post-Release 1.0
| # | Dominio | Acción | Archivo/Ruta |
|---|---------|--------|--------------|
...
```

- [ ] **Step 3: Completar el Resumen Ejecutivo**

Contar hallazgos totales por severidad a partir de los 5 bloques. Identificar los blockers reales de release (CRÍTICO + ALTO). Escribir el resumen ejecutivo con números reales.

- [ ] **Step 4: Completar la tabla de Plan de Acción**

Para cada hallazgo CRÍTICO y ALTO, añadir una fila a la tabla "Inmediato" con la acción concreta y estimación de tiempo (5min / 30min / 2h).

Para hallazgos MEDIO y BAJO, añadir a la tabla "Post-Release".

- [ ] **Step 5: Verificar que el informe es autocontenido**

El informe debe ser legible sin los archivos temporales de `.superpowers/sdd/`. Verificar que no hay referencias a "ver archivo X" sin incluir el contenido relevante.

- [ ] **Step 6: Limpiar archivos temporales de análisis (opcional)**

```bash
# Los archivos temporales pueden eliminarse tras la consolidación
# (NO ejecutar hasta que el usuario apruebe el informe final)
# rm "$ROOT/.superpowers/sdd/audit-security.md"
# rm "$ROOT/.superpowers/sdd/audit-frontend.md"
# rm "$ROOT/.superpowers/sdd/audit-backend.md"
# rm "$ROOT/.superpowers/sdd/audit-hygiene.md"
# rm "$ROOT/.superpowers/sdd/audit-docs.md"
```

Dejar comentado — solo ejecutar tras aprobación del usuario.

- [ ] **Step 7: Stage del informe final (no commit)**

```bash
git -C "$ROOT" add docs/PRE_RELEASE_AUDIT.md
git -C "$ROOT" status
```

NO hacer commit. Mostrar el path del informe al usuario para su revisión.

---

## Self-Review del Plan

**Cobertura del spec:**
- ✅ Agente 1 Seguridad → Task 1 (git history, .env.example, .gitignore, CORS, Tauri, inputs)
- ✅ Agente 2 Frontend → Task 2 (componentes, exports, dist/, App.tsx, TODOs)
- ✅ Agente 3 Backend → Task 3 (módulos, tests huérfanos, cli.py, seeds, ruff, endpoints)
- ✅ Agente 4 Higiene → Task 4 (market-data-poc, graphify-out, .superpowers, ux-snapshots, *.json, data/)
- ✅ Agente 5 Docs → Task 5 (docs-to-code, fases, API contract, README, roadmap)
- ✅ Consolidación → Task 6 (informe final con severidades y plan de acción)

**Sin placeholders:** Todos los steps tienen comandos concretos con rutas reales.

**Dependencias:** Tasks 1–5 son independientes. Task 6 depende de todas ellas.
