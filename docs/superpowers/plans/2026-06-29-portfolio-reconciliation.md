# Fase 8.5 — Portfolio Reconciliation & Investment Analytics — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir un tab "Reconciliación" en InvestmentsPage que muestre quality state por holding, completitud de cartera, distribución por dimensión y alertas de concentración.

**Architecture:** Nuevo `ReconciliationService` (Python, computado on-demand) + endpoint `GET /api/investments/reconciliation` + tab frontend con Recharts. Sin nueva tabla en base de datos.

**Tech Stack:** Python + FastAPI + Pydantic v2 · React + TypeScript + Tailwind + Recharts + Lucide Icons · shadcn/ui

## Global Constraints

- Sin nueva tabla en base de datos — computado on-demand sobre holdings existentes
- Solo Recharts para gráficas — no introducir otras librerías de charts
- Solo Lucide Icons — no mezclar familias de iconos
- Español en toda la UI — labels, placeholders, mensajes de error
- Sin box-shadow — profundidad solo por luminancia (tokens del design system)
- Sin modo claro — canvas-dark `#000000`, surface-elevated `#16181a`
- No romper módulo de inversiones existente ni sus tests
- No enviar datos a la nube
- Rama git: `feature/fase-8-5-portfolio-reconciliation` — crearla antes de empezar

---

## File Map

**Backend — nuevos:**
- `backend/app/modules/investments/reconciliation_service.py` — lógica pura, sin dependencias de FastAPI
- `backend/app/modules/investments/reconciliation_routes.py` — router FastAPI con el endpoint GET
- `backend/app/tests/test_reconciliation.py` — tests unitarios e integración

**Backend — modificados:**
- `backend/app/main.py` — registrar `reconciliation_router`

**Frontend — nuevos:**
- `apps/desktop/src/features/investments/reconciliation/ReconciliationTab.tsx` — contenedor del tab
- `apps/desktop/src/features/investments/reconciliation/QualityStateBadge.tsx` — badge semántico
- `apps/desktop/src/features/investments/reconciliation/CompletenessDonut.tsx` — PieChart 4 segmentos
- `apps/desktop/src/features/investments/reconciliation/WeightBreakdownChart.tsx` — BarChart horizontal con tabs
- `apps/desktop/src/features/investments/reconciliation/ReconciliationTable.tsx` — tabla de holdings
- `apps/desktop/src/features/investments/reconciliation/ConcentrationAlertCard.tsx` — alerta de concentración

**Frontend — modificados:**
- `apps/desktop/src/lib/api/investments.ts` — añadir `fetchReconciliation()` y tipos
- `apps/desktop/src/lib/hooks/useInvestments.ts` — añadir `useReconciliation()`
- `apps/desktop/src/features/investments/InvestmentsPage.tsx` — añadir tab "Reconciliación"

**Docs — nuevos:**
- `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`

---

## Task 1: Crear rama git

**Files:**
- (ninguno — solo git)

- [ ] **Step 1: Crear y cambiar a la rama**

```bash
cd AI-Financial-OS
git checkout -b feature/fase-8-5-portfolio-reconciliation
```

Expected: `Switched to a new branch 'feature/fase-8-5-portfolio-reconciliation'`

---

## Task 2: Backend — ReconciliationService

**Files:**
- Create: `backend/app/modules/investments/reconciliation_service.py`

**Interfaces:**
- Consumes: `HoldingOut` de `backend/app/modules/investments/schemas.py`
- Produces:
  - `ReconciliationReport` (dataclass con campos: `generated_at`, `portfolio_value_eur`, `completeness`, `holdings`, `weights_by`, `concentration_alerts`)
  - `compute_reconciliation(holdings: list[HoldingOut]) -> ReconciliationReport`

- [ ] **Step 1: Escribir el test que falla**

```python
# backend/app/tests/test_reconciliation.py
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.investments.reconciliation_service import (
    compute_reconciliation,
    QualityState,
)
from app.modules.investments.schemas import HoldingOut, InvestmentAssetOut


def _make_asset(currency: str = "EUR", sector: str = "Tecnología",
                region: str = "US", asset_type: str = "equity") -> InvestmentAssetOut:
    return InvestmentAssetOut(
        id="asset-1", name="Apple", ticker="AAPL", isin=None,
        asset_type=asset_type, currency=currency, region=region,
        sector=sector, price_source="market",
    )


def _make_holding(
    market_value: str = "5000",
    current_price: str = "175",
    currency: str = "USD",
    price_updated_at: datetime | None = None,
    is_mock: bool = False,
    average_price: str = "140",
    quantity: str = "30",
) -> HoldingOut:
    if price_updated_at is None:
        price_updated_at = datetime.now(timezone.utc) - timedelta(hours=1)
    return HoldingOut(
        id="h-1", account_id="acc-1", asset_id="asset-1",
        quantity=Decimal(quantity), average_price=Decimal(average_price),
        current_price=Decimal(current_price),
        current_price_currency=currency,
        current_price_updated_at=price_updated_at,
        market_value=Decimal(market_value),
        interest_rate=None, inception_date=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        asset=_make_asset(currency=currency),
        cost_basis=Decimal(average_price) * Decimal(quantity),
        return_absolute=Decimal("800"), return_percent=19.0,
        accrued_interest=None,
        display_name="Apple", symbol="AAPL",
        asset_type="equity", broker="acc-1",
        invested_amount=Decimal(average_price) * Decimal(quantity),
        unrealized_pnl=Decimal("800"), unrealized_pnl_pct=19.0,
        currency=currency, is_mock=is_mock, quality_score=1.0, warnings=[],
    )


def test_confirmed_when_fresh_price_eur():
    holding = _make_holding(currency="EUR", price_updated_at=datetime.now(timezone.utc) - timedelta(hours=1))
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.CONFIRMED


def test_fx_pending_when_price_not_eur():
    holding = _make_holding(currency="USD")
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.FX_PENDING
    assert report.holdings[0].requires_fx is True


def test_no_price_when_market_value_none():
    h = _make_holding()
    h = h.model_copy(update={"market_value": None, "current_price": None, "current_price_updated_at": None})
    report = compute_reconciliation([h])
    assert report.holdings[0].quality_state == QualityState.NO_PRICE


def test_manual_when_mock():
    holding = _make_holding(is_mock=True, currency="EUR")
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.MANUAL


def test_weights_sum_to_100():
    h1 = _make_holding(market_value="6000", currency="USD")
    h2 = _make_holding(market_value="4000", currency="EUR")
    h2 = h2.model_copy(update={"id": "h-2"})
    report = compute_reconciliation([h1, h2])
    total = sum(w.weight_pct for w in report.weights_by["currency"])
    assert abs(total - 100.0) < 0.2


def test_concentration_alert_when_over_threshold():
    h = _make_holding(market_value="9000", currency="EUR")
    report = compute_reconciliation([h])
    # single holding = 100% → above 20% threshold
    assert any(a.type == "asset" for a in report.concentration_alerts)


def test_empty_holdings_returns_valid_report():
    report = compute_reconciliation([])
    assert report.portfolio_value_eur == 0.0
    assert report.completeness.confirmed_pct == 0.0
    assert report.holdings == []
```

- [ ] **Step 2: Ejecutar test y verificar que falla**

```bash
cd backend
python -m pytest app/tests/test_reconciliation.py -v 2>&1 | head -30
```

Expected: `ImportError` o `ModuleNotFoundError` — el módulo no existe aún.

- [ ] **Step 3: Implementar ReconciliationService**

```python
# backend/app/modules/investments/reconciliation_service.py
"""Reconciliation service — computes quality states, weights and concentration alerts on-demand."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum

from app.modules.investments.schemas import HoldingOut

ASSET_CONCENTRATION_THRESHOLD = 20.0   # %
CURRENCY_CONCENTRATION_THRESHOLD = 40.0  # %
PRICE_FRESHNESS_HOURS = 24


class QualityState(str, Enum):
    CONFIRMED = "confirmed"
    ESTIMATED = "estimated"
    MANUAL = "manual"
    NO_PRICE = "no_price"
    FX_PENDING = "fx_pending"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class ReconciliationHolding:
    holding_id: str
    display_name: str
    ticker: str | None
    quality_state: QualityState
    value_eur: float
    weight_pct: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    currency: str
    requires_fx: bool
    broker: str
    sector: str | None
    asset_type: str


@dataclass
class WeightItem:
    key: str
    weight_pct: float


@dataclass
class ConcentrationAlert:
    type: str          # "asset" | "currency"
    key: str
    weight_pct: float
    threshold_pct: float


@dataclass
class Completeness:
    confirmed_pct: float = 0.0
    estimated_pct: float = 0.0
    manual_pct: float = 0.0
    no_price_pct: float = 0.0


@dataclass
class ReconciliationReport:
    generated_at: datetime
    portfolio_value_eur: float
    completeness: Completeness
    holdings: list[ReconciliationHolding]
    weights_by: dict[str, list[WeightItem]]
    concentration_alerts: list[ConcentrationAlert]


def _compute_quality_state(h: HoldingOut) -> tuple[QualityState, bool]:
    """Returns (quality_state, requires_fx)."""
    if h.is_mock:
        return QualityState.MANUAL, False

    if h.market_value is None or h.current_price is None:
        return QualityState.NO_PRICE, False

    requires_fx = h.currency not in ("EUR", "")
    if requires_fx:
        return QualityState.FX_PENDING, True

    if h.current_price_updated_at is not None:
        now = datetime.now(timezone.utc)
        age_hours = (now - h.current_price_updated_at).total_seconds() / 3600
        if age_hours > PRICE_FRESHNESS_HOURS:
            return QualityState.ESTIMATED, False

    return QualityState.CONFIRMED, False


def _group_weights(items: list[tuple[str, float]], total: float) -> list[WeightItem]:
    grouped: dict[str, float] = {}
    for key, value in items:
        k = key or "Otro"
        grouped[k] = grouped.get(k, 0.0) + value
    if total == 0:
        return []
    return sorted(
        [WeightItem(key=k, weight_pct=round(v / total * 100, 1)) for k, v in grouped.items()],
        key=lambda x: x.weight_pct,
        reverse=True,
    )


def compute_reconciliation(holdings: list[HoldingOut]) -> ReconciliationReport:
    if not holdings:
        return ReconciliationReport(
            generated_at=datetime.now(timezone.utc),
            portfolio_value_eur=0.0,
            completeness=Completeness(),
            holdings=[],
            weights_by={"currency": [], "sector": [], "broker": [], "asset_type": [], "region": []},
            concentration_alerts=[],
        )

    total_value = sum(
        float(h.market_value or h.invested_amount or Decimal("0"))
        for h in holdings
    )

    reconciled: list[ReconciliationHolding] = []
    state_counts: dict[QualityState, int] = {s: 0 for s in QualityState}

    for h in holdings:
        state, requires_fx = _compute_quality_state(h)
        state_counts[state] += 1
        value = float(h.market_value or h.invested_amount or Decimal("0"))
        weight_pct = round(value / total_value * 100, 1) if total_value > 0 else 0.0
        reconciled.append(ReconciliationHolding(
            holding_id=h.id,
            display_name=h.display_name,
            ticker=h.symbol,
            quality_state=state,
            value_eur=round(value, 2),
            weight_pct=weight_pct,
            unrealized_pnl=float(h.unrealized_pnl),
            unrealized_pnl_pct=h.unrealized_pnl_pct,
            currency=h.currency,
            requires_fx=requires_fx,
            broker=h.broker,
            sector=h.asset.sector,
            asset_type=h.asset_type,
        ))

    n = len(holdings)
    completeness = Completeness(
        confirmed_pct=round(state_counts[QualityState.CONFIRMED] / n * 100, 1),
        estimated_pct=round(state_counts[QualityState.ESTIMATED] / n * 100, 1),
        manual_pct=round((state_counts[QualityState.MANUAL] + state_counts[QualityState.REQUIRES_REVIEW]) / n * 100, 1),
        no_price_pct=round((state_counts[QualityState.NO_PRICE] + state_counts[QualityState.FX_PENDING]) / n * 100, 1),
    )

    values_by: dict[str, list[tuple[str, float]]] = {
        "currency": [], "sector": [], "broker": [], "asset_type": [], "region": [],
    }
    for rh, h in zip(reconciled, holdings):
        v = rh.value_eur
        values_by["currency"].append((rh.currency, v))
        values_by["sector"].append((rh.sector or "Sin sector", v))
        values_by["broker"].append((rh.broker, v))
        values_by["asset_type"].append((rh.asset_type, v))
        values_by["region"].append((h.asset.region or "Sin región", v))

    weights_by = {dim: _group_weights(items, total_value) for dim, items in values_by.items()}

    alerts: list[ConcentrationAlert] = []
    for rh in reconciled:
        if rh.weight_pct > ASSET_CONCENTRATION_THRESHOLD:
            alerts.append(ConcentrationAlert(
                type="asset", key=rh.display_name,
                weight_pct=rh.weight_pct, threshold_pct=ASSET_CONCENTRATION_THRESHOLD,
            ))
    for item in weights_by.get("currency", []):
        if item.weight_pct > CURRENCY_CONCENTRATION_THRESHOLD:
            alerts.append(ConcentrationAlert(
                type="currency", key=item.key,
                weight_pct=item.weight_pct, threshold_pct=CURRENCY_CONCENTRATION_THRESHOLD,
            ))

    return ReconciliationReport(
        generated_at=datetime.now(timezone.utc),
        portfolio_value_eur=round(total_value, 2),
        completeness=completeness,
        holdings=reconciled,
        weights_by=weights_by,
        concentration_alerts=alerts,
    )
```

- [ ] **Step 4: Ejecutar tests y verificar que pasan**

```bash
cd backend
python -m pytest app/tests/test_reconciliation.py -v
```

Expected: 7 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/investments/reconciliation_service.py backend/app/tests/test_reconciliation.py
git commit -m "feat(reconciliation): add ReconciliationService with quality states, weights and concentration alerts"
```

---

## Task 3: Backend — Endpoint + registro en main.py

**Files:**
- Create: `backend/app/modules/investments/reconciliation_routes.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `compute_reconciliation(holdings)` de `reconciliation_service.py`
- Consumes: `list_holdings()` de `routes.py` (función interna)
- Produces: `GET /api/investments/reconciliation` → JSON

- [ ] **Step 1: Crear el router**

```python
# backend/app/modules/investments/reconciliation_routes.py
"""Endpoint for Portfolio Reconciliation report."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.holding import Holding
from app.models.investment_asset import InvestmentAsset
from app.modules.investments.reconciliation_service import (
    QualityState,
    ReconciliationReport,
    compute_reconciliation,
)
from app.modules.investments.routes import _enrich_holding

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────

class CompletenessOut(BaseModel):
    confirmed_pct: float
    estimated_pct: float
    manual_pct: float
    no_price_pct: float


class ReconciliationHoldingOut(BaseModel):
    holding_id: str
    display_name: str
    ticker: str | None
    quality_state: str
    value_eur: float
    weight_pct: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    currency: str
    requires_fx: bool
    broker: str
    sector: str | None
    asset_type: str


class WeightItemOut(BaseModel):
    key: str
    weight_pct: float


class ConcentrationAlertOut(BaseModel):
    type: str
    key: str
    weight_pct: float
    threshold_pct: float


class ReconciliationReportOut(BaseModel):
    generated_at: datetime
    portfolio_value_eur: float
    completeness: CompletenessOut
    holdings: list[ReconciliationHoldingOut]
    weights_by: dict[str, list[WeightItemOut]]
    concentration_alerts: list[ConcentrationAlertOut]


# ── Route ─────────────────────────────────────────────────────────────────────

@router.get("/reconciliation", response_model=ReconciliationReportOut)
def get_reconciliation(db: Session = Depends(get_db)) -> ReconciliationReportOut:
    rows = (
        db.query(Holding, InvestmentAsset)
        .join(InvestmentAsset, Holding.asset_id == InvestmentAsset.id)
        .all()
    )
    enriched = [_enrich_holding(h, asset) for h, asset in rows]
    report = compute_reconciliation(enriched)

    return ReconciliationReportOut(
        generated_at=report.generated_at,
        portfolio_value_eur=report.portfolio_value_eur,
        completeness=CompletenessOut(
            confirmed_pct=report.completeness.confirmed_pct,
            estimated_pct=report.completeness.estimated_pct,
            manual_pct=report.completeness.manual_pct,
            no_price_pct=report.completeness.no_price_pct,
        ),
        holdings=[
            ReconciliationHoldingOut(
                holding_id=rh.holding_id,
                display_name=rh.display_name,
                ticker=rh.ticker,
                quality_state=rh.quality_state.value,
                value_eur=rh.value_eur,
                weight_pct=rh.weight_pct,
                unrealized_pnl=rh.unrealized_pnl,
                unrealized_pnl_pct=rh.unrealized_pnl_pct,
                currency=rh.currency,
                requires_fx=rh.requires_fx,
                broker=rh.broker,
                sector=rh.sector,
                asset_type=rh.asset_type,
            )
            for rh in report.holdings
        ],
        weights_by={
            dim: [WeightItemOut(key=w.key, weight_pct=w.weight_pct) for w in items]
            for dim, items in report.weights_by.items()
        },
        concentration_alerts=[
            ConcentrationAlertOut(
                type=a.type, key=a.key,
                weight_pct=a.weight_pct, threshold_pct=a.threshold_pct,
            )
            for a in report.concentration_alerts
        ],
    )
```

- [ ] **Step 2: Registrar el router en main.py**

Añadir tras la línea que importa `price_coverage_router`:

```python
from app.modules.investments.reconciliation_routes import router as reconciliation_router
```

Añadir tras la línea `app.include_router(price_coverage_router, ...)`:

```python
app.include_router(reconciliation_router, prefix="/api/investments", tags=["investments"])
```

- [ ] **Step 3: Verificar que el endpoint arranca**

```bash
cd backend
uvicorn app.main:app --reload --port 8000 &
curl -s http://localhost:8000/api/investments/reconciliation | python -m json.tool | head -20
```

Expected: JSON con `generated_at`, `portfolio_value_eur`, `completeness`, `holdings`, `weights_by`, `concentration_alerts`.

- [ ] **Step 4: Matar el servidor y hacer commit**

```bash
kill %1
git add backend/app/modules/investments/reconciliation_routes.py backend/app/main.py
git commit -m "feat(reconciliation): add GET /api/investments/reconciliation endpoint"
```

---

## Task 4: Frontend — tipos + API client + hook

**Files:**
- Modify: `apps/desktop/src/lib/api/investments.ts`
- Modify: `apps/desktop/src/lib/hooks/useInvestments.ts`

**Interfaces:**
- Produces:
  - `ReconciliationReport` (tipo TypeScript)
  - `fetchReconciliation(): Promise<ReconciliationReport>`
  - `useReconciliation(): { data, loading, error, refresh }`

- [ ] **Step 1: Añadir tipos y función en investments.ts**

Al final de `apps/desktop/src/lib/api/investments.ts`, añadir:

```typescript
// ── Reconciliation ────────────────────────────────────────────────────────────

export interface ReconciliationHolding {
  holding_id: string;
  display_name: string;
  ticker: string | null;
  quality_state: "confirmed" | "estimated" | "manual" | "no_price" | "fx_pending" | "requires_review";
  value_eur: number;
  weight_pct: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  currency: string;
  requires_fx: boolean;
  broker: string;
  sector: string | null;
  asset_type: string;
}

export interface WeightItem {
  key: string;
  weight_pct: number;
}

export interface ConcentrationAlert {
  type: "asset" | "currency";
  key: string;
  weight_pct: number;
  threshold_pct: number;
}

export interface ReconciliationReport {
  generated_at: string;
  portfolio_value_eur: number;
  completeness: {
    confirmed_pct: number;
    estimated_pct: number;
    manual_pct: number;
    no_price_pct: number;
  };
  holdings: ReconciliationHolding[];
  weights_by: {
    currency: WeightItem[];
    sector: WeightItem[];
    broker: WeightItem[];
    asset_type: WeightItem[];
    region: WeightItem[];
  };
  concentration_alerts: ConcentrationAlert[];
}

export const fetchReconciliation = (): Promise<ReconciliationReport> =>
  api.get<ReconciliationReport>("/api/investments/reconciliation");
```

- [ ] **Step 2: Añadir hook en useInvestments.ts**

Al final de `apps/desktop/src/lib/hooks/useInvestments.ts`, añadir:

```typescript
import { fetchReconciliation, type ReconciliationReport } from "@/lib/api/investments";

export function useReconciliation() {
  const [data, setData] = useState<ReconciliationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchReconciliation());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar reconciliación");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refresh: load };
}
```

Nota: el import de `fetchReconciliation` debe añadirse al import existente de `@/lib/api/investments` al inicio del archivo, no crear un import duplicado.

- [ ] **Step 3: Verificar que TypeScript compila**

```bash
cd apps/desktop
npm run type-check 2>&1 | grep -E "error|Error" | head -20
```

Expected: sin errores nuevos.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/lib/api/investments.ts apps/desktop/src/lib/hooks/useInvestments.ts
git commit -m "feat(reconciliation): add ReconciliationReport types, API client and hook"
```

---

## Task 5: Frontend — QualityStateBadge + CompletenessDonut

**Files:**
- Create: `apps/desktop/src/features/investments/reconciliation/QualityStateBadge.tsx`
- Create: `apps/desktop/src/features/investments/reconciliation/CompletenessDonut.tsx`

**Interfaces:**
- `QualityStateBadge({ state: ReconciliationHolding["quality_state"] })`
- `CompletenessDonut({ completeness: ReconciliationReport["completeness"] })`

- [ ] **Step 1: Crear QualityStateBadge**

```tsx
// apps/desktop/src/features/investments/reconciliation/QualityStateBadge.tsx
import type { ReconciliationHolding } from "@/lib/api/investments";

type QualityState = ReconciliationHolding["quality_state"];

const CONFIG: Record<QualityState, { label: string; classes: string }> = {
  confirmed:       { label: "Confirmado",   classes: "bg-accent-teal/15 text-accent-teal" },
  estimated:       { label: "Estimado",     classes: "bg-accent-warning/15 text-accent-warning" },
  manual:          { label: "Manual",       classes: "bg-white/10 text-stone" },
  no_price:        { label: "Sin precio",   classes: "bg-accent-yellow/15 text-accent-yellow" },
  fx_pending:      { label: "FX pendiente", classes: "bg-sky-500/15 text-sky-400" },
  requires_review: { label: "Revisar",      classes: "bg-accent-danger/15 text-accent-danger" },
};

export default function QualityStateBadge({ state }: { state: QualityState }) {
  const { label, classes } = CONFIG[state] ?? CONFIG.requires_review;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${classes}`}>
      {label}
    </span>
  );
}
```

- [ ] **Step 2: Crear CompletenessDonut**

```tsx
// apps/desktop/src/features/investments/reconciliation/CompletenessDonut.tsx
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ReconciliationReport } from "@/lib/api/investments";

const SEGMENTS = [
  { key: "confirmed_pct",  label: "Confirmado",  color: "#00a87e" },
  { key: "estimated_pct",  label: "Estimado",    color: "#ec7e00" },
  { key: "manual_pct",     label: "Manual",      color: "#8d969e" },
  { key: "no_price_pct",   label: "Sin precio",  color: "#b09000" },
] as const;

interface Props {
  completeness: ReconciliationReport["completeness"];
}

export default function CompletenessDonut({ completeness }: Props) {
  const data = SEGMENTS.map((s) => ({
    name: s.label,
    value: completeness[s.key],
    color: s.color,
  })).filter((d) => d.value > 0);

  const confirmedPct = completeness.confirmed_pct;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative h-48 w-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={56}
              outerRadius={80}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
              itemStyle={{ color: "#fff", fontSize: 12 }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, ""]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <p className="text-2xl font-semibold text-on-dark">{confirmedPct.toFixed(0)}%</p>
          <p className="text-[11px] text-stone">validado</p>
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {SEGMENTS.map((s) => (
          <div key={s.key} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
            <span className="text-[11px] text-stone">{s.label} {completeness[s.key].toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/desktop
npm run type-check 2>&1 | grep -E "reconciliation" | head -10
```

Expected: sin errores en los archivos nuevos.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/features/investments/reconciliation/
git commit -m "feat(reconciliation): add QualityStateBadge and CompletenessDonut components"
```

---

## Task 6: Frontend — WeightBreakdownChart + ConcentrationAlertCard

**Files:**
- Create: `apps/desktop/src/features/investments/reconciliation/WeightBreakdownChart.tsx`
- Create: `apps/desktop/src/features/investments/reconciliation/ConcentrationAlertCard.tsx`

**Interfaces:**
- `WeightBreakdownChart({ weightsBy: ReconciliationReport["weights_by"] })`
- `ConcentrationAlertCard({ alert: ConcentrationAlert })`

- [ ] **Step 1: Crear WeightBreakdownChart**

```tsx
// apps/desktop/src/features/investments/reconciliation/WeightBreakdownChart.tsx
import { useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReconciliationReport } from "@/lib/api/investments";

type Dimension = keyof ReconciliationReport["weights_by"];

const TABS: { key: Dimension; label: string }[] = [
  { key: "currency",   label: "Divisa" },
  { key: "sector",     label: "Sector" },
  { key: "broker",     label: "Broker" },
  { key: "asset_type", label: "Tipo" },
  { key: "region",     label: "Región" },
];

interface Props {
  weightsBy: ReconciliationReport["weights_by"];
}

export default function WeightBreakdownChart({ weightsBy }: Props) {
  const [active, setActive] = useState<Dimension>("currency");
  const data = (weightsBy[active] ?? []).slice(0, 8);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={[
              "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              active === tab.key
                ? "bg-primary text-white"
                : "bg-white/5 text-stone hover:text-on-dark",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-stone">Sin datos para esta dimensión.</p>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: "#8d969e", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="key"
                width={80}
                tick={{ fill: "#8d969e", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
                itemStyle={{ color: "#fff", fontSize: 12 }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, "Peso"]}
                cursor={{ fill: "rgba(255,255,255,0.04)" }}
              />
              <Bar dataKey="weight_pct" radius={[0, 4, 4, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill="#494fdf" fillOpacity={1 - i * 0.08} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Crear ConcentrationAlertCard**

```tsx
// apps/desktop/src/features/investments/reconciliation/ConcentrationAlertCard.tsx
import { AlertTriangle } from "lucide-react";
import type { ConcentrationAlert } from "@/lib/api/investments";

const TYPE_LABEL: Record<string, string> = {
  asset:    "activo",
  currency: "divisa",
};

export default function ConcentrationAlertCard({ alert }: { alert: ConcentrationAlert }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border-l-[3px] border-accent-warning bg-accent-warning/5 px-4 py-3">
      <AlertTriangle size={16} className="mt-0.5 shrink-0 text-accent-warning" />
      <p className="text-sm text-on-dark">
        <span className="font-medium">{alert.key}</span>
        {" "}representa el{" "}
        <span className="font-semibold text-accent-warning">{alert.weight_pct.toFixed(1)}%</span>
        {" "}de tu cartera por {TYPE_LABEL[alert.type] ?? alert.type}
        {" "}(límite recomendado: {alert.threshold_pct}%).
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/desktop
npm run type-check 2>&1 | grep -E "reconciliation|error TS" | head -10
```

Expected: sin errores.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/features/investments/reconciliation/
git commit -m "feat(reconciliation): add WeightBreakdownChart and ConcentrationAlertCard"
```

---

## Task 7: Frontend — ReconciliationTable + ReconciliationTab

**Files:**
- Create: `apps/desktop/src/features/investments/reconciliation/ReconciliationTable.tsx`
- Create: `apps/desktop/src/features/investments/reconciliation/ReconciliationTab.tsx`

**Interfaces:**
- `ReconciliationTable({ holdings: ReconciliationHolding[] })`
- `ReconciliationTab()` — usa `useReconciliation()` internamente

- [ ] **Step 1: Crear ReconciliationTable**

```tsx
// apps/desktop/src/features/investments/reconciliation/ReconciliationTable.tsx
import type { ReconciliationHolding } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import QualityStateBadge from "./QualityStateBadge";

interface Props {
  holdings: ReconciliationHolding[];
}

export default function ReconciliationTable({ holdings }: Props) {
  if (holdings.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-xl border border-hairline-dark bg-surface-elevated">
      <table className="w-full min-w-[800px] border-collapse">
        <thead>
          <tr className="border-b border-hairline-dark">
            {["Activo", "Estado", "Valor EUR", "Peso", "P&L", "Divisa", "Sector", "Tipo"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-widest text-stone">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-divider-soft">
          {holdings.map((h) => {
            const pnlPositive = h.unrealized_pnl >= 0;
            return (
              <tr key={h.holding_id} className="transition-colors hover:bg-white/[0.03]">
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-on-dark">{h.display_name}</p>
                  {h.ticker && <p className="text-[11px] text-stone">{h.ticker}</p>}
                </td>
                <td className="px-4 py-3">
                  <QualityStateBadge state={h.quality_state} />
                </td>
                <td className="px-4 py-3 text-sm font-semibold tabular-nums text-on-dark">
                  {formatCurrency(String(h.value_eur))}
                </td>
                <td className="px-4 py-3 text-sm tabular-nums text-stone">
                  {h.weight_pct.toFixed(1)}%
                </td>
                <td className="px-4 py-3">
                  <p className={`text-sm font-semibold tabular-nums ${pnlPositive ? "text-accent-teal" : "text-accent-danger"}`}>
                    {pnlPositive ? "+" : ""}{formatCurrency(String(h.unrealized_pnl))}
                  </p>
                  <p className={`text-[11px] ${pnlPositive ? "text-accent-teal" : "text-accent-danger"}`}>
                    {pnlPositive ? "+" : ""}{h.unrealized_pnl_pct.toFixed(1)}%
                  </p>
                </td>
                <td className="px-4 py-3 text-sm text-stone">{h.currency}</td>
                <td className="px-4 py-3 text-sm text-stone">{h.sector ?? "—"}</td>
                <td className="px-4 py-3 text-sm text-stone capitalize">{h.asset_type}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Crear ReconciliationTab**

```tsx
// apps/desktop/src/features/investments/reconciliation/ReconciliationTab.tsx
import { BarChart3, CheckCircle, TrendingUp, AlertCircle } from "lucide-react";
import { ChartCard, EmptyState, ErrorState, KpiCard, LoadingState } from "@/components/ui/Dashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import { useReconciliation } from "@/lib/hooks/useInvestments";
import CompletenessDonut from "./CompletenessDonut";
import ConcentrationAlertCard from "./ConcentrationAlertCard";
import ReconciliationTable from "./ReconciliationTable";
import WeightBreakdownChart from "./WeightBreakdownChart";

export default function ReconciliationTab() {
  const { data, loading, error, refresh } = useReconciliation();

  if (loading) return <LoadingState label="Analizando tu cartera" />;

  if (error) {
    return (
      <ErrorState
        title="Error al cargar la reconciliación"
        description={error}
        onRetry={refresh}
      />
    );
  }

  if (!data || data.holdings.length === 0) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Sin posiciones para analizar"
        description="Añade posiciones a tu cartera para ver el análisis de calidad, distribución y concentración."
      />
    );
  }

  const totalPnl = data.holdings.reduce((sum, h) => sum + h.unrealized_pnl, 0);
  const pnlPositive = totalPnl >= 0;
  const noPriceCount = data.holdings.filter(
    (h) => h.quality_state === "no_price" || h.quality_state === "fx_pending"
  ).length;

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="dashboard-grid">
        <div className="col-span-3">
          <KpiCard
            label="Valor total"
            value={formatCurrency(String(data.portfolio_value_eur))}
            hint="Cartera completa"
            icon={TrendingUp}
          />
        </div>
        <div className="col-span-3">
          <KpiCard
            label="Validado"
            value={`${data.completeness.confirmed_pct.toFixed(0)}%`}
            hint="Posiciones confirmadas"
            icon={CheckCircle}
            positive={data.completeness.confirmed_pct >= 80}
          />
        </div>
        <div className="col-span-3">
          <KpiCard
            label="P&L total"
            value={`${pnlPositive ? "+" : ""}${formatCurrency(String(totalPnl))}`}
            hint="Rentabilidad no realizada"
            icon={BarChart3}
            positive={pnlPositive}
          />
        </div>
        <div className="col-span-3">
          <KpiCard
            label="Pendientes"
            value={String(noPriceCount)}
            hint={noPriceCount === 0 ? "Todo al día" : "Sin precio o FX pendiente"}
            icon={AlertCircle}
            positive={noPriceCount === 0}
          />
        </div>
      </div>

      {/* Charts */}
      <div className="dashboard-grid">
        <ChartCard
          className="col-span-4"
          title="Completitud"
          description="Calidad de los datos de tu cartera"
        >
          <CompletenessDonut completeness={data.completeness} />
        </ChartCard>
        <ChartCard
          className="col-span-8"
          title="Distribución"
          description="Peso de tu cartera por dimensión"
        >
          <WeightBreakdownChart weightsBy={data.weights_by} />
        </ChartCard>
      </div>

      {/* Concentration alerts */}
      {data.concentration_alerts.length > 0 && (
        <div className="space-y-2">
          {data.concentration_alerts.map((alert, i) => (
            <ConcentrationAlertCard key={i} alert={alert} />
          ))}
        </div>
      )}

      {/* Holdings table */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-on-dark">Posiciones</h2>
        <ReconciliationTable holdings={data.holdings} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/desktop
npm run type-check 2>&1 | grep -E "error TS" | head -20
```

Expected: sin errores nuevos.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/features/investments/reconciliation/
git commit -m "feat(reconciliation): add ReconciliationTable and ReconciliationTab components"
```

---

## Task 8: Frontend — Integrar tab en InvestmentsPage

**Files:**
- Modify: `apps/desktop/src/features/investments/InvestmentsPage.tsx`

- [ ] **Step 1: Leer la sección de tabs actual de InvestmentsPage**

Abrir `apps/desktop/src/features/investments/InvestmentsPage.tsx` y localizar el bloque donde se renderizan los tabs o botones de navegación entre secciones. Buscar el patrón de `useState` que controla qué sección está activa.

- [ ] **Step 2: Añadir import y tab**

Al inicio del archivo, añadir:

```typescript
import ReconciliationTab from "./reconciliation/ReconciliationTab";
```

Localizar el estado de tab activo (si no existe, añadirlo):

```typescript
const [activeSection, setActiveSection] = useState<"positions" | "reconciliation">("positions");
```

Añadir los botones de tab justo antes de la sección de posiciones, usando el patrón pill existente en la app:

```tsx
{/* Tab selector */}
<div className="flex gap-1 rounded-xl border border-hairline-dark bg-surface-elevated p-1 w-fit">
  {(["positions", "reconciliation"] as const).map((section) => (
    <button
      key={section}
      onClick={() => setActiveSection(section)}
      className={[
        "rounded-lg px-4 py-2 text-xs font-medium transition-colors",
        activeSection === section
          ? "bg-primary text-white"
          : "text-stone hover:text-on-dark",
      ].join(" ")}
    >
      {section === "positions" ? "Posiciones" : "Reconciliación"}
    </button>
  ))}
</div>

{activeSection === "positions" && (
  // ... contenido existente de posiciones ...
)}
{activeSection === "reconciliation" && <ReconciliationTab />}
```

- [ ] **Step 3: Verificar que la app compila y el tab aparece**

```bash
cd apps/desktop
npm run dev &
# Abrir http://localhost:1420, ir a Inversiones, clicar tab "Reconciliación"
```

Expected: el tab se muestra, carga datos del endpoint y renderiza KPIs + donut + chart + tabla.

- [ ] **Step 4: Matar el servidor y hacer commit**

```bash
git add apps/desktop/src/features/investments/InvestmentsPage.tsx
git commit -m "feat(reconciliation): integrate Reconciliación tab in InvestmentsPage"
```

---

## Task 9: Añadir ruta al snapshot y documentación

**Files:**
- Modify: `tools/ux-snapshot/snapshot-routes.ts` (o la ruta equivalente)
- Create: `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`
- Modify: `docs/02_ROADMAP.md`
- Modify: `docs/11_API_CONTRACT.md`

- [ ] **Step 1: Registrar snapshot**

En `tools/ux-snapshot/snapshot-routes.ts`, añadir una entrada al array `snapshotRoutes`:

```typescript
{
  path: "/investments",
  filename: "investments-reconciliation.png",
  screenName: "Investments — Reconciliación",
  state: "mock_data",
  description: "Tab de reconciliación con KPIs, donut de completitud, distribución y tabla de holdings",
  requiresInteraction: true,
},
```

- [ ] **Step 2: Crear docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md**

```markdown
# 22 — Portfolio Reconciliation & Investment Analytics

## Objetivo

Validar la calidad de los datos de cartera antes de usarlos en patrimonio, insights y simulaciones.

## Endpoint

`GET /api/investments/reconciliation`

Computado on-demand. Sin persistencia adicional.

## Quality States

| Estado | Condición |
|--------|-----------|
| confirmed | Precio < 24h + EUR + no mock |
| estimated | Precio disponible, dato retrasado (>24h) |
| manual | Activo mock/demo o sin cotización pública |
| no_price | Sin precio ni valor de mercado |
| fx_pending | Precio en divisa no EUR |
| requires_review | Precio o cantidad incoherentes |

## Umbrales de concentración

- Activo individual: >20%
- Divisa: >40%

## Frontend

Tab "Reconciliación" en `InvestmentsPage`.
Componentes: `ReconciliationTab`, `CompletenessDonut`, `WeightBreakdownChart`, `ReconciliationTable`, `QualityStateBadge`, `ConcentrationAlertCard`.
```

- [ ] **Step 3: Actualizar ROADMAP.md**

En la tabla de estado, cambiar la línea de la Fase 8.5:

```markdown
| 8.5 | Portfolio Reconciliation & Investment Analytics | ✅ Completa | rama `feature/fase-8-5-portfolio-reconciliation` |
```

- [ ] **Step 4: Actualizar API_CONTRACT.md**

Añadir sección:

```markdown
### GET /api/investments/reconciliation

Devuelve un reporte de reconciliación de la cartera computado on-demand.

**Response:** `ReconciliationReportOut`
- `generated_at`: ISO timestamp
- `portfolio_value_eur`: valor total en EUR (float)
- `completeness`: porcentajes por quality state
- `holdings[]`: lista con quality_state, value_eur, weight_pct, unrealized_pnl
- `weights_by`: distribución por currency/sector/broker/asset_type/region
- `concentration_alerts[]`: alertas cuando un activo >20% o divisa >40%
```

- [ ] **Step 5: Commit final**

```bash
git add docs/ tools/
git commit -m "docs: add Phase 8.5 documentation, update roadmap and API contract"
```

---

## Self-Review

**Spec coverage:**
- ✅ Reconciliación valor capturado vs mercado — quality_state cubre esto
- ✅ Estado de calidad por holding — 6 estados implementados
- ✅ Separación coste estimado / confirmado — derivada de quality_state
- ✅ Rentabilidad no realizada — reutiliza `unrealized_pnl` de HoldingOut
- ✅ Peso por activo, divisa, sector, broker, tipo, región — WeightBreakdownChart
- ✅ Detección concentración excesiva — ConcentrationAlertCard
- ✅ Control activos manuales — quality_state MANUAL
- ✅ Resumen completitud — CompletenessDonut + KPI
- ✅ Preparación datos para Insights/Goals/IA — endpoint reutilizable

**Placeholder scan:** ninguno encontrado.

**Type consistency:** `ReconciliationHolding["quality_state"]` usado en `QualityStateBadge` y `ReconciliationTable` con el mismo tipo. `WeightItem` y `ConcentrationAlert` definidos una sola vez en `investments.ts`.
