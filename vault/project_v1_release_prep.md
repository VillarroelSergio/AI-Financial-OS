---
name: project-v1-release-prep
description: Prep de release v1.0 para GitHub (2026-07-14) — cambios sin commitear y pendientes
metadata: 
  node_type: memory
  type: project
  originSessionId: 45223307-6561-4cc4-808b-706798a24ebe
---

# Prep v1.0 para GitHub (2026-07-14)

Trabajo hecho en `AI-Financial-OS/` (rama `feature/preRelease`), **sin commitear** (a la espera de confirmación del usuario):

- Versión unificada a **1.0.0** en `backend/app/main.py` (FastAPI title + `/health`), `backend/pyproject.toml`, `apps/desktop/package.json`, `apps/desktop/src-tauri/tauri.conf.json`.
- **README.md reescrito** (detallado/conciso, ES): logo `apps/desktop/src-tauri/icons/source-icon.png` + 5 capturas mock en `docs/assets/` (overview, spending, investments, markets, economy).
- **Fix seguridad**: token de API con `hmac.compare_digest` (timing-safe) en `main.py`.
- **Docs obsoletas limpiadas**: refs `market-data-poc/` (03_ARCHITECTURE, 15_MARKET_PROVIDERS), roadmap MI→SQLite WAL, `.gitignore`.
- **`.env.example` consolidado** en la raíz (canónico, usado por `setup.ps1`); eliminado `backend/.env.example` duplicado/divergente.

**Auditoría seguridad (agente):** sin vulnerabilidades críticas/altas. Secretos `.env` NUNCA estuvieron en git (verificado historial). Pendientes menores: file read antes de check de tamaño (imports/rag, impacto local mínimo), `verify=False` en tesoro.py (deliberado/documentado).

**Why:** Dejar el proyecto listo para publicar v1.0.
**How to apply:** Pendiente del usuario → (1) confirmar commit, (2) **rotar las API keys reales** del `.env`/`backend/.env` (Alpha Vantage, Finnhub, FMP, TwelveData, FRED, Polygon, EIA, AEMET, OpenFIGI) por higiene; nunca commitear `.env`. Nota harness: GateGuard bloquea la 1ª edición de cada archivo y pasa al reintentar. Ver [[project_markets_module]], [[project_ai_module_plan]].


---
**Relacionadas:** [[project_constraints]] · [[project_economy_plan]] · [[project_investments_module]] · [[project_markets_module]]

Tags: #release #decisión
