# Fase 8.5 — Portfolio Reconciliation & Investment Analytics — Design Spec

**Fecha:** 2026-06-29
**Estado:** Aprobado
**Fase:** 8.5

---

## Objetivo

Consolidar la cartera importada/manual y asegurar que las posiciones, precios, divisas, costes y valoraciones son fiables antes de usarlas en patrimonio, insights y simulaciones.

El usuario obtiene respuesta a:
- ¿Qué parte de mi cartera está completamente validada?
- ¿Qué posiciones usan datos estimados?
- ¿Hay activos que requieren acción manual?
- ¿Estoy demasiado concentrado en algún activo o divisa?

---

## Contexto

Stack: Tauri + React + TypeScript + Tailwind + shadcn/ui + Recharts · Python + FastAPI + SQLite.
Design system: Dark Premium (tokens Revolut). Sin modo claro.

Módulos relevantes:
- `backend/app/modules/investments/routes.py` — CRUD holdings, `_enrich_holding()`
- `backend/app/modules/investments/schemas.py` — `HoldingOut` (ya tiene `cost_basis`, `unrealized_pnl`, `sector`, `region`, `broker`)
- `backend/app/modules/investments/price_coverage_audit.py` — referencia de quality states

---

## Arquitectura

### Backend

```
backend/app/modules/investments/
  reconciliation_service.py    ← ReconciliationService
  reconciliation_routes.py     ← GET /api/investments/reconciliation
```

**ReconciliationService** opera sobre los holdings existentes sin nueva persistencia:

```python
class ReconciliationService:
    def get_report(self, db: Session) -> ReconciliationReport:
        holdings = list_holdings(db)               # reutiliza existente
        enriched = [_enrich_holding(h) for h in holdings]
        quality  = [_compute_quality_state(h) for h in enriched]
        weights  = _compute_weights(enriched)      # por divisa/sector/broker/tipo/región
        alerts   = _detect_concentration(weights)  # umbral 20% activo, 40% divisa
        return ReconciliationReport(...)
```

### Lógica de quality_state

| Estado | Condición |
|--------|-----------|
| `confirmed` | Precio de mercado < 24h + divisa EUR + coste no es estimado |
| `estimated` | Precio disponible pero coste viene de captura/estimación |
| `manual` | `price_update_mode = manual` o activo no cotizado |
| `no_price` | Sin precio de mercado registrado |
| `fx_pending` | Precio en divisa diferente a EUR, sin conversión |
| `requires_review` | Cantidad o precio incoherentes con valor declarado |

### Endpoint

```
GET /api/investments/reconciliation
→ 200 ReconciliationReportOut
→ 200 con completeness todo en 0 si no hay holdings (no 404)
```

### Schema de respuesta

```json
{
  "generated_at": "2026-06-29T10:00:00Z",
  "portfolio_value_eur": 45000.0,
  "completeness": {
    "confirmed_pct": 60.0,
    "estimated_pct": 25.0,
    "manual_pct": 10.0,
    "no_price_pct": 5.0
  },
  "holdings": [
    {
      "holding_id": "uuid",
      "display_name": "Apple",
      "ticker": "AAPL",
      "quality_state": "confirmed",
      "value_eur": 5000.0,
      "weight_pct": 11.1,
      "unrealized_pnl": 800.0,
      "unrealized_pnl_pct": 19.0,
      "currency": "USD",
      "requires_fx": true,
      "broker": "Degiro",
      "sector": "Tecnología",
      "asset_type": "equity"
    }
  ],
  "weights_by": {
    "currency": [{"key": "USD", "weight_pct": 65.0}],
    "sector":   [{"key": "Tecnología", "weight_pct": 40.0}],
    "broker":   [{"key": "Degiro", "weight_pct": 70.0}],
    "asset_type":[{"key": "equity", "weight_pct": 80.0}],
    "region":   [{"key": "US", "weight_pct": 60.0}]
  },
  "concentration_alerts": [
    {"type": "asset", "key": "AAPL", "weight_pct": 22.0, "threshold_pct": 20.0}
  ]
}
```

---

## Frontend

### Archivos nuevos

```
apps/desktop/src/features/investments/reconciliation/
  ReconciliationTab.tsx
  QualityStateBadge.tsx
  CompletenessDonut.tsx
  WeightBreakdownChart.tsx
  ReconciliationTable.tsx
  ConcentrationAlertCard.tsx

apps/desktop/src/lib/api/investments.ts       ← añadir fetchReconciliation()
apps/desktop/src/lib/hooks/useInvestments.ts  ← añadir useReconciliation()
```

### Layout (design system)

```
p-8 max-w-[1500px] mx-auto space-y-6

4 × KpiCard (dashboard-grid col-span-3)
  Valor total EUR | Validado % | P&L total | Pendientes (count)

dashboard-grid:
  col-span-4  CompletenessDonut
    PieChart 4 segmentos:
      confirmed  → #00a87e  (accent-teal)
      estimated  → #ec7e00  (accent-warning)
      manual     → #8d969e  (stone)
      no_price   → #b09000  (accent-yellow)
    Leyenda caption stone debajo

  col-span-8  WeightBreakdownChart
    Tabs pill: Divisa / Sector / Broker / Tipo / Región
    BarChart horizontal: fill #494fdf, axis caption stone
    grid lines divider-soft

[ConcentrationAlertCard × N]  solo si alerts.length > 0
  border-l-3 accent-warning, bg accent-warning/5
  Texto: "AAPL representa el 22% de tu cartera (límite: 20%)"

ReconciliationTable
  Header: caption stone uppercase tracking-widest border-b hairline-dark
  Filas:  body-sm on-dark, hover bg-white/5, divider-soft entre filas
  Cols:   Activo | Estado | Valor EUR | Peso % | P&L | Divisa | Broker | Sector
```

### QualityStateBadge — tokens exactos

```tsx
const config = {
  confirmed:       { label: "Confirmado",   classes: "bg-accent-teal/15 text-accent-teal" },
  estimated:       { label: "Estimado",     classes: "bg-accent-warning/15 text-accent-warning" },
  manual:          { label: "Manual",       classes: "bg-white/10 text-stone" },
  no_price:        { label: "Sin precio",   classes: "bg-accent-yellow/15 text-accent-yellow" },
  fx_pending:      { label: "FX pendiente", classes: "bg-accent-blue/15 text-accent-blue" },
  requires_review: { label: "Revisar",      classes: "bg-accent-danger/15 text-accent-danger" },
}
// aplicar: rounded-full px-2.5 py-1 text-[11px] font-medium
```

### Estados de componente

| Estado | Comportamiento |
|--------|---------------|
| `loading` | `LoadingState label="Analizando tu cartera"` |
| `empty` | `EmptyState` — "Añade posiciones para ver el análisis de tu cartera." |
| `error` | `ErrorState` con botón "Reintentar" |
| `partial` | Datos visibles + badge warning en KPI completitud |
| `success` | Vista completa |

### Integración en InvestmentsPage

Añadir tab "Reconciliación" con el mismo patrón pill activo/inactivo existente. Sin romper tabs actuales.

---

## Data flow

```
InvestmentsPage
  └── ReconciliationTab
        └── useReconciliation()
              └── GET /api/investments/reconciliation
                    └── ReconciliationService
                          ├── list_holdings()
                          ├── _compute_quality_state()
                          ├── _compute_weights()
                          └── _detect_concentration()
```

---

## Testing backend

Archivo: `backend/app/tests/test_reconciliation.py`

Casos:
- Quality state `confirmed` cuando precio < 24h y divisa EUR
- Quality state `fx_pending` cuando precio en USD y cartera en EUR
- Quality state `no_price` cuando sin precio registrado
- Pesos suman 100% (±0.1 por redondeo)
- Concentración detectada cuando holding > 20%
- Cartera vacía → respuesta válida, completeness en 0

---

## Restricciones

- Sin nueva tabla en base de datos — computado on-demand
- No hardcodear precios
- No enviar datos a cloud
- No romper módulo de inversiones existente
- Solo Recharts para gráficas
- Español en toda la UI

---

## Criterios de aceptación

1. `GET /api/investments/reconciliation` devuelve report completo
2. Quality states computados correctamente para los 6 estados
3. Pesos calculados por divisa, sector, broker, tipo de activo y región
4. Alertas de concentración detectadas (>20% activo, >40% divisa)
5. ReconciliationTab visible en InvestmentsPage
6. CompletenessDonut renderiza 4 segmentos con colores del design system
7. WeightBreakdownChart cambia de dimensión con los tabs pill
8. QualityStateBadge usa tokens exactos del design system
9. ConcentrationAlertCard solo aparece cuando hay alertas
10. Estados loading, empty, error implementados
11. Tests backend principales pasan
12. No se rompe el módulo de inversiones existente
13. Documentación `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md` creada

---

## Documentación a crear/actualizar

- Crear: `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`
- Actualizar: `docs/02_ROADMAP.md`
- Actualizar: `docs/11_API_CONTRACT.md`
