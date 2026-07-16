# 22 — Portfolio Reconciliation & Analytics

## Overview

The Portfolio Reconciliation feature consolidates imported holdings and validates portfolio data quality before it flows into wealth calculations, insights, and simulations. It reconciles captured values, market prices, FX rates, and estimated costs to produce a single source of truth for portfolio composition.

## Architecture

**Backend:** `ReconciliationService` in `backend/app/modules/investments` computes holding quality states, weights, concentration alerts, and completeness metrics.

**API:** `GET /api/investments/reconciliation` returns a `ReconciliationReport` on demand.

**Frontend:** React components in `apps/desktop/src/modules/investments/reconciliation/` visualize completeness, allocation, and quality states.

## Quality States

Each holding is assigned one of six states:

| State | Meaning |
|-------|---------|
| **confirmed** | Price and cost validated via market data or user confirmation. |
| **estimated** | Price estimated from historical data or cost inferred from return %. |
| **manual** | User-entered price or cost; no market validation. |
| **no_price** | Asset lacks market coverage (e.g., private holdings). |
| **fx_pending** | FX rate missing or stale; EUR conversion pending. |
| **requires_review** | Conflicting data or ambiguous instrument; manual review needed. |

**Note on Completeness Metrics:** The `completeness` object aggregates these six states into four percentages:
- `no_price_pct` includes all `no_price` and `fx_pending` holdings
- `manual_pct` includes both `manual` and `requires_review` holdings
- `confirmed_pct` and `estimated_pct` count directly

## Thresholds

- **Asset concentration:** >20% triggers alert.
- **Currency concentration:** >40% triggers alert.
- **Price freshness:** 24 hours; older prices flag as estimated.

## Component Tree

```
ReconciliationTab
├── CompletenessDonut
│   └── segments: confirmed, estimated, manual, no_price, fx_pending, requires_review
├── WeightBreakdownChart (5 dimensions)
│   ├── by_currency
│   ├── by_asset_type
│   ├── by_sector
│   ├── by_broker
│   └── by_region
├── ConcentrationAlertCard (× N alerts)
│   └── asset or currency exceeds threshold
└── ReconciliationTable
    ├── holding_id, name, ticker, quantity, current_price
    ├── current_value, cost_estimated, unrealized_pnl, weight
    └── QualityStateBadge (state color & label)
```

## API Contract

### GET `/api/investments/reconciliation`

Returns portfolio reconciliation report.

**Response (ReconciliationReport):**

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

## Data Flow

1. User imports holdings via Portfolio Import Assistant.
2. Holdings stored with `quality_state`, `current_price`, `cost_estimated`, and FX conversion status.
3. On-demand: `ReconciliationService` aggregates holdings, computes weights, detects concentration.
4. Frontend displays completeness, five-dimensional breakdown, alerts, and detail table.
5. Quality data flows to Goals simulations and Insights Engine for reliable projections.
