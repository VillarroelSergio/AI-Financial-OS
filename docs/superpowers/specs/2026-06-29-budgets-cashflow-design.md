# Phase 8.6 — Budgets, Recurring Transactions & Cashflow Planning — Design Spec

## Goal

Pasar del análisis histórico a la planificación mensual: presupuestos por categoría, gastos recurrentes, calendario financiero y previsión de cashflow.

## Architecture

**Backend:** 2 nuevas tablas SQLite (`budgets`, `recurring_transactions`) + 3 módulos FastAPI nuevos (`budgets`, `recurring`, `cashflow`). Sin extensión del modelo Transaction — los recurrentes son plantillas independientes.

**Frontend:** Nueva página `PlanificacionPage` con 3 tabs: Presupuestos, Recurrentes, Cashflow. Integrada en la navegación principal.

**Tech Stack:** Python + FastAPI + SQLAlchemy + SQLite (backend); React + TypeScript + Tailwind + Recharts + Lucide Icons (frontend).

---

## Data Models

### Budget
```
id: str (UUID)
category_id: str (FK → categories.id)
period: "monthly" | "yearly"
amount: Decimal          -- límite del presupuesto
alert_threshold_pct: int -- porcentaje donde se activa alerta suave (default 80)
active: bool
created_at: datetime
updated_at: datetime
```

### RecurringTransaction
```
id: str (UUID)
name: str
category_id: str | None
account_id: str | None
amount: Decimal
currency: str (default "EUR")
type: "income" | "expense"
frequency: "monthly" | "weekly" | "yearly"
day_of_month: int | None  -- 1-31 (para monthly/yearly)
day_of_week: int | None   -- 0-6 (para weekly)
month_of_year: int | None -- 1-12 (para yearly)
next_date: date
active: bool
description: str | None
created_at: datetime
updated_at: datetime
```

---

## API Endpoints

### Budgets
```
GET    /api/budgets                     → list[BudgetOut]
POST   /api/budgets                     → BudgetOut
PUT    /api/budgets/{id}                → BudgetOut
DELETE /api/budgets/{id}                → 204
GET    /api/budgets/comparison?month=YYYY-MM → list[BudgetComparisonItem]
```

**BudgetComparisonItem:**
```json
{
  "budget_id": "...",
  "category_id": "...",
  "category_name": "...",
  "budget_amount": 500.0,
  "actual_amount": 320.0,
  "remaining": 180.0,
  "consumption_pct": 64.0,
  "alert": false,
  "over_budget": false,
  "period": "monthly"
}
```

### Recurring Transactions
```
GET    /api/recurring                   → list[RecurringOut]
POST   /api/recurring                   → RecurringOut
PUT    /api/recurring/{id}              → RecurringOut
DELETE /api/recurring/{id}              → 204
GET    /api/recurring/calendar?days=60  → list[CalendarEvent]
```

**CalendarEvent:**
```json
{
  "recurring_id": "...",
  "name": "Netflix",
  "amount": 15.99,
  "type": "expense",
  "date": "2026-07-08",
  "category_name": "Suscripciones"
}
```

### Cashflow Forecast
```
GET /api/cashflow/forecast?months=3 → CashflowForecast
```

**CashflowForecast:**
```json
{
  "generated_at": "...",
  "months": [
    {
      "month": "2026-07",
      "projected_income": 2500.0,
      "projected_expenses": 1800.0,
      "projected_balance": 700.0,
      "historical_avg_income": 2400.0,
      "historical_avg_expenses": 1750.0,
      "recurring_items": [...]
    }
  ]
}
```

Forecast logic:
- **Income**: avg últimos 3 meses de transactions tipo income + recurrentes activos tipo income
- **Expenses**: avg últimos 3 meses de transactions tipo expense + recurrentes activos tipo expense
- **projected_balance**: income - expenses acumulado

---

## Frontend Layout

### PlanificacionPage (`/planificacion`)

#### Tab 1: Presupuestos
- KPI row (3 cards): Total presupuestado, Total gastado (mes actual), Categorías sobre límite
- Lista de budget cards: cada card muestra barra de progreso (teal <80%, warning 80-100%, danger >100%), nombre categoría, X€ de Y€, % consumido
- Botón "Nuevo presupuesto" → modal (categoría, monto, periodo)
- Estado vacío: "Crea tu primer presupuesto para controlar tus gastos"

#### Tab 2: Recurrentes
- 2 secciones: Gastos fijos | Ingresos fijos
- Cada item: nombre, importe, frecuencia, próxima fecha, categoría, acciones (editar/desactivar)
- Botón "Añadir recurrente" → modal
- Subpanel "Próximos 30 días": lista cronológica de eventos del calendario

#### Tab 3: Cashflow
- Gráfica BarChart (Recharts): barras agrupadas income/expense por mes (3 meses)
- Línea de balance proyectado (area chart overlay)
- Tabla debajo: mes, ingresos proyectados, gastos proyectados, saldo proyectado
- Estado vacío: "Añade transacciones recurrentes para mejorar la previsión"

---

## Component Tree

```
PlanificacionPage
├── BudgetTab
│   ├── BudgetCard (× N)
│   └── BudgetFormModal
├── RecurringTab
│   ├── RecurringItem (× N)
│   ├── RecurringFormModal
│   └── UpcomingCalendar
└── CashflowTab
    ├── CashflowChart
    └── CashflowTable
```

---

## UX Constraints
- Máximo 3 KPIs por sección
- Máximo 1 gráfica grande por tab
- Español en toda la UI
- 5 estados por componente: loading / empty / error / partial / success
- Design tokens: surface-elevated, primary, accent-teal, accent-warning, accent-danger, stone
- No box-shadow

---

## Test Strategy
- Backend: pytest por módulo — CRUD budgets, comparison logic, calendar generation, forecast computation
- Frontend: TypeScript clean (npx tsc --noEmit)

---

## Out of Scope (Phase 8.6)
- Auto-detección de suscripciones desde histórico de importaciones
- Integración con IA local para explicaciones
- Reglas complejas de gastos (extraordinarios, variables programados)
- Notificaciones push de alertas
