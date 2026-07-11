# PLAN DE MEJORA — Módulo Insights + Balance General (v3)

**Fecha:** 2026-07-07
**Repositorio:** https://github.com/VillarroelSergio/AI-Financial-OS
**Base documental:** `16_INSIGHTS_ENGINE.md`, `04_DATA_MODEL.md`, `23_BUDGETS_RECURRING_CASHFLOW.md`, `03_ARCHITECTURE.md`, `12_DEVELOPMENT_WORKFLOW.md`, `27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`, `PRE_RELEASE_AUDIT.md`
**Evidencia:** 3 capturas de InsightsPage con datos reales del mes 2026-07

**Decisiones cerradas:**
- **D1:** Concentración medida sobre patrimonio total (incluir todos los activos), con copy correcto. Concentración de cartera de mercado como métrica complementaria.
- **D2:** Patrimonio con histórico (snapshots) + Balance General estilo empresa (activos, pasivos, patrimonio, rentabilidades).
- **D3:** Migrar dismissals de JSON a SQLite.
- **D4:** Incluir caché TTL 1h.
- **D5:** El Balance General se monta como sección en **Resumen/Overview**, no en Insights.
- **D6:** Pasivos con campo explícito `is_liability` en `Account`.
- **D7:** Snapshots **mensuales** creados mediante un **cierre de mes asistido**: la app pide al usuario actualizar la información necesaria con una checklist de partes pendientes antes de crear el snapshot.
- Ampliación con nuevos tipos de insight (dos lotes).

---

## 1. Diagnóstico — Catálogo de defectos observados

### Defectos de cálculo y contrato (backend)

| ID | Defecto | Evidencia | Causa raíz probable |
|---|---|---|---|
| INS-B1 | **Redondeo inconsistente entre reglas.** Resumen mensual: tasa de ahorro **61.6%**. Tarjeta "Tasa de ahorro mensual": **61.7%**. Cifra real: 2413,75 / 3915,00 = 61,65%. | Captura 1 vs 2 | `monthly_review` y la regla `savings_rate` redondean por separado. Viola el principio de cálculo determinista único. |
| INS-B2 | **Incremento inconsistente en la misma tarjeta.** Texto: "un 91% más". Métrica: "91.1%". | Captura 1 | Copy y métrica se formatean en dos puntos distintos del pipeline. |
| INS-B3 | **Insight duplicado literal.** "Posiciones sin precio actualizado" aparece dos veces: lista principal (`investment_rules`) y sección Calidad de datos (`data_quality_rules`). | Captura 3 | Dos reglas emiten la misma señal sin clave canónica de deduplicación. |
| INS-B4 | **Semántica incorrecta de concentración.** "Cuenta Remunerada Trade Republic representa el 100% de tu cartera": el copy dice "cartera" pero el cálculo mezcla tipos de activo. | Captura 2 | La regla no declara sobre qué universo mide. **Resolución (D1):** concentración de patrimonio total con copy correcto. |
| INS-B5 | **"Patrimonio neto actual" emitido como insight estático.** Sin variación ni umbral. | Captura 2 | No existe histórico de saldos. **Resolución (D2/D7):** snapshots mensuales con cierre asistido. |
| INS-B6 | **Redundancia Resumen ↔ tarjeta.** "Tasa de ahorro mensual" repite los 4 KPIs del bloque Resumen mensual. | Capturas 1-2 | No hay regla de supresión cruzada. |

### Defectos de formato e interacción (frontend)

| ID | Defecto | Evidencia |
|---|---|---|
| INS-F1 | **Locale inconsistente.** "61.6%" (punto) vs "61,6 %" (coma); "2414 €" vs "2413,75 €" vs "42.100 €" vs "1540 €". | Capturas 1-2 |
| INS-F2 | **Badges de conteo no interactivos** que duplican la dimensión de los dropdowns de filtro. | Captura 1 |
| INS-F3 | **Densidad muy baja:** ~300px por tarjeta para un único número; jerarquía plana entre severidades. | Todas |
| INS-F4 | **CTAs genéricos repetidos** ("Ver gastos" ×2, "Ver inversiones" ×3). | Capturas 2-3 |
| INS-F5 | **Banner de calidad genérico** sin identificar fuentes ni periodos. | Captura 1 |

---

## 2. Causas raíz consolidadas

1. **No existe taxonomía de clases de insight** (señal / contexto / calidad de datos) en el contrato ni en la UI.
2. **Formateo numérico en múltiples puntos** sin contrato de valor estructurado ni formatter es-ES único.
3. **Reglas independientes sin deduplicación ni supresión cruzada.**
4. **No hay histórico de patrimonio**, por lo que las reglas de patrimonio degeneran en hechos estáticos.
5. **El scoring de prioridad existe pero es invisible** en el orden y peso visual de las tarjetas.
6. **Insights desconectado de módulos que ya generan señales naturales:** presupuestos (`alert_threshold_pct` ya modelado), recurrentes, cashflow forecast y `household_bills` (que detecta subidas anómalas internamente sin exponerlas).

---

## 3. Arquitectura de información propuesta

### Taxonomía de tres clases (campo nuevo `insight_class`)

| Clase | Contenido | Tratamiento UI |
|---|---|---|
| `signal` | Señales accionables con umbral o variación: anomalías, alertas de presupuesto, cashflow, tendencias, desviación de objetivos, variación real de patrimonio | Tarjeta completa, orden por `priority`, severidad visible |
| `context` | Observaciones sin acción inmediata: tasa de ahorro (ya en el review), contexto macro/mercado, composición de patrimonio | Fila compacta (~48px), sección colapsable "Contexto del mes" |
| `data_quality` | Datos incompletos, precios sin actualizar, periodos faltantes | Bloque único al pie, específico por fuente/periodo, con CTA de resolución |

### Página Insights (de arriba abajo)

```txt
1. PageHeader Mercury + selector de mes + Actualizar
2. Resumen mensual (hero) — se mantiene
3. Señales (signal) — orden por priority, severidad en borde/badge
4. Contexto del mes (context) — filas compactas con expansión
5. Calidad de datos (data_quality) — bloque único, específico, con CTA
```

### Página Resumen/Overview — nueva sección Balance General (D5)

```txt
BALANCE GENERAL (panel colapsable, patrón mercury-panel)
  ACTIVOS por clase: liquidez, cuentas remuneradas, cartera de mercado, fondos, otros
  PASIVOS: cuentas con is_liability (hipoteca, préstamos, deudas)
  PATRIMONIO NETO + variación vs snapshot del mes anterior
  RENTABILIDADES: cartera de mercado, intereses de cuentas remuneradas,
                  rentabilidad real (nominal − IPC vigente)
  Gráfico de evolución de patrimonio (Recharts, serie de snapshots mensuales)
  Estado del mes: "Cerrado" | "Pendiente de cierre" + acceso al cierre asistido
```

### Cierre de mes asistido (D7)

Flujo — coherente con el principio del proyecto de confirmación explícita antes de persistir:

```txt
Trigger: últimos 3 días del mes, o cualquier día del mes siguiente
         si el snapshot del mes anterior no existe
 → Banner en Resumen: "Cierre de junio pendiente — 2 de 5 elementos actualizados"
 → Panel checklist (GET /api/net-worth/snapshot-readiness):
     [ok]    Movimientos del mes           (última transacción/import dentro del mes)
     [stale] Saldos de cuentas             (Account.updated_at < inicio de mes)  → CTA Cuentas
     [stale] Valoración de fondos          (valuation_date < mes)                → CTA Inversiones
     [ok]    Precios de posiciones cotizadas (sin posiciones NO_PRICE)
     [ok]    Facturas del hogar del periodo (si hay recurrentes esperadas)
 → Usuario completa pendientes (cada CTA navega a la pantalla correspondiente)
 → Botón "Cerrar mes y crear snapshot" (habilitado con todo ok)
   o "Cerrar como parcial" (siempre disponible; snapshot con data_state=partial
   y detalle de qué faltaba, visible después en Calidad de datos)
 → POST /api/net-worth/snapshots {month, force_partial?}
 → Snapshot idempotente por mes (DELETE+INSERT)
```

Reglas:
- **Nunca snapshot automático silencioso.** El recordatorio es proactivo; la persistencia es explícita.
- La checklist es **derivada** (frescura calculada de datos existentes), no una lista mantenida a mano.
- Un mes cerrado como parcial puede recerrarse: el nuevo snapshot reemplaza al parcial.

### Reglas de renderizado en Insights

- Badges de conteo → **chips-filtro clicables** (sustituyen al dropdown de severidad); quedan chips de severidad + dropdown de área.
- Tarjeta `signal`: título, frase con las **mismas cifras** que las métricas, métrica principal, comparativa inline, CTA específico ("Ver gastos de Salud"), disclosure "Datos utilizados".
- Dismiss con confirmación + undo, persistido en SQLite (D3).

---

## 4. Cambios de contrato, modelo y persistencia

### `InsightOut` (schemas.py)

```txt
insight_class: "signal" | "context" | "data_quality"      # nuevo
dedupe_key: str                                            # nuevo
metrics: [ { label, value: Decimal-as-string, unit: "EUR"|"%"|"count"|"months", precision } ]
cta: { label, route, params } | null
data_state: complete|partial|insufficient|empty|error      # existente
```

Principios:
- **El backend nunca formatea números en el copy**: frases con placeholders resueltos por el frontend con las mismas `metrics`. Corrige INS-B1/B2/F1 por construcción.
- **Importes como string decimal** (regla del proyecto: nunca float en lógica financiera).
- **Deduplicación en `service.py`** por `dedupe_key`, conservando la instancia de mayor prioridad.
- **Supresión cruzada** declarativa (`suppressed_by_review`).

### Modelo `Account` (D6)

```txt
is_liability: bool, default false    # nuevo campo explícito
```

- Migración: `mortgage` → `is_liability=true` por defecto; resto `false`; editable en UI de Cuentas.
- Un saldo negativo transitorio (descubierto) NO reclasifica la cuenta.
- Actualizar `04_DATA_MODEL.md`.

### Nuevas tablas SQLite

```txt
net_worth_snapshots                        # D2/D7
  id, month (YYYY-MM), snapshot_date, total_assets, total_liabilities,
  net_worth, breakdown_json (por clase de activo), data_state (complete|partial),
  missing_items_json, currency, created_at

insight_dismissals                          # D3 (migra el JSON actual)
  id, dedupe_key, month, dismissed_at, created_at
```

Migración de dismissals con script one-shot reversible.

### Caché TTL (D4)

- Respuesta calculada de `/api/insights` y `/api/insights/monthly-review`, TTL 1h, clave por mes.
- Invalidación explícita en: refresh, dismiss, confirmación de importación, CRUD de transacciones/holdings/presupuestos/cuentas, creación de snapshot.
- En memoria de proceso (dict + timestamp). Documentar en `16_INSIGHTS_ENGINE.md`.

### Nuevo submódulo: `net_worth` (balance + snapshots + readiness)

Ubicación propuesta: `backend/app/modules/insights/net_worth/` (o módulo hermano `net_worth/` si crece — Claude Code decide según el árbol real; el plan asume submódulo de insights porque comparte scoring y data_state).

Servicios deterministas, sin IA:
- **Balance:** activos = `Account.current_balance` por tipo (excluyendo `is_liability`) + `Holding.market_value` (reutiliza servicios de inversiones, no duplica cálculo). Pasivos = cuentas `is_liability`. Rentabilidades: cartera (servicio INV), intereses de remuneradas (calculadora determinista del plan INV), rentabilidad real = nominal − IPC leído de `mi_*`.
- **Readiness:** evalúa frescura por fuente y devuelve la checklist derivada (§3).
- **Snapshots:** creación idempotente por mes, solo vía endpoint explícito.

Endpoints:

```txt
GET  /api/net-worth/balance-sheet?month=YYYY-MM
GET  /api/net-worth/snapshots?from=&to=
GET  /api/net-worth/snapshot-readiness?month=YYYY-MM
POST /api/net-worth/snapshots            {month, force_partial: bool}
```

Actualizar `11_API_CONTRACT.md` con `/api/net-worth/*` y `/api/insights/*` completos (cierra parcialmente DOC-13 de la auditoría).

---

## 5. Nuevos tipos de insight

Todos deterministas, sobre datos ya existentes. Ninguno requiere ingesta nueva ni IA.

### Lote 1 — Planificación (datos de `budgets`, `recurring`, `cashflow`, `household_bills`)

| Tipo | Clase | Regla | Fuente |
|---|---|---|---|
| `budget_alert` | signal | Consumo ≥ `alert_threshold_pct` (campo ya modelado). Atención ≥ umbral; alta ≥ 100%. | `GET /api/budgets/comparison` (existente) |
| `upcoming_cashflow` | signal | Cargos recurrentes de próximos 15 días superan liquidez disponible, o acumulación inusual de vencimientos. | recurring + cashflow forecast (existentes) |
| `recurring_creep` | signal | Suma mensual de recurrentes de gasto crece ≥ X% vs hace 3 meses. | `recurring_transactions` |
| `household_bill_anomaly` | signal | Exponer como insight las subidas anómalas que `household_bills` ya detecta. | `household_bills` (existente) |
| `snapshot_pending` | data_quality | Cierre de mes anterior no realizado o realizado como parcial (con detalle de faltantes). | readiness service (nuevo) |

### Lote 2 — Tendencias y patrimonio (requiere snapshots)

| Tipo | Clase | Regla | Fuente |
|---|---|---|---|
| `savings_rate_trend` | signal/context | Tendencia de tasa de ahorro a 3-6 meses (mejora/deterioro sostenido). | transactions |
| `category_trend` | signal | Categoría con crecimiento sostenido ≥ N meses consecutivos (distinto de la anomalía puntual). | transactions |
| `emergency_fund_coverage` | signal/context | Liquidez / gasto medio mensual (3m) = meses de colchón. Señal si < umbral (p.ej. 3 meses). Cruza con objetivo `emergency_fund` si existe. | accounts + transactions + goals |
| `net_worth_change` (real) | signal | Variación real mes a mes desde snapshots. Sustituye al insight estático actual. | `net_worth_snapshots` |
| `wealth_concentration` | context/signal | **D1:** concentración sobre patrimonio total. Copy: "El 100% de tu patrimonio está en Cuenta Remunerada Trade Republic". | balance service |
| `portfolio_concentration` | signal | Concentración dentro de la cartera de mercado, solo con ≥2 posiciones cotizadas. | balance service |
| `real_return` | context | Rentabilidad nominal de remuneradas vs IPC → rentabilidad real. | INV (intereses) + `mi_*` (IPC, solo lectura) |

### Fuera de alcance (futuro documentado)

- `personal_inflation` (cesta IPC por subgrupos × gasto real): depende del plan de Economía, post-ECO-1. No incluir aquí (disciplina de superficie de contaminación).
- Umbrales de todos los tipos nuevos → `constants.py`, configurables.

---

## 6. Sprints

Secuencia estricta: integridad → modelo y persistencia → balance y cierre → nuevas reglas → UI.

### INS-0 — Base de tests y fixtures (0,5–1 día)
- Verificar inclusión de `test_insights_api.py` en `testpaths` (lección ECO-0).
- Fixtures deterministas con las cifras de las capturas (3915,00 / 1501,25 / 2413,75) como regresión de redondeo.
- Tests en rojo documentado: consistencia review↔regla (INS-B1); cero duplicados por `dedupe_key` (INS-B3).
- **DoD:** suite corre; regresiones escritas.

### INS-1 — Integridad de cálculo y formato (1–2 días)
- Redondeo único central con `Decimal` + `ROUND_HALF_UP`, consumido por todas las reglas y el review.
- Contrato `metrics`; eliminar cifras hardcodeadas en copy de reglas.
- Formatter único es-ES en `lib/formatters/`; migrar todo el formateo de InsightsPage.
- **DoD:** una sola cifra de tasa de ahorro en toda la pantalla; formato es-ES uniforme; tests de INS-0 en verde.

### INS-2 — Taxonomía, deduplicación y concentración D1 (1–2 días)
- `insight_class` + `dedupe_key` en schema y reglas; deduplicación y supresión cruzada en `service.py`.
- `wealth_concentration` + `portfolio_concentration` con copy honesto por universo.
- `savings_rate` reclasificada a `context`.
- **DoD:** respuesta sin duplicados; copy de concentración correcto.

### INS-3 — Modelo y persistencia (1,5–2 días)
- Campo `is_liability` en `Account` + migración (`mortgage` → true) + edición en UI de Cuentas (D6).
- Tabla `net_worth_snapshots` + tabla `insight_dismissals` (migración JSON reversible).
- Caché TTL 1h con invalidación explícita.
- **DoD:** dos meses de snapshots simulados producen variación correcta en tests; dismiss sobrevive reinicio; caché invalida en todos los eventos; `04_DATA_MODEL.md` actualizado.

### INS-4 — Balance General + cierre de mes asistido (2,5–3,5 días)
- Submódulo `net_worth`: servicios balance / readiness / snapshots + 4 endpoints.
- **UI en Resumen/Overview (D5):** panel Balance General colapsable + gráfico de evolución + estado del mes.
- **Cierre asistido (D7):** banner de recordatorio, panel checklist con estados ok/stale/missing y CTAs por pantalla, cierre completo o parcial con confirmación explícita.
- `net_worth_change` real en Insights; el insight estático desaparece.
- Actualizar `11_API_CONTRACT.md` y `16_INSIGHTS_ENGINE.md`.
- **DoD:** invariante activos − pasivos = patrimonio con test; checklist derivada correcta en fixtures con datos frescos/stale; snapshot parcial registra faltantes; ningún snapshot se crea sin acción del usuario.

### INS-5 — Nuevos insights, Lote 1: Planificación (1,5–2 días)
- `rules/budget_rules.py`, `rules/planning_rules.py` (upcoming_cashflow, recurring_creep), `household_bill_anomaly`, `snapshot_pending`.
- Umbrales en `constants.py`; tests por regla.
- **DoD:** cada regla con test dispara/no-dispara y `dedupe_key` propio.

### INS-6 — Nuevos insights, Lote 2: Tendencias y patrimonio (1,5–2 días)
- `savings_rate_trend`, `category_trend`, `emergency_fund_coverage`, `real_return`.
- Depende de INS-3/INS-4.
- **DoD:** tests de tendencia con series sintéticas de 6 meses; `emergency_fund_coverage` cruza con Goal si existe.

### INS-7 — Rediseño UI de Insights (2–3 días)
- Jerarquía de 5 niveles (§3) con primitivas Mercury.
- Chips de severidad clicables con conteos vivos; tarjetas signal compactas; filas context; bloque data_quality específico con CTA; banner genérico eliminado.
- Dismiss con undo; estados loading/empty/partial/error; snapshots UX regenerados (Insights + Resumen, desktop/tablet/mobile).
- **DoD:** la página con ~12 insights cabe en ~2 pantallas; jerarquía severidad-primero verificable en snapshot.

### INS-8 — IA contextual (opcional, 0,5–1 día)
- Botón "Explicar" por señal → panel lateral con `get_insights_summary` + contexto del insight (patrón `contextualCopilot.ts`).
- Nueva tool de solo lectura `get_balance_sheet` para que la IA explique el balance (guardrails de `06_AI_STRATEGY.md`: explica, nunca recalcula; cita las mismas `metrics`).

**Estimación total: 13–19 días efectivos.** INS-5 puede ir en paralelo a INS-4; INS-8 en paralelo a INS-7.

---

## 7. Verificaciones previas para Claude Code

Antes de INS-0, contra el repositorio real:
1. Confirmar árbol de `backend/app/modules/insights/` y si `test_insights_api.py` corre en `pytest` (testpaths).
2. Confirmar que `Account` no tiene ya campo equivalente a `is_liability` y el mecanismo de migraciones vigente.
3. Confirmar dónde calcula hoy Overview el `net_worth` de `GET /api/dashboard/overview` para reutilizar (no duplicar) esa agregación en el servicio de balance.
4. Confirmar formato actual del JSON de dismissals para el script de migración.

## 8. Qué NO toca este plan

- La lógica de valoración de inversiones (pertenece a INV; este plan la **consume** para el balance).
- El pipeline de ingestión macro (pertenece a ECO; `real_return` solo **lee** IPC de `mi_*`).
- `personal_inflation` (bloqueado hasta post-ECO-1).
- El LLM en cualquier punto del cálculo o del cierre de mes (guardrail permanente).