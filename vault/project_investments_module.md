---
name: project_investments_module
description: Decisiones de diseño del rework del módulo de Inversiones (plan INV-1..INV-6)
metadata: 
  node_type: memory
  type: project
  originSessionId: 779dcbb8-1061-4909-a1a0-e28247cc9a25
---

Rework del módulo de Inversiones, plan de 6 sprints (INV-1..INV-6) sobre 3 tipos de activo: acciones, fondos, cuentas remuneradas.

**Estado (2026-07-05):** INV-1..INV-6 completos (código + tests escritos, NO ejecutados). El plan real está en `d:\AgentsTeamsRocket\# Plan de Mejora — Módulo de Inversiones.md`. Alineado a la spec §2-3 tras que el usuario lo pidiera. **Pendiente SOLO cierre**: ejecutar suite de tests (con permiso), `ux:snapshots:headed` (hubo cambios UI), commits (con confirmación).

**INV-6 (rediseño resumen):** (1) Cabecera desglose por tipo `PortfolioByTypeCards.tsx` (mercado/fondos/ahorro con valor+rentabilidad+badge de calidad: Mercado/Manual/Calculado + "N sin valorar"). (2) Gráfica agregada `PortfolioEvolutionChart.tsx` (AreaChart) sobre nuevo `GET /holdings/portfolio-evolution`: serie mensual sumada con forward-fill (fondos=snapshots, ahorro=motor, resto=HoldingValueHistory×qty o market_value), todo desde BD sin red. (3) Reconciliation: `_compute_quality_state` clasifica por `h.asset.asset_type` (OJO: HoldingOut.asset_type mapea savings_account→cash, hay que usar h.asset.asset_type) → fund=manual, savings_account=confirmed, antes que por frescura de precio.

**INV-5 (edición UX):** menú contextual unificado `PositionMenu.tsx` (dropdown `⋯`: Editar / Actualizar valor·Historial·Evolución / Fusionar duplicado / Eliminar) usado por HoldingRow y SavingsAccountCard. "Fusionar" solo aparece si el holding está en un grupo de duplicados (reusa mergeGroup). Savings tiene su propio `SavingsEditDialog.tsx` (edita rate_source/fixed_rate/opened_at vía nuevo `GET /savings/{account_id}` + PUT) porque HoldingEditor genérico no toca la config. Borrar cuenta remunerada borra config (deleteSavings) además del holding, si no la cuenta queda "ya configurada" (409 al re-dar-de-alta). update_savings sincroniza interest_rate/inception_date del holding. KPIs reactivos vía onRefreshAll en cada mutación.

**Modelo alineado a spec (usuario: tablas nuevas + alinear a spec exacta + aportaciones desde Transaction):**
- Fondos → `FundValuationSnapshot` (campos spec: `date`, `market_value`, `contributed_total`; único holding+date). Rutas `/api/investments/funds` (alta) y `/funds/{holding_id}/snapshots` + `/funds/snapshots/{id}`. Holding sync desde último snapshot.
- Cuentas remuneradas → `SavingsAccountConfig` keyed por **account_id** (spec), campos `opened_at`/`rate_source`(ecb_deposit_facility|fixed|manual)/`fixed_rate`/`spread_bps`. Rutas `/api/investments/savings` (alta), `/savings/{account_id}/projection`, PUT/DELETE `/savings/{account_id}`. Aportaciones = `Transaction` type=transfer sobre la Account.
- Acciones/ETF → `HoldingValueHistory` + yfinance (NO forkeado). `/performance` sin ticker cae a snapshots de fondo → luego history.
- Motor `savings_service.py`: compuesto mensual, tipo del **último día del mes**, modo inverso = retro-calcula saldo INICIAL (no rate) con probe grande para evitar redondeo; `estimated=true`.

**Tipo de referencia BCE:** histórico DFR cacheado en SQLite app (`ReferenceRateObservation`, keyed por rate_id+effective_date) vía `reference_rate_service` (ECB SDMX, fallback FRED CSV `ECBDFR`, sin API key). `get_rate_on(fecha)`. Endpoint interno `GET /api/market-intelligence/rates/ecb-deposit-facility`. (Spec decía reusar EconomicObservation pero no existe como tabla SQLite → se usa ReferenceRateObservation, aprobado por el usuario.)
- Migración `_migrate_investment_domain()` en database.py recrea las tablas nuevas si tienen esquema pre-spec (drop seguro, sin datos).

Restricciones: Decimal siempre; nada se crea sin confirmación; IA fuera del cálculo. Ver [[project_constraints]].

---
**Relacionadas:** [[project_constraints]] · [[project_economy_plan]] · [[project_reconciliation_design]]

Tags: #módulo #decisión
