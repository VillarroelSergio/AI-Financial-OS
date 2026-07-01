# Pre-Release 1.0 Audit — Design Spec

**Date:** 2026-06-30  
**Status:** Approved  
**Branch:** fix/corrections-and-stabilization

---

## Objetivo

Análisis exhaustivo previo al release 1.0 de AI-Financial-OS. Detectar y producir un informe accionable de: secretos/seguridad, código muerto, artefactos de desarrollo en git, y documentación sobrante o desactualizada.

## Contexto

- Stack: Tauri + React/TypeScript + FastAPI Python + SQLite + DuckDB
- 581 archivos rastreados en git
- `market-data-poc/` confirmado para **excluir** del release 1.0
- Hay cambios staged (AI providers + roadmap) pendientes de commit
- `.env` con claves API reales existe localmente pero NO está en historial git

## Arquitectura del Análisis

5 agentes independientes ejecutados en paralelo. Cada uno produce un bloque de hallazgos clasificados por severidad. El resultado se consolida en `docs/PRE_RELEASE_AUDIT.md`.

---

## Agente 1 — Seguridad

**Alcance:**
- Escaneo del historial git completo buscando secretos commiteados (API keys, tokens, passwords, JWTs)
- Validación de `.gitignore`: todas las rutas con datos sensibles están ignoradas
- Revisión del `.env.example` (root y `backend/`) — no debe contener claves reales
- Backend Python OWASP: CORS config, autenticación/autorización, validación de inputs en endpoints, path traversal en manejo de archivos subidos, SQL injection en queries manuales
- Permisos Tauri: `tauri.conf.json` y `apps/desktop/src-tauri/capabilities/default.json`
- `.gitignore` issue: la línea `*.json` al final — ¿gitignora nuevos JSON no rastreados?

**Salida esperada:** Lista de hallazgos críticos/altos con archivo y línea.

---

## Agente 2 — Código Muerto Frontend (TypeScript/React)

**Alcance:**
- `apps/desktop/src/` — componentes definidos pero no importados en ningún archivo
- Exports sin consumidores dentro del proyecto
- Tipos/interfaces declarados pero no usados
- Directorios con solo `.gitkeep` (¿siguen vacíos? ¿deben mantenerse?)
- `apps/desktop/dist/` — build output en disco, verificar si está en git o solo en disco
- `apps/desktop/src/App.tsx` y `main.tsx` — revisión de imports iniciales

**Salida esperada:** Lista de archivos/símbolos eliminables con justificación.

---

## Agente 3 — Código Muerto Backend (Python)

**Alcance:**
- `backend/app/` — módulos, clases, funciones no referenciadas en ningún import
- Endpoints FastAPI registrados en routers pero sin consumidor en el frontend
- Imports no utilizados en todos los módulos (`backend/app/core/`, `models/`, `modules/`)
- `backend/app/infrastructure/` — directorio con solo `__init__.py`, ¿tiene propósito?
- `backend/cli.py` — ¿se usa en scripts de dev/producción? ¿está documentado?
- `backend/app/seeds/` — ¿se ejecutan en producción o solo en dev?
- `market-data-poc/` backend tests referenciados desde `backend/tests/market_intelligence/` — estos tests quedan huérfanos cuando se excluya el POC

**Salida esperada:** Lista de módulos/funciones eliminables y endpoints sin uso.

---

## Agente 4 — Higiene del Repositorio

**Alcance:**
- **`market-data-poc/`**: plan exacto para excluir del repo (git rm --cached, .gitignore entry, verificar que no haya dependencias desde backend)
- **`graphify-out/`**: 80+ archivos de caché semántico JSON y chunk files en git — añadir a .gitignore, mantener solo `GRAPH_REPORT.md` y archivos de configuración esenciales
- **`.superpowers/sdd/`**: diffs y task reports de proceso de desarrollo (review-*.diff, task-*.md) — ¿deben estar en git en el release?
- **`docs/superpowers/plans/` y `specs/`**: artefactos del proceso AI-dev — ¿van en release o son internos?
- **`*.json` en `.gitignore`**: verificar impacto real — ¿qué JSON files no rastreados existen que deberían o no rastrearse?
- **`backend/.ruff_cache/`** y **`.pytest_cache/`**: verificar si están en git
- **`ux-snapshots/latest/`**: 80+ imágenes PNG en git (~varios MB) — ¿necesarias en el repo de release?
- **`backend/data/backups/`**: 9 archivos .db de backup en disco — gitignoreados, confirmar
- **`data/` root**: base de datos duplicada respecto a `backend/data/` — confirmar qué se usa

**Salida esperada:** Lista de entradas a añadir a `.gitignore`, archivos a `git rm --cached`, y decisiones de estructura.

---

## Agente 5 — Documentación

**Alcance:**
- **Docs de fases (20–31)**: son informes de proceso/sprint, no documentación de producto — evaluar cuáles tienen valor para usuarios/colaboradores vs. cuáles son solo historial de desarrollo
- **Docs core (00–16)**: verificar que reflejan el estado actual del código (especialmente `03_ARCHITECTURE.md`, `04_DATA_MODEL.md`, `11_API_CONTRACT.md`)
- **`README.md`**: ¿está actualizado para release 1.0? ¿incluye instrucciones de instalación, configuración del `.env`, arranque?
- **`docs/13_CLAUDE_CODE_GUIDE.md`**: es documentación de proceso AI-dev, no de producto
- **`docs/Styles/`**: `DESIGN.md` y `variables.css` — ¿referenciados desde algún lugar o artefactos sueltos?
- Gaps: features implementadas sin documentación (planificación/cashflow introducido en fase 8.6)

**Salida esperada:** Lista de docs a eliminar, actualizar, o mover a carpeta `docs/internal/`.

---

## Output Final

Consolidación en **`docs/PRE_RELEASE_AUDIT.md`** con estructura:

```
## Resumen Ejecutivo
## Severidad CRÍTICA
## Severidad ALTA  
## Severidad MEDIA
## Severidad BAJA
## Acciones Inmediatas (pre-release blockers)
## Deuda Técnica Aceptada (post-release)
```

Cada hallazgo incluye: dominio, descripción, archivo/ruta afectada, y acción concreta recomendada.
