# 16 — Insights Engine

## Objetivo

Motor determinista de insights financieros que analiza datos personales reales y genera señales priorizadas, trazables y explicables.

## Arquitectura

```
Datos locales (SQLite + DuckDB)
  ↓
Servicios deterministas (rules/)
  ↓
Scoring y priorización (scoring.py)
  ↓
API /api/insights
  ↓
UI Insights (InsightsPage.tsx)
  ↓
IA local opcional (get_insights_summary tool)
```

## Módulo Backend

`backend/app/modules/insights/`

| Fichero | Responsabilidad |
|---------|----------------|
| `constants.py` | Umbrales y puntuaciones configurables |
| `schemas.py` | Pydantic models (InsightOut, MonthlyReviewOut, etc.) |
| `scoring.py` | Cálculo de prioridad, severidad, confianza |
| `service.py` | Orquestador principal — llama a todas las reglas |
| `repository.py` | Persistencia mínima de dismissals (JSON) |
| `routes.py` | Endpoints FastAPI |
| `rules/spending_rules.py` | Anomalías de gasto, comparativa mensual, tasa de ahorro |
| `rules/cashflow_rules.py` | Alerta de déficit de cashflow |
| `rules/net_worth_rules.py` | Variación de patrimonio |
| `rules/investment_rules.py` | Concentración de cartera, precios faltantes |
| `rules/goal_rules.py` | Progreso de objetivos |
| `rules/market_rules.py` | Contexto de mercado (índices) |
| `rules/macro_rules.py` | Contexto macro (inflación, tipos) |
| `rules/data_quality_rules.py` | Detección de datos incompletos |

## Tipos de Insights

| Tipo | Descripción |
|------|-------------|
| `spending_anomaly` | Categoría de gasto > 25% sobre media de 3 meses |
| `monthly_comparison` | Gasto/ahorro vs mes anterior |
| `savings_rate` | Tasa de ahorro del mes |
| `cashflow_alert` | Gastos > Ingresos |
| `net_worth_change` | Variación REAL de patrimonio entre los dos últimos snapshots mensuales (INS-4). Sin ≥2 snapshots no emite nada — el insight estático desapareció. |
| `investment_allocation` | Concentración o precios faltantes |
| `goal_progress` | Progreso vs ritmo esperado |
| `market_context` | Variaciones relevantes en índices |
| `macro_context` | Inflación o tipos elevados |
| `data_quality` | Datos incompletos o faltantes |

## Scoring

```
priority = severity_score * 0.35
         + impact_score * 0.35
         + confidence_score * 0.20
         + freshness_score * 0.10
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/insights` | Lista de insights con filtros |
| GET | `/api/insights/monthly-review` | Resumen mensual completo |
| GET | `/api/insights/anomalies` | Solo anomalías de gasto |
| GET | `/api/insights/data-quality` | Solo insights de calidad |
| POST | `/api/insights/refresh` | Recalcular insights |
| POST | `/api/insights/{id}/dismiss` | Descartar insight |
| POST | `/api/insights/{id}/restore` | Deshacer un descarte (undo, INS-7) |

## Integración con IA

Tool: `get_insights_summary`
- Llama al servicio determinista
- La IA puede explicar, pero no recalcular ni inventar insights
- System prompt actualizado para usar la tool cuando se pregunte por alertas o revisión mensual

Tool: `get_balance_sheet` (INS-8, solo lectura)
- Envuelve `net_worth.service.build_balance_sheet` (activos, pasivos, patrimonio)
- La IA **explica y contextualiza** las cifras, nunca las recalcula ni inventa; cita los mismos importes
- El botón "Preguntar a la IA" de cada señal abre el asistente con el insight como contexto

## Estados de datos

| Estado | Significado |
|--------|-------------|
| `complete` | Datos suficientes para la mayoría de insights |
| `partial` | Hay datos pero faltan fuentes o histórico |
| `insufficient` | Datos mínimos, sin histórico suficiente |
| `empty` | Sin datos relevantes |
| `error` | Error controlado |

Cuando `data_status` es `empty` (sin transacciones en el periodo), la respuesta
devuelve `insights: []` y el `summary` a cero, aunque las reglas de contexto
(macro/mercado/calidad) hubieran generado insights informativos. Badge y cuerpo
derivan siempre del mismo estado y no pueden contradecirse.

## Umbrales configurables

Ver `constants.py`. Ejemplo: `SPENDING_ANOMALY_MULTIPLIER = 1.25`

## Cómo probar

```bash
cd backend && uv run pytest app/tests/test_insights_api.py -v
cd apps/desktop && npx tsc --noEmit
```

## Caché (INS-3, D4)

Respuestas calculadas memoizadas en memoria de proceso (dict + timestamp) con TTL 1h,
clave por mes (`cache.py`). Invalidación desde un único punto: un listener `after_commit`
de SQLAlchemy limpia la caché ante **cualquier** escritura (transacciones, cuentas,
holdings, presupuestos, creación de snapshots…). Las lecturas no hacen commit, así que
no la tocan. `refresh` y `dismiss` invalidan además explícitamente.

## Patrimonio y cierre de mes (INS-4)

`net_worth_change` se calcula sobre `net_worth_snapshots`. Los snapshots se crean por el
**cierre de mes asistido** en Resumen (submódulo `net_worth`, endpoints `/api/net-worth/*`),
nunca de forma automática. Ver `11_API_CONTRACT.md`.

## Limitaciones actuales

- Rentabilidad real (nominal − IPC) y rentabilidad de intereses aún no están en el balance (INS-6)
- Market/macro insights dependen de que haya datos ingestados en DuckDB

## Próximos pasos

- Nuevos insights Lote 1/2 (INS-5/INS-6): budget_alert, recurring_creep, savings_rate_trend, real_return…
- Tests de frontend con Vitest/Testing Library
