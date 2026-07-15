# 21 — Goals & Simulations (Fase 8)

## Objetivo

Ayudar al usuario a proyectar el progreso hacia sus objetivos financieros mediante simulaciones deterministas con tres escenarios de crecimiento y ajuste por inflación.

## Modelo de simulación

### Escenarios

| Escenario | Crecimiento nominal anual | Color UI |
|---|---|---|
| Conservador | 2 % | Stone (#94a3b8) |
| Base | 6 % | Emerald (#10b981) |
| Optimista | 10 % | Amber (#f59e0b) |

Los escenarios representan rangos históricos aproximados: depósitos/cuentas (conservador), cartera diversificada (base), renta variable pura (optimista).

### Fórmula de acumulación

Con tipo mensual `rₘ = (1 + r_anual)^(1/12) − 1`:

```
S_k = S₀ · (1+rₘ)^k + C · [(1+rₘ)^k − 1] / rₘ    (rₘ > 0)
S_k = S₀ + C · k                                     (rₘ = 0)
```

Donde:
- `S₀` = saldo actual del objetivo
- `C` = aportación mensual
- `k` = mes de la proyección

### Ajuste por inflación

El objetivo ajustado por inflación indica cuánto será necesario en términos nominales futuros para mantener el poder adquisitivo equivalente al objetivo actual:

```
objetivo_ajustado = objetivo × (1 + inflación)^(meses_base / 12)
```

Inflación por defecto: 3 % anual (promedio histórico europeo). Configurable por el usuario mediante slider (0–10%).

### Horizonte del gráfico

- Mínimo 12 meses
- Máximo 120 meses (10 años, para legibilidad del gráfico)
- Horizonte efectivo: el primero en alcanzarse entre los tres escenarios

### Fecha proyectada

Para cada escenario, se calcula el primer mes `k` en que `S_k ≥ objetivo`. Si no se alcanza en el horizonte máximo (30 años por defecto), se marca como "No alcanzable".

### Cumplimiento de fecha objetivo

Si el usuario configuró una fecha objetivo, cada escenario indica si la meta se alcanza antes de esa fecha (`achievable_by_target_date`).

## Progreso (`/progress`)

El endpoint de progreso computa:
- `progress_pct`: `min(100, current / target × 100)`
- `remaining`: `max(0, target − current)`
- `on_track`: si el escenario base alcanza el objetivo antes de la fecha objetivo
- `base_projected_date`: fecha estimada en escenario base

## UI

Cada tarjeta de objetivo incluye un panel expandible "Proyección y escenarios" con:

1. **Slider de inflación** (0–10%) que relanza la simulación al soltarlo
2. **Nota de inflación**: objetivo ajustado en euros futuros
3. **3 tarjetas de escenario**: crecimiento, fecha estimada, en/fuera de plazo
4. **Gráfico de área** (recharts): tres curvas solapadas, línea de referencia en objetivo
5. **Aviso de aportación**: si no hay aportación mensual configurada

## API

```
POST /api/goals/{id}/simulate
  Body: { inflation_rate?: float, max_months?: int }
  Returns: SimulationResult

GET /api/goals/{id}/progress
  Returns: GoalProgressOut
```

### SimulationResult

```json
{
  "goal_id": "uuid",
  "current_amount": 2000.0,
  "target_amount": 10000.0,
  "monthly_contribution": 300.0,
  "inflation_rate": 0.03,
  "inflation_adjusted_target": 10927.0,
  "monthly_data": [
    { "month": 0, "label": "Jun 2026", "conservative": 2000, "base": 2000, "optimistic": 2000 },
    ...
  ],
  "scenarios": [
    {
      "scenario": "conservative",
      "label": "Conservador",
      "color": "#94a3b8",
      "annual_growth_rate": 0.02,
      "months_to_target": 28,
      "projected_date": "2028-10-01",
      "achievable_by_target_date": true,
      "final_amount": 10000.0
    },
    ...
  ],
  "target_date": "2029-01-01",
  "generated_at": "2026-06-29T..."
}
```

## Limitaciones conocidas

- Los escenarios son aproximaciones históricas, no garantías de rentabilidad
- No se tienen en cuenta impuestos sobre plusvalías ni comisiones de fondos
- La inflación se aplica de forma uniforme (sin inflación variable)
- No modela retiradas parciales ni cambios de aportación
- La simulación es estática (se recalcula cada vez, no persiste en BD)

## Archivos clave

| Archivo | Propósito |
|---|---|
| `backend/app/modules/goals/simulation_service.py` | Cálculo de escenarios, acumulación compound, ajuste inflación |
| `backend/app/modules/goals/routes.py` | Endpoints `/simulate` y `/progress` |
| `backend/app/modules/goals/schemas.py` | Schemas Pydantic de simulación |
| `apps/desktop/src/features/goals/components/GoalSimulationPanel.tsx` | Panel de proyección con gráfico |
| `apps/desktop/src/features/goals/GoalsPage.tsx` | Página de objetivos refactorizada |
| `apps/desktop/src/lib/api/goals.ts` | Tipos y llamadas API de simulación |
| `backend/app/tests/test_goals_simulation.py` | 22 tests unitarios + integración |
