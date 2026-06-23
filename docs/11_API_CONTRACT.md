# 11 — API Contract

## Objetivo

Definir contratos iniciales entre frontend Tauri/React y backend FastAPI.

## Convenciones

- Base URL local: `http://127.0.0.1:8000`.
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

## Investments

### GET `/api/investments/summary`

### GET `/api/investments/holdings`

### POST `/api/investments/holdings`

## Market Data

### GET `/api/markets/snapshot`

### POST `/api/markets/refresh`

## Economic Data

### GET `/api/economy/snapshot`

### GET `/api/economy/indicators/{code}`

### POST `/api/economy/refresh`

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
