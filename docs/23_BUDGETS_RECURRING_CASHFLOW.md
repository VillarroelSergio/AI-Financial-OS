# 23 — Budgets, Recurring Transactions & Cashflow Planning

## Visión general

La Fase 8.6 añade capacidades de planificación mensual al AI Financial OS, permitiendo al usuario:

1. **Presupuestos por categoría**: definir límites de gasto mensual y recibir alertas cuando se acerca el límite.
2. **Transacciones recurrentes**: registrar gastos e ingresos fijos (suscripciones, salarios, etc.) como plantillas.
3. **Calendario financiero**: visualizar próximos cargos e ingresos en los próximos 30-60 días.
4. **Previsión de cashflow**: proyectar ingresos, gastos y saldo esperado basado en histórico + recurrentes.

El resultado es que el usuario puede responder en cualquier momento: "¿cuánto puedo gastar este mes?", "¿qué cargos tengo próximos?" y "¿mantendré mi plan de ahorro?".

## Modelos de base de datos

### `budgets` table

```
id              VARCHAR PRIMARY KEY (UUID string)
category_id     VARCHAR NOT NULL (foreign key to categories)
period          VARCHAR DEFAULT 'monthly' (monthly | yearly)
amount          DECIMAL(14,2) NOT NULL (límite de gasto en EUR)
alert_threshold_pct INTEGER DEFAULT 80 (% para alerta suave)
active          BOOLEAN DEFAULT TRUE
created_at      DATETIME(tz) NOT NULL
updated_at      DATETIME(tz) NOT NULL
```

Propósito: Almacenar presupuestos por categoría. El período es "monthly" para límites mensuales.

### `recurring_transactions` table

```
id              VARCHAR PRIMARY KEY (UUID string)
name            VARCHAR NOT NULL (ej. "Netflix")
category_id     VARCHAR NULLABLE (opcional)
account_id      VARCHAR NULLABLE (opcional)
amount          DECIMAL(14,2) NOT NULL
currency        VARCHAR DEFAULT 'EUR'
type            VARCHAR NOT NULL (income | expense)
frequency       VARCHAR NOT NULL (monthly | weekly | yearly)
day_of_month    INTEGER NULLABLE (para monthly: 1-31)
day_of_week     INTEGER NULLABLE (para weekly: 0-6)
month_of_year   INTEGER NULLABLE (para yearly: 1-12)
next_date       DATE NOT NULL (siguiente ocurrencia)
active          BOOLEAN DEFAULT TRUE
description     VARCHAR NULLABLE
created_at      DATETIME(tz) NOT NULL
updated_at      DATETIME(tz) NOT NULL
```

Propósito: Almacenar plantillas de transacciones recurrentes. NO son transacciones reales; se usan para proyecciones y calendario. Los campos `day_of_*` permiten calcular ocurrencias futuras sin crear filas manuales.

## API endpoints

### Budgets CRUD

**GET /api/budgets**
- Devuelve lista de presupuestos activos.
- Response: `Budget[]`

**POST /api/budgets**
- Crea nuevo presupuesto.
- Body: `{ category_id, amount, period?, alert_threshold_pct? }`
- Response: `Budget` (201)

**PUT /api/budgets/{id}**
- Actualiza presupuesto.
- Body: `{ amount?, alert_threshold_pct?, active? }`
- Response: `Budget`

**DELETE /api/budgets/{id}**
- Elimina presupuesto.
- Response: 204

**GET /api/budgets/comparison?month=YYYY-MM**
- Compara gasto real vs presupuesto para un mes.
- Response: `BudgetComparisonItem[]`

```json
{
  "budget_id": "uuid",
  "category_id": "uuid",
  "category_name": "Restaurante",
  "budget_amount": 500.0,
  "actual_amount": 420.5,
  "remaining": 79.5,
  "consumption_pct": 84.1,
  "alert": true,
  "over_budget": false,
  "period": "monthly"
}
```

### Recurring Transactions CRUD

**GET /api/recurring**
- Devuelve lista de transacciones recurrentes.
- Response: `RecurringTransaction[]`

**POST /api/recurring**
- Crea nueva recurrente.
- Body: `{ name, amount, type, frequency, next_date, day_of_month?, ... }`
- Response: `RecurringTransaction` (201)

**PUT /api/recurring/{id}**
- Actualiza recurrente.
- Body: `{ name?, amount?, next_date?, active?, ... }`
- Response: `RecurringTransaction`

**DELETE /api/recurring/{id}**
- Elimina recurrente.
- Response: 204

**GET /api/recurring/calendar?days=60**
- Genera calendario con ocurrencias futuras de recurrentes.
- Response: `CalendarEvent[]`

```json
{
  "recurring_id": "uuid",
  "name": "Netflix",
  "amount": 15.99,
  "type": "expense",
  "date": "2026-07-08",
  "category_name": "Entretenimiento"
}
```

### Cashflow Forecast

**GET /api/cashflow/forecast?months=3**
- Proyecta cashflow mensual combinando histórico + recurrentes.
- Response: `CashflowForecast`

```json
{
  "generated_at": "2026-06-29T12:00:00Z",
  "months": [
    {
      "month": "2026-07",
      "projected_income": 2500.0,
      "projected_expenses": 1480.0,
      "projected_balance": 1020.0,
      "historical_avg_income": 2100.0,
      "historical_avg_expenses": 1200.0,
      "recurring_income": 2500.0,
      "recurring_expenses": 850.0
    }
  ]
}
```

La proyección toma `max(histórico_promedio_3meses, suma_recurrentes)` para ser conservadora.

## Componentes frontend

```
PlanificacionPage
├── BudgetTab
│   ├── BudgetFormModal (crear/editar)
│   └── BudgetCard[] (lista comparativa vs gasto real)
├── RecurringTab
│   ├── RecurringFormModal (crear/editar)
│   ├── RecurringItem[] (lista gastos + ingresos)
│   └── UpcomingCalendar (próximos 30 días)
└── CashflowTab
    ├── CashflowChart (gráfico barras ingresos/gastos)
    └── ForecastTable (tabla detallada mensual)
```

**Rutas internas:**
- `apps/desktop/src/features/planning/` — componentes
- `apps/desktop/src/lib/api/budgets.ts` — cliente HTTP
- `apps/desktop/src/lib/hooks/useBudgets.ts` — hooks React
- `apps/desktop/src/pages/PlanificacionPage.tsx` — página

**Navegación:** Link "Planificación" en la barra principal apunta a `/planificacion`.

## Decisiones de diseño

### Recurrentes como plantillas, no como transacciones

Las `recurring_transactions` son **plantillas** para proyecciones, NO entidades que auto-crean `Transaction` rows.

Beneficios:
- El usuario mantiene control explícito: puede registrar manualmente la transacción con descripción real.
- Calendario muestra intenciones, no garantías (si falta la entrada, el usuario lo ve).
- Evita duplicación: no habría que reconciliar recurrente + entrada manual.

Workflow:
1. Usuario crea recurrente "Netflix" para el 8 de cada mes.
2. En el calendario ve "Netflix, 15.99€, 8 Jul".
3. Cuando llega el mes, registra la transacción real (posiblemente con otro monto si cambió tarifa).
4. Previsión y comparativa usan ambas: recurrentes → proyección futura, transacciones → análisis histórico.

### Cashflow = max(histórico, recurrentes)

El endpoint `/api/cashflow/forecast` combina dos fuentes:

- **Histórico:** promedio de últimos 3 meses por tipo (ingresos, gastos).
- **Recurrentes:** suma de todas las recurrentes activas, normalizadas a mes (weekly × 4.33, yearly ÷ 12).

Resultado final: `max(histórico, recurrentes)` por tipo.

Razón: Es conservador. Si el usuario tiene ingresos irregulares pero salario recurrente, usa el salario. Si tiene muchos gastos ocasionales pero pocas recurrentes, usa el histórico.

## Integración futura

- **Insights Engine:** alertas cuando `consumption_pct >= alert_threshold_pct`.
- **IA local:** explicaciones sobre presupuesto (ej. "Has gastado 84% del presupuesto de restaurantes, quedan 5 días").
- **Goals & Simulations:** proyectar ahorro considerando presupuestos y recurrentes.

## Cambios técnicos relacionados

- `Transaction.date` es `String` (ISO format), usado en filtros con `.like("YYYY-MM%")`.
- Presupuestos y recurrentes siguen el patrón SQLAlchemy de `Transaction` y `Goal`.
- Frontend usa React hooks (`useBudgets`, `useRecurring`, `useCashflowForecast`) reutilizables.
