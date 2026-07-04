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
| `net_worth_change` | Variación de patrimonio |
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

## Integración con IA

Tool: `get_insights_summary`
- Llama al servicio determinista
- La IA puede explicar, pero no recalcular ni inventar insights
- System prompt actualizado para usar la tool cuando se pregunte por alertas o revisión mensual

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

## Limitaciones actuales

- Net worth change requiere histórico de saldos que no se captura aún (devuelve `partial`)
- Market/macro insights dependen de que haya datos ingestados en DuckDB
- Dismissals persisten en JSON junto a la base de datos SQLite

## Próximos pasos

- Persistir snapshots de patrimonio para calcular cambio real mes a mes
- Caché de insights calculados con TTL de 1 hora
- Tests de frontend con Vitest/Testing Library
- UX snapshots automáticos
