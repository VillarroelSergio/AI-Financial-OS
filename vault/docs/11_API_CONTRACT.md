# 11 — API Contract

## Objetivo

Definir contratos iniciales entre frontend Tauri/React y backend FastAPI.

## Convenciones

- Base URL local de desarrollo: `http://127.0.0.1:8010`.
- JSON.
- Fechas ISO.
- Importes como string decimal en API si se requiere máxima precisión.
- Errores normalizados.

## Health

### GET `/health`

Respuesta:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## Accounts

### GET `/api/accounts`

Devuelve cuentas.

### POST `/api/accounts`

```json
{
  "name": "BBVA",
  "type": "bank",
  "institution": "BBVA",
  "currency": "EUR",
  "current_balance": "1000.00"
}
```

### PATCH `/api/accounts/{id}`

Actualiza cuenta.

### DELETE `/api/accounts/{id}`

Desactiva o elimina cuenta según política.

## Categories

### GET `/api/categories`

### POST `/api/categories`

```json
{
  "name": "Restaurante",
  "type": "expense",
  "color": "#000000",
  "icon": "utensils"
}
```

## Transactions

### GET `/api/transactions`

Filtros:

```txt
account_id
category_id
from_date
to_date
type
source
```

### POST `/api/transactions`

```json
{
  "account_id": "uuid",
  "category_id": "uuid",
  "date": "2026-06-22",
  "description": "Mercadona",
  "amount": "-42.30",
  "currency": "EUR",
  "type": "expense"
}
```

## Dashboard

### GET `/api/dashboard/overview`

Respuesta:

```json
{
  "net_worth": "42350.00",
  "liquidity": "12800.00",
  "investments": "29550.00",
  "monthly_income": "2100.00",
  "monthly_expense": "1480.00",
  "monthly_savings": "620.00",
  "savings_rate": 0.295,
  "currency": "EUR"
}
```

### GET `/api/dashboard/spending?month=2026-06`

```json
{
  "month": "2026-06",
  "total_expense": "1480.00",
  "total_income": "2100.00",
  "by_category": [
    {
      "category": "Restaurante",
      "amount": "240.00",
      "percentage": 0.162
    }
  ]
}
```

## Imports

### POST `/api/imports/preview`

Multipart file upload.

Campos:

```txt
source_type
file
```

Respuesta:

```json
{
  "import_batch_id": "uuid",
  "source_type": "monefy",
  "columns": ["date", "account", "category", "amount"],
  "rows_total": 1082,
  "preview_rows": [],
  "warnings": []
}
```

### POST `/api/imports/{id}/confirm`

Confirma importación.

### POST `/api/imports/{id}/rollback`

Revierte importación.

### GET `/api/imports`

Historial.

La Fase 2 acepta `monefy` y `generic_csv`, procesa UTF-8 localmente (máximo 10 MB),
omite filas inválidas o duplicadas al confirmar y conserva el lote tras un rollback.

## Investments

### GET `/api/investments/summary`

### GET `/api/investments/holdings`

### POST `/api/investments/holdings`

### POST `/api/investments/holdings/merge`

Fusiona dos posiciones duplicadas (misma cuenta + activo). Body `{ source_id, target_id }`:
suma cantidades, recalcula precio medio ponderado, reasigna histórico y operaciones al
target y borra el source. `422` si `source_id == target_id`.

### GET `/api/investments/reconciliation`

Estado de calidad por posición (INV-6): fondos → `manual`, cuentas remuneradas →
`confirmed` (fuente calculada), acciones/ETF por frescura de precio de mercado.

### GET `/api/investments/holdings/portfolio-evolution`

Serie mensual agregada `{ series: [{ month: "YYYY-MM", value }], currency }` (INV-6).
Combina, por mes y con forward-fill, fondos (snapshots), cuentas remuneradas (motor
determinista) y resto (histórico guardado o market_value). Solo datos en BD, sin red.

> `GET /api/investments/summary` incluye `pending_valuation_count` y
> `pending_valuation_invested`: posiciones sin valor de mercado, excluidas de los KPIs de
> rentabilidad en vez de contarse como pérdida.

### Fondos (INV-3)

```txt
POST   /api/investments/funds                          # alta: name, account_id, contributed, value, date
GET    /api/investments/funds/{holding_id}/snapshots
POST   /api/investments/funds/{holding_id}/snapshots   # { date, market_value, contributed_total? } — upsert por fecha
PUT    /api/investments/funds/snapshots/{id}
DELETE /api/investments/funds/snapshots/{id}
```

### Cuentas remuneradas (INV-4)

```txt
POST   /api/investments/savings                        # alta: account_id | new_account_name, opened_at, balance, rate_source, spread_bps, fixed_rate?
GET    /api/investments/savings/{account_id}/projection  # serie mensual + total_interest (+ estimated)
GET    /api/investments/savings/{account_id}           # config actual (para el formulario de edición)
PUT    /api/investments/savings/{account_id}           # editar config (sincroniza TAE/fecha del holding)
DELETE /api/investments/savings/{account_id}           # borrar config (el borrado de la cuenta borra config + holding)
```

Motor determinista (Decimal): interés compuesto mensual, tipo vigente el último día del
mes (BCE facilidad de depósito + spread_bps, o fijo). Aportaciones/retiradas = `Transaction`
tipo `transfer` sobre la cuenta. Modo inverso V1: si solo se conoce el saldo actual, se
retro-calcula el inicial (`estimated=true`).

### Tipo BCE (interno)

```txt
GET    /api/market-intelligence/rates/ecb-deposit-facility?from=YYYY-MM-DD
```
Sirve el cache `ReferenceRateObservation` (ECB SDMX, fallback FRED); ingesta bajo demanda
si está vacío. La UI de cuentas lo consume vía backend, nunca directamente.

Returns on-demand portfolio reconciliation report with quality states, allocation weights, and concentration alerts.

**Response:**

```json
{
  "generated_at": "2026-06-29T12:00:00Z",
  "portfolio_value_eur": 15000.00,
  "completeness": {
    "confirmed_pct": 60.0,
    "estimated_pct": 20.0,
    "manual_pct": 10.0,
    "no_price_pct": 10.0
  },
  "holdings": [
    {
      "holding_id": "uuid",
      "name": "Apple Inc.",
      "ticker": "AAPL",
      "quantity": 0.564555,
      "current_price": 230.45,
      "current_value": 129.99,
      "cost_estimated": 100.99,
      "unrealized_pnl": 29.00,
      "weight_pct": 0.87,
      "currency": "USD",
      "sector": "Technology",
      "asset_type": "stock",
      "broker": "Trade Republic",
      "region": "North America",
      "quality_state": "confirmed",
      "price_freshness_hours": 2
    }
  ],
  "weights_by": {
    "currency": [
      { "key": "EUR", "weight_pct": 40.0 },
      { "key": "USD", "weight_pct": 60.0 }
    ],
    "asset_type": [
      { "key": "stock", "weight_pct": 70.0 },
      { "key": "etf", "weight_pct": 30.0 }
    ],
    "sector": [
      { "key": "Technology", "weight_pct": 45.0 },
      { "key": "Healthcare", "weight_pct": 55.0 }
    ],
    "broker": [
      { "key": "Trade Republic", "weight_pct": 100.0 }
    ],
    "region": [
      { "key": "North America", "weight_pct": 60.0 },
      { "key": "Europe", "weight_pct": 40.0 }
    ]
  },
  "concentration_alerts": [
    {
      "type": "asset",
      "key": "Apple",
      "weight_pct": 25.0,
      "threshold_pct": 20.0
    }
  ]
}
```

**Note on Completeness Schema:** The `completeness` object contains four percentages:
- `confirmed_pct`: holdings with validated price/cost
- `estimated_pct`: holdings with estimated price/cost
- `manual_pct`: includes both manually entered and requires-review holdings
- `no_price_pct`: includes both no-price and fx-pending holdings

## Market Intelligence

La API vigente para mercado, macro, divisas, bonos, noticias e impacto personal esta
bajo `/api/market-intelligence`. Los endpoints legacy `/api/markets/*` y `/api/economy/*`
no estan registrados en `backend/app/main.py`.

### GET `/api/market-intelligence/snapshot/macro`

Devuelve indicadores macro agrupados por region. Cada punto incluye, ademas del valor:
`subcategory`, `frequency` y `priority` (del catalogo), `previous_value` y `delta`
(vs periodo anterior) e `history` (hasta 13 pares `{period, value}` para sparklines).
La `unit` mostrada es siempre la declarada en el catalogo, no la del provider.

### GET `/api/market-intelligence/snapshot/market`

Devuelve indices, cripto y commodities con `provider_id` y `quality_score`.

### GET `/api/market-intelligence/snapshot/forex`

Devuelve tipos de cambio normalizados.

### GET `/api/market-intelligence/snapshot/bonds`

Devuelve rendimientos de bonos.

### GET `/api/market-intelligence/snapshot/news?limit=20`

Devuelve noticias financieras.

### GET `/api/market-intelligence/personal-impact`

Devuelve comparativas deterministas entre datos personales y contexto macro/mercado.
Reglas del contrato:

- `signal` puede ser `positive | negative | neutral | warning | no_data`.
- Si falta el dato de mercado, la comparativa lleva `signal = "no_data"` y su
  `signal_text` nunca afirma un veredicto.
- Las comparativas que no aplican al perfil (sin deuda, sin gasto USD, sin cartera,
  sin gasto en transporte/alimentacion) se omiten de la respuesta.
- El benchmark de cartera usa la variacion a 12 meses de S&P 500 / IBEX 35 /
  EuroStoxx 50 calculada desde `mi_historical_prices` (no el `change_pct` diario).

### GET `/api/market-intelligence/ingest-status`

Devuelve el estado de la ingesta automatica lanzada al arrancar FastAPI. Además del
estado global (`status`, `last_run`, `count`), incluye:

- `results`: detalle por indicador (`indicator`, `category`, `provider`, `success`,
  `fallback_used`, `error` con el motivo por proveedor).
- `storage`: `"file"` o `"memory"`. En `"memory"` la base analítica DuckDB estaba
  bloqueada por otro proceso y los datos no persisten; `storage_warning` explica
  el problema. Este era el origen del fallo intermitente de Mercados.

### GET `/api/market-intelligence/ai-datasheet?scope=daily`

Devuelve un datasheet compacto para consumo de IA local.

## AI

### GET `/api/ai/providers`

### GET `/api/ai/health`

### POST `/api/ai/chat`

```json
{
  "message": "Analiza mis gastos de este mes",
  "context": {
    "module": "Gastos",
    "route": "/spending",
    "period": "2026-06",
    "data_status": "periodo seleccionado en pantalla",
    "visible_metrics": ["gasto total", "ahorro neto", "categorias"]
  }
}
```

Respuesta:

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "...",
  "tool_calls": [],
  "sources": [],
  "quality_score": 0.9,
  "provider": "ollama",
  "model": "qwen3-coder:30b"
}
```

El backend solo acepta claves contextuales permitidas (`module`, `route`, `period`, `visible_metrics`, `data_status`, `selected_entity`, `suggested_action`) y las usa para orientar la respuesta. Las cifras deben salir de tools deterministas, no del contexto visual.

## Document Intelligence / RAG

### GET `/api/rag/documents`

Devuelve documentos locales indexados.

### POST `/api/rag/documents`

```json
{
  "filename": "contrato.txt",
  "title": "Contrato hipoteca",
  "text": "Texto del documento",
  "entity_type": "account",
  "entity_id": "uuid"
}
```

### POST `/api/rag/documents/upload`

Multipart local. Acepta `txt`, `md`, `csv` y `json`.

### POST `/api/rag/query`

```json
{
  "question": "Cuando vence la cuota?",
  "limit": 5
}
```

Devuelve respuesta con `sources` trazables a documento y fragmento.

## Security & Backups

### GET `/api/security/status`

Devuelve estado local de seguridad, ruta de datos y backups.

### GET `/api/security/backups`

Lista backups locales.

### POST `/api/security/backups`

Crea copia local de la base SQLite.

### GET `/api/security/integrity`

Ejecuta validacion de integridad y lista tablas disponibles.

## Portfolio Import

### POST `/api/investments/import/parse-text`

Extrae posiciones de texto pegado por el usuario (local, sin red externa).

```json
Body: { "text": "Apple\nx 0,564555\n140,15 €\n+38,76 %\n\nMicrosoft\nx 1,234\n280,50 €" }

Response: [
  {
    "raw_name": "Apple",
    "quantity": 0.564555,
    "current_value": 140.15,
    "currency": "EUR",
    "return_pct": 38.76,
    "estimated_cost": 100.99
  }
]
```

### POST `/api/investments/import/validate`

Resuelve instrumentos + cobertura de precios para un batch de posiciones raw.

```json
Body: { "positions": [ { "raw_name": "Apple", "quantity": 0.564, ... } ] }

Response: [
  {
    "raw_name": "Apple",
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "market": "NASDAQ",
    "currency": "USD",
    "quantity": 0.564,
    "current_value": 140.15,
    "return_pct": 38.76,
    "estimated_cost": 100.99,
    "current_price": null,
    "eur_value": null,
    "resolution_status": "found",
    "coverage_status": "OK",
    "import_status": "READY",
    "requires_confirmation": false,
    "confirmation_reason": null
  }
]
```

### POST `/api/investments/import/check-duplicates`

```json
Body: { "ticker": "AAPL", "account_id": "uuid" }

Response: {
  "ticker": "AAPL",
  "account_id": "uuid",
  "has_duplicate": false,
  "existing_holding_id": null
}
```

### POST `/api/investments/import/confirm`

Crea holdings confirmados por el usuario. Requiere llamada explícita.

```json
Body: {
  "positions": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "market": "NASDAQ",
      "currency": "USD",
      "quantity": 0.564,
      "average_price": 179.0,
      "price_source": "auto",
      "account_id": "uuid"
    }
  ]
}

Response: {
  "created": 1,
  "skipped": 0,
  "errors": [],
  "holding_ids": ["uuid"]
}
```

## Budgets

### GET `/api/budgets`

Devuelve lista de presupuestos activos.

Response: `Budget[]`

### POST `/api/budgets`

Crea nuevo presupuesto.

```json
{
  "category_id": "uuid",
  "period": "monthly",
  "amount": 500.0,
  "alert_threshold_pct": 80
}
```

Response: `Budget` (201)

### PUT `/api/budgets/{id}`

Actualiza presupuesto.

```json
{
  "amount": 600.0,
  "alert_threshold_pct": 75,
  "active": true
}
```

### DELETE `/api/budgets/{id}`

Elimina presupuesto. Response: 204

### GET `/api/budgets/comparison?month=YYYY-MM`

Compara gasto real vs presupuesto para un mes específico.

Response:

```json
[
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
]
```

## Recurring Transactions

### GET `/api/recurring`

Devuelve lista de transacciones recurrentes ordenadas por fecha próxima.

Response: `RecurringTransaction[]`

### GET `/api/recurring/candidates`

Devuelve candidatos recurrentes detectados desde movimientos existentes. Es un endpoint de lectura: no crea plantillas ni modifica movimientos.

Response:

```json
[
  {
    "id": "netflix:expense",
    "name": "Netflix",
    "description": "Detectado por 3 movimientos similares cada 30 dias.",
    "amount": 15.99,
    "amount_min": 15.99,
    "amount_max": 16.49,
    "currency": "EUR",
    "type": "expense",
    "frequency": "monthly",
    "next_date": "2026-04-05",
    "confidence": 0.86,
    "transaction_count": 3,
    "transaction_ids": ["uuid"],
    "category_id": "uuid",
    "account_id": "uuid",
    "evidence": ["2026-03-05 - Netflix - -16.49 EUR"]
  }
]
```

### POST `/api/recurring`

Crea nueva transacción recurrente.

```json
{
  "name": "Netflix",
  "category_id": "uuid",
  "amount": 15.99,
  "currency": "EUR",
  "type": "expense",
  "frequency": "monthly",
  "day_of_month": 8,
  "next_date": "2026-07-08"
}
```

Response: `RecurringTransaction` (201)

### PUT `/api/recurring/{id}`

Actualiza recurrente.

```json
{
  "name": "Netflix Premium",
  "amount": 17.99,
  "active": true
}
```

### DELETE `/api/recurring/{id}`

Elimina recurrente. Response: 204

### GET `/api/recurring/calendar?days=60`

Genera calendario con ocurrencias futuras de transacciones recurrentes.

Response:

```json
[
  {
    "recurring_id": "uuid",
    "name": "Netflix",
    "amount": 15.99,
    "type": "expense",
    "date": "2026-07-08",
    "category_name": "Entretenimiento"
  }
]
```

Los eventos están ordenados por fecha. Máximo período consultable: 365 días.

## Cashflow

### GET `/api/cashflow/forecast?months=3`

Proyecta cashflow mensual combinando histórico (últimos 3 meses) y transacciones recurrentes activas.

Response:

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

La proyección usa `max(histórico, recurrentes)` para ser conservadora. Máximo: 12 meses.

## Household Bills

### GET `/api/household-bills`

Lista facturas registradas manualmente. Filtros opcionales: `service_type`, `provider`.

### POST `/api/household-bills`

```json
{
  "provider": "Iberdrola",
  "service_type": "electricity",
  "period_start": "2026-05-01",
  "period_end": "2026-05-31",
  "amount": "95.00",
  "currency": "EUR",
  "category_id": "uuid",
  "is_recurring": true,
  "due_date": "2026-06-10"
}
```

### PUT `/api/household-bills/{id}`

Actualiza proveedor, servicio, periodo, importe, categoria, recurrencia, vencimiento o notas.

### DELETE `/api/household-bills/{id}`

Elimina la factura. Response: 204.

### GET `/api/household-bills/summary`

Agrupa por proveedor y tipo de servicio, compara contra la factura anterior, marca subidas anomalas desde +20% y estima el siguiente recibo.

```json
{
  "generated_at": "2026-06-29T20:00:00Z",
  "total_monthly_estimate": 185.0,
  "items": [
    {
      "service_type": "electricity",
      "provider": "Iberdrola",
      "bills_count": 2,
      "last_amount": 110.0,
      "previous_amount": 80.0,
      "change_pct": 37.5,
      "average_amount": 95.0,
      "next_estimate": 110.0,
      "anomaly": true,
      "latest_period": "2026-05-01 - 2026-05-31"
    }
  ]
}
```

## Goals

### GET `/api/goals`

### POST `/api/goals`

```json
{
  "name": "Fondo de emergencia",
  "type": "emergency_fund",
  "target_amount": "10000",
  "current_amount": "2000",
  "monthly_contribution": "300",
  "priority": "high",
  "target_date": "2028-01-01"
}
```

### GET `/api/goals/{id}`

### PATCH `/api/goals/{id}`

### DELETE `/api/goals/{id}`

### POST `/api/goals/{id}/simulate`

Calcula proyección con tres escenarios de crecimiento nominal.

```json
Body: { "inflation_rate": 0.03, "max_months": 360 }

Response: {
  "goal_id": "uuid",
  "current_amount": 2000.0,
  "target_amount": 10000.0,
  "monthly_contribution": 300.0,
  "inflation_rate": 0.03,
  "inflation_adjusted_target": 10927.0,
  "monthly_data": [
    { "month": 0, "label": "Jun 2026", "conservative": 2000, "base": 2000, "optimistic": 2000 }
  ],
  "scenarios": [
    {
      "scenario": "base",
      "label": "Base",
      "color": "#10b981",
      "annual_growth_rate": 0.06,
      "months_to_target": 24,
      "projected_date": "2028-06-29",
      "achievable_by_target_date": true,
      "final_amount": 10000.0
    }
  ],
  "target_date": "2029-01-01",
  "generated_at": "2026-06-29T..."
}
```

### GET `/api/goals/{id}/progress`

```json
{
  "goal_id": "uuid",
  "progress_pct": 20.0,
  "remaining": 8000.0,
  "on_track": true,
  "base_projected_date": "2028-06-29"
}
```

## Patrimonio (net_worth, INS-4)

Servicios deterministas sin IA. Importes como string decimal. Snapshots solo se crean por acción explícita del usuario (cierre de mes asistido); nunca automáticos.

```txt
GET  /api/net-worth/balance-sheet?month=YYYY-MM
GET  /api/net-worth/snapshots?from=YYYY-MM&to=YYYY-MM
GET  /api/net-worth/snapshot-readiness?month=YYYY-MM
POST /api/net-worth/snapshots            {month, force_partial: bool}
```

`GET /balance-sheet` → activos por clase (liquidez, remuneradas, efectivo de inversión, cartera, fondos, otros), pasivos por cuenta `is_liability`, `net_worth = total_assets − total_liabilities`, `net_worth_change` vs snapshot del mes anterior (o `null`), `portfolio_cost`/`portfolio_gain`.

`GET /snapshot-readiness` → checklist derivada de la frescura de datos: `items[{key,label,status: ok|stale|missing,detail,cta_route}]`, `ready` (todos ok), `snapshot_exists`, `snapshot_state`.

`POST /snapshots` → 201 con el snapshot; `data_state=complete` si todo está ok, `partial` (con `missing_items`) si `force_partial=true`. Idempotente por mes (DELETE+INSERT). **409** si faltan elementos y `force_partial=false`.

## Error format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "No se pudo parsear la fecha",
    "details": {}
  }
}
```
