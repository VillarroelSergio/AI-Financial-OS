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

## Market Intelligence

La API vigente para mercado, macro, divisas, bonos, noticias e impacto personal esta
bajo `/api/market-intelligence`. Los endpoints legacy `/api/markets/*` y `/api/economy/*`
no estan registrados en `backend/app/main.py`.

### GET `/api/market-intelligence/snapshot/macro`

Devuelve indicadores macro agrupados por region.

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

### GET `/api/market-intelligence/ingest-status`

Devuelve el estado de la ingesta automatica lanzada al arrancar FastAPI.

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
    "scope": "spending",
    "period": "2026-06"
  }
}
```

Respuesta:

```json
{
  "answer": "...",
  "tools_used": [],
  "data_period": "2026-06",
  "confidence_level": "medium"
}
```

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
