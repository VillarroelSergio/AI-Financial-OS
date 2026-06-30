# Budgets, Recurring Transactions & Cashflow Planning — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir planificación financiera mensual: presupuestos por categoría, transacciones recurrentes, calendario financiero y previsión de cashflow.

**Architecture:** 2 nuevas tablas SQLite (budgets, recurring_transactions) + 3 módulos FastAPI + nueva página React con 3 tabs.

**Tech Stack:** Python + FastAPI + SQLAlchemy + SQLite; React + TypeScript + Tailwind + Recharts + Lucide Icons + shadcn/ui.

## Global Constraints

- Rama: `feature/fase-8-6-budgets-cashflow`
- Backend: `backend/app/` — Python 3.12, FastAPI, SQLAlchemy ORM, Pydantic v2, SQLite
- Frontend: `apps/desktop/src/` — React 18, TypeScript, Tailwind CSS (tokens: surface-elevated #16181a, primary #494fdf, accent-teal #00a87e, accent-warning #ec7e00, accent-danger #e23b4a, stone #8d969e, canvas-dark #000000)
- No box-shadow en UI — profundidad solo por luminance
- UI language: español completo
- No scraping, no cloud, no email, local-first
- Commits autónomos autorizados para esta sesión
- Patrón de modelos: seguir `backend/app/models/transaction.py` — UUID como string, timestamps con timezone.utc
- Patrón de rutas: seguir `backend/app/modules/transactions/routes.py`
- ID generation: `str(uuid.uuid4())`

---

### Task 1: DB models — Budget + RecurringTransaction

**Files:**
- Create: `backend/app/models/budget.py`
- Create: `backend/app/models/recurring_transaction.py`
- Modify: `backend/app/core/database.py` (add to Base metadata if needed) or `backend/app/main.py` (create_all)

**Interfaces:**
- Produces: `Budget` SQLAlchemy model, `RecurringTransaction` SQLAlchemy model (imported by Tasks 2, 3, 4)

- [ ] **Step 1: Read existing model pattern**

Read `backend/app/models/transaction.py` to understand column conventions (UUID string, Decimal, datetime with timezone).

- [ ] **Step 2: Create `backend/app/models/budget.py`**

```python
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    period: Mapped[str] = mapped_column(String, nullable=False, default="monthly")  # monthly | yearly
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    alert_threshold_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 3: Create `backend/app/models/recurring_transaction.py`**

```python
from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="EUR")
    type: Mapped[str] = mapped_column(String, nullable=False)  # income | expense
    frequency: Mapped[str] = mapped_column(String, nullable=False)  # monthly | weekly | yearly
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month_of_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_date: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Register models in main.py**

Read `backend/app/main.py`. Find where `Base.metadata.create_all` is called. Add imports for both new models so SQLAlchemy registers the tables:

```python
from app.models.budget import Budget  # noqa: F401
from app.models.recurring_transaction import RecurringTransaction  # noqa: F401
```

- [ ] **Step 5: Verify tables are created**

```bash
cd backend
python -c "
from app.core.database import engine, Base
from app.models.budget import Budget
from app.models.recurring_transaction import RecurringTransaction
Base.metadata.create_all(bind=engine)
from sqlalchemy import inspect
insp = inspect(engine)
print('Tables:', insp.get_table_names())
"
```

Expected: `budgets` and `recurring_transactions` appear in the table list.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/budget.py backend/app/models/recurring_transaction.py backend/app/main.py
git commit -m "feat(budgets): add Budget and RecurringTransaction SQLAlchemy models"
```

---

### Task 2: Backend — Budgets module (CRUD + comparison)

**Files:**
- Create: `backend/app/modules/budgets/` (directory)
- Create: `backend/app/modules/budgets/__init__.py`
- Create: `backend/app/modules/budgets/schemas.py`
- Create: `backend/app/modules/budgets/routes.py`
- Create: `backend/app/tests/test_budgets.py`
- Modify: `backend/app/main.py` (register router)

**Interfaces:**
- Consumes: `Budget` from `app.models.budget`; `Transaction` from `app.models.transaction`; `Category` from `app.models.category`
- Produces: `GET /api/budgets`, `POST /api/budgets`, `PUT /api/budgets/{id}`, `DELETE /api/budgets/{id}`, `GET /api/budgets/comparison`

- [ ] **Step 1: Read existing patterns**

Read `backend/app/modules/transactions/routes.py` and `backend/app/modules/transactions/schemas.py` to understand the Pydantic v2 + FastAPI pattern.

Also check what fields `Transaction` model has for `type` (income/expense) and `date`.

- [ ] **Step 2: Create `backend/app/modules/budgets/schemas.py`**

```python
from __future__ import annotations
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BudgetCreate(BaseModel):
    category_id: str
    period: str = "monthly"
    amount: Decimal
    alert_threshold_pct: int = 80
    active: bool = True


class BudgetUpdate(BaseModel):
    amount: Decimal | None = None
    alert_threshold_pct: int | None = None
    active: bool | None = None


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    period: str
    amount: Decimal
    alert_threshold_pct: int
    active: bool
    created_at: datetime
    updated_at: datetime


class BudgetComparisonItem(BaseModel):
    budget_id: str
    category_id: str
    category_name: str
    budget_amount: float
    actual_amount: float
    remaining: float
    consumption_pct: float
    alert: bool
    over_budget: bool
    period: str
```

- [ ] **Step 3: Create `backend/app/modules/budgets/routes.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.category import Category
from app.modules.budgets.schemas import BudgetCreate, BudgetOut, BudgetUpdate, BudgetComparisonItem

router = APIRouter()


@router.get("", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db)) -> list[BudgetOut]:
    return db.query(Budget).order_by(Budget.created_at.desc()).all()


@router.post("", response_model=BudgetOut, status_code=201)
def create_budget(body: BudgetCreate, db: Session = Depends(get_db)) -> BudgetOut:
    budget = Budget(id=str(uuid.uuid4()), **body.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(budget_id: str, body: BudgetUpdate, db: Session = Depends(get_db)) -> BudgetOut:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(budget, field, value)
    budget.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: str, db: Session = Depends(get_db)) -> None:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()


@router.get("/comparison", response_model=list[BudgetComparisonItem])
def budget_comparison(
    month: str = Query(default=None, description="YYYY-MM format"),
    db: Session = Depends(get_db),
) -> list[BudgetComparisonItem]:
    if month is None:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"

    try:
        year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")

    budgets = db.query(Budget).filter(Budget.active == True).all()
    result: list[BudgetComparisonItem] = []

    for budget in budgets:
        cat = db.get(Category, budget.category_id)
        cat_name = cat.name if cat else budget.category_id

        actual_q = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.category_id == budget.category_id,
                Transaction.type == "expense",
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mon,
            )
            .scalar()
        )
        actual = float(actual_q or Decimal("0"))
        budget_amt = float(budget.amount)
        remaining = budget_amt - actual
        consumption_pct = round(actual / budget_amt * 100, 1) if budget_amt > 0 else 0.0

        result.append(BudgetComparisonItem(
            budget_id=budget.id,
            category_id=budget.category_id,
            category_name=cat_name,
            budget_amount=budget_amt,
            actual_amount=actual,
            remaining=remaining,
            consumption_pct=consumption_pct,
            alert=consumption_pct >= budget.alert_threshold_pct,
            over_budget=actual > budget_amt,
            period=budget.period,
        ))

    return sorted(result, key=lambda x: x.consumption_pct, reverse=True)
```

- [ ] **Step 4: Create `backend/app/modules/budgets/__init__.py`** (empty)

- [ ] **Step 5: Write tests `backend/app/tests/test_budgets.py`**

```python
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_budget(client):
    resp = client.post("/api/budgets", json={
        "category_id": "cat-1",
        "period": "monthly",
        "amount": "500.00",
        "alert_threshold_pct": 80,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category_id"] == "cat-1"
    assert float(data["amount"]) == 500.0


def test_list_budgets(client):
    client.post("/api/budgets", json={"category_id": "cat-1", "amount": "300.00"})
    resp = client.get("/api/budgets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_budget(client):
    resp = client.post("/api/budgets", json={"category_id": "cat-1", "amount": "300.00"})
    bid = resp.json()["id"]
    resp2 = client.put(f"/api/budgets/{bid}", json={"amount": "450.00"})
    assert resp2.status_code == 200
    assert float(resp2.json()["amount"]) == 450.0


def test_delete_budget(client):
    resp = client.post("/api/budgets", json={"category_id": "cat-1", "amount": "300.00"})
    bid = resp.json()["id"]
    assert client.delete(f"/api/budgets/{bid}").status_code == 204
    assert len(client.get("/api/budgets").json()) == 0


def test_comparison_returns_list(client):
    client.post("/api/budgets", json={"category_id": "cat-1", "amount": "500.00"})
    resp = client.get("/api/budgets/comparison?month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["budget_amount"] == 500.0
    assert data[0]["actual_amount"] == 0.0
    assert data[0]["over_budget"] is False
```

- [ ] **Step 6: Run tests**

```bash
cd backend
python -m pytest app/tests/test_budgets.py -v
```

Expected: 5 passed.

- [ ] **Step 7: Register router in main.py**

Add after the other investment/reconciliation imports:
```python
from app.modules.budgets.routes import router as budgets_router
```
And:
```python
app.include_router(budgets_router, prefix="/api/budgets", tags=["budgets"])
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/modules/budgets/ backend/app/tests/test_budgets.py backend/app/main.py
git commit -m "feat(budgets): add Budget CRUD and comparison endpoint"
```

---

### Task 3: Backend — Recurring Transactions module (CRUD + calendar)

**Files:**
- Create: `backend/app/modules/recurring/` (directory)
- Create: `backend/app/modules/recurring/__init__.py`
- Create: `backend/app/modules/recurring/schemas.py`
- Create: `backend/app/modules/recurring/routes.py`
- Create: `backend/app/tests/test_recurring.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `RecurringTransaction` from `app.models.recurring_transaction`; `Category` from `app.models.category`
- Produces: `GET /api/recurring`, `POST /api/recurring`, `PUT /api/recurring/{id}`, `DELETE /api/recurring/{id}`, `GET /api/recurring/calendar`

- [ ] **Step 1: Create `backend/app/modules/recurring/schemas.py`**

```python
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RecurringCreate(BaseModel):
    name: str
    category_id: str | None = None
    account_id: str | None = None
    amount: Decimal
    currency: str = "EUR"
    type: str  # income | expense
    frequency: str  # monthly | weekly | yearly
    day_of_month: int | None = None
    day_of_week: int | None = None
    month_of_year: int | None = None
    next_date: date
    active: bool = True
    description: str | None = None


class RecurringUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = None
    next_date: date | None = None
    active: bool | None = None
    description: str | None = None
    day_of_month: int | None = None


class RecurringOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category_id: str | None
    account_id: str | None
    amount: Decimal
    currency: str
    type: str
    frequency: str
    day_of_month: int | None
    day_of_week: int | None
    month_of_year: int | None
    next_date: date
    active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime


class CalendarEvent(BaseModel):
    recurring_id: str
    name: str
    amount: float
    type: str
    date: date
    category_name: str | None
```

- [ ] **Step 2: Create `backend/app/modules/recurring/routes.py`**

```python
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.models.recurring_transaction import RecurringTransaction
from app.modules.recurring.schemas import (
    CalendarEvent, RecurringCreate, RecurringOut, RecurringUpdate,
)

router = APIRouter()


def _next_occurrences(rt: RecurringTransaction, from_date: date, until: date) -> list[date]:
    """Generate all occurrence dates for a recurring transaction in [from_date, until]."""
    dates: list[date] = []
    cursor = rt.next_date
    # Guard: advance cursor to from_date
    while cursor < from_date:
        cursor = _advance(rt, cursor)
    while cursor <= until:
        dates.append(cursor)
        cursor = _advance(rt, cursor)
    return dates


def _advance(rt: RecurringTransaction, current: date) -> date:
    if rt.frequency == "weekly":
        return current + timedelta(weeks=1)
    elif rt.frequency == "monthly":
        m = current.month + 1
        y = current.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        d = min(rt.day_of_month or current.day, 28)
        return date(y, m, d)
    elif rt.frequency == "yearly":
        return date(current.year + 1, current.month, current.day)
    return current + timedelta(days=30)


@router.get("", response_model=list[RecurringOut])
def list_recurring(db: Session = Depends(get_db)) -> list[RecurringOut]:
    return db.query(RecurringTransaction).order_by(RecurringTransaction.next_date).all()


@router.post("", response_model=RecurringOut, status_code=201)
def create_recurring(body: RecurringCreate, db: Session = Depends(get_db)) -> RecurringOut:
    rt = RecurringTransaction(id=str(uuid.uuid4()), **body.model_dump())
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


@router.put("/{rt_id}", response_model=RecurringOut)
def update_recurring(rt_id: str, body: RecurringUpdate, db: Session = Depends(get_db)) -> RecurringOut:
    rt = db.get(RecurringTransaction, rt_id)
    if not rt:
        raise HTTPException(status_code=404, detail="RecurringTransaction not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rt, field, value)
    rt.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rt)
    return rt


@router.delete("/{rt_id}", status_code=204)
def delete_recurring(rt_id: str, db: Session = Depends(get_db)) -> None:
    rt = db.get(RecurringTransaction, rt_id)
    if not rt:
        raise HTTPException(status_code=404, detail="RecurringTransaction not found")
    db.delete(rt)
    db.commit()


@router.get("/calendar", response_model=list[CalendarEvent])
def get_calendar(
    days: int = Query(default=60, ge=1, le=365),
    db: Session = Depends(get_db),
) -> list[CalendarEvent]:
    from_date = date.today()
    until = from_date + timedelta(days=days)

    rts = db.query(RecurringTransaction).filter(RecurringTransaction.active == True).all()
    events: list[CalendarEvent] = []

    for rt in rts:
        cat = db.get(Category, rt.category_id) if rt.category_id else None
        for occ in _next_occurrences(rt, from_date, until):
            events.append(CalendarEvent(
                recurring_id=rt.id,
                name=rt.name,
                amount=float(rt.amount),
                type=rt.type,
                date=occ,
                category_name=cat.name if cat else None,
            ))

    return sorted(events, key=lambda e: e.date)
```

- [ ] **Step 3: Create `backend/app/modules/recurring/__init__.py`** (empty)

- [ ] **Step 4: Write tests `backend/app/tests/test_recurring.py`**

```python
from __future__ import annotations
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix",
        "amount": "15.99",
        "type": "expense",
        "frequency": "monthly",
        "day_of_month": 8,
        "next_date": "2026-07-08",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Netflix"


def test_list_recurring(client):
    client.post("/api/recurring", json={
        "name": "Salario", "amount": "2500", "type": "income",
        "frequency": "monthly", "day_of_month": 1, "next_date": "2026-07-01",
    })
    resp = client.get("/api/recurring")
    assert len(resp.json()) == 1


def test_update_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": "2026-07-08",
    })
    rid = resp.json()["id"]
    resp2 = client.put(f"/api/recurring/{rid}", json={"amount": "17.99"})
    assert float(resp2.json()["amount"]) == 17.99


def test_delete_recurring(client):
    resp = client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": "2026-07-08",
    })
    rid = resp.json()["id"]
    assert client.delete(f"/api/recurring/{rid}").status_code == 204


def test_calendar_returns_events(client):
    client.post("/api/recurring", json={
        "name": "Netflix", "amount": "15.99", "type": "expense",
        "frequency": "monthly", "day_of_month": 8, "next_date": str(date.today()),
    })
    resp = client.get("/api/recurring/calendar?days=60")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["name"] == "Netflix"
```

- [ ] **Step 5: Run tests**

```bash
cd backend
python -m pytest app/tests/test_recurring.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Register router in main.py**

```python
from app.modules.recurring.routes import router as recurring_router
```
```python
app.include_router(recurring_router, prefix="/api/recurring", tags=["recurring"])
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/recurring/ backend/app/tests/test_recurring.py backend/app/main.py
git commit -m "feat(recurring): add RecurringTransaction CRUD and calendar endpoint"
```

---

### Task 4: Backend — Cashflow Forecast endpoint

**Files:**
- Create: `backend/app/modules/cashflow/` (directory)
- Create: `backend/app/modules/cashflow/__init__.py`
- Create: `backend/app/modules/cashflow/routes.py`
- Create: `backend/app/tests/test_cashflow.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `Transaction` (historical), `RecurringTransaction` (for recurring income/expense)
- Produces: `GET /api/cashflow/forecast`

- [ ] **Step 1: Create `backend/app/modules/cashflow/routes.py`**

```python
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction

router = APIRouter()


class MonthForecast(BaseModel):
    month: str  # YYYY-MM
    projected_income: float
    projected_expenses: float
    projected_balance: float
    historical_avg_income: float
    historical_avg_expenses: float
    recurring_income: float
    recurring_expenses: float


class CashflowForecast(BaseModel):
    generated_at: datetime
    months: list[MonthForecast]


def _monthly_avg(db: Session, tx_type: str, lookback_months: int = 3) -> float:
    today = date.today()
    # Collect last N months sums
    sums = []
    for i in range(1, lookback_months + 1):
        m = today.month - i
        y = today.year + (m - 1) // 12 if m <= 0 else today.year
        m = ((m - 1) % 12) + 1 if m <= 0 else m
        total = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.type == tx_type,
                extract("year", Transaction.date) == y,
                extract("month", Transaction.date) == m,
            )
            .scalar()
        ) or Decimal("0")
        sums.append(float(total))
    return round(sum(sums) / len(sums), 2) if sums else 0.0


def _recurring_monthly(db: Session, tx_type: str) -> float:
    rts = (
        db.query(RecurringTransaction)
        .filter(RecurringTransaction.active == True, RecurringTransaction.type == tx_type)
        .all()
    )
    total = 0.0
    for rt in rts:
        amt = float(rt.amount)
        if rt.frequency == "monthly":
            total += amt
        elif rt.frequency == "weekly":
            total += amt * 4.33
        elif rt.frequency == "yearly":
            total += amt / 12
    return round(total, 2)


@router.get("/forecast", response_model=CashflowForecast)
def get_forecast(
    months: int = Query(default=3, ge=1, le=12),
    db: Session = Depends(get_db),
) -> CashflowForecast:
    avg_income = _monthly_avg(db, "income")
    avg_expenses = _monthly_avg(db, "expense")
    rec_income = _recurring_monthly(db, "income")
    rec_expenses = _recurring_monthly(db, "expense")

    projected_income = max(avg_income, rec_income)
    projected_expenses = max(avg_expenses, rec_expenses)

    today = date.today()
    result_months: list[MonthForecast] = []

    for i in range(months):
        m = today.month + i
        y = today.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        result_months.append(MonthForecast(
            month=f"{y}-{m:02d}",
            projected_income=projected_income,
            projected_expenses=projected_expenses,
            projected_balance=round(projected_income - projected_expenses, 2),
            historical_avg_income=avg_income,
            historical_avg_expenses=avg_expenses,
            recurring_income=rec_income,
            recurring_expenses=rec_expenses,
        ))

    return CashflowForecast(generated_at=datetime.now(timezone.utc), months=result_months)
```

- [ ] **Step 2: Create `backend/app/modules/cashflow/__init__.py`** (empty)

- [ ] **Step 3: Write tests `backend/app/tests/test_cashflow.py`**

```python
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_forecast_returns_correct_month_count(client):
    resp = client.get("/api/cashflow/forecast?months=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["months"]) == 3


def test_forecast_empty_db_returns_zeros(client):
    resp = client.get("/api/cashflow/forecast?months=1")
    m = resp.json()["months"][0]
    assert m["projected_income"] == 0.0
    assert m["projected_expenses"] == 0.0
    assert m["projected_balance"] == 0.0


def test_forecast_month_format(client):
    resp = client.get("/api/cashflow/forecast?months=2")
    months = [m["month"] for m in resp.json()["months"]]
    for m in months:
        parts = m.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 4
        assert len(parts[1]) == 2
```

- [ ] **Step 4: Run tests**

```bash
cd backend
python -m pytest app/tests/test_cashflow.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Register router**

```python
from app.modules.cashflow.routes import router as cashflow_router
```
```python
app.include_router(cashflow_router, prefix="/api/cashflow", tags=["cashflow"])
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/cashflow/ backend/app/tests/test_cashflow.py backend/app/main.py
git commit -m "feat(cashflow): add monthly cashflow forecast endpoint"
```

---

### Task 5: Frontend — Types + API clients + hooks

**Files:**
- Create: `apps/desktop/src/lib/api/budgets.ts`
- Create: `apps/desktop/src/lib/hooks/useBudgets.ts`

**Interfaces:**
- Produces: `fetchBudgets`, `createBudget`, `updateBudget`, `deleteBudget`, `fetchBudgetComparison`, `fetchRecurring`, `createRecurring`, `updateRecurring`, `deleteRecurring`, `fetchCalendar`, `fetchCashflowForecast` — all used by Tasks 6, 7, 8

- [ ] **Step 1: Read existing API client pattern**

Read `apps/desktop/src/lib/api/investments.ts` and `apps/desktop/src/lib/hooks/useInvestments.ts` to understand the pattern.

- [ ] **Step 2: Create `apps/desktop/src/lib/api/budgets.ts`**

```typescript
import { api } from "./client";

// ── Budget types ──────────────────────────────────────────────────────────────

export interface Budget {
  id: string;
  category_id: string;
  period: "monthly" | "yearly";
  amount: number;
  alert_threshold_pct: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BudgetCreate {
  category_id: string;
  period?: "monthly" | "yearly";
  amount: number;
  alert_threshold_pct?: number;
}

export interface BudgetUpdate {
  amount?: number;
  alert_threshold_pct?: number;
  active?: boolean;
}

export interface BudgetComparisonItem {
  budget_id: string;
  category_id: string;
  category_name: string;
  budget_amount: number;
  actual_amount: number;
  remaining: number;
  consumption_pct: number;
  alert: boolean;
  over_budget: boolean;
  period: string;
}

// ── Recurring types ───────────────────────────────────────────────────────────

export interface RecurringTransaction {
  id: string;
  name: string;
  category_id: string | null;
  account_id: string | null;
  amount: number;
  currency: string;
  type: "income" | "expense";
  frequency: "monthly" | "weekly" | "yearly";
  day_of_month: number | null;
  day_of_week: number | null;
  month_of_year: number | null;
  next_date: string;
  active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecurringCreate {
  name: string;
  category_id?: string | null;
  account_id?: string | null;
  amount: number;
  currency?: string;
  type: "income" | "expense";
  frequency: "monthly" | "weekly" | "yearly";
  day_of_month?: number | null;
  next_date: string;
  description?: string | null;
}

export interface CalendarEvent {
  recurring_id: string;
  name: string;
  amount: number;
  type: "income" | "expense";
  date: string;
  category_name: string | null;
}

// ── Cashflow types ────────────────────────────────────────────────────────────

export interface MonthForecast {
  month: string;
  projected_income: number;
  projected_expenses: number;
  projected_balance: number;
  historical_avg_income: number;
  historical_avg_expenses: number;
  recurring_income: number;
  recurring_expenses: number;
}

export interface CashflowForecast {
  generated_at: string;
  months: MonthForecast[];
}

// ── API functions ─────────────────────────────────────────────────────────────

export const fetchBudgets = (): Promise<Budget[]> => api.get<Budget[]>("/api/budgets");
export const createBudget = (body: BudgetCreate): Promise<Budget> => api.post<Budget>("/api/budgets", body);
export const updateBudget = (id: string, body: BudgetUpdate): Promise<Budget> => api.put<Budget>(`/api/budgets/${id}`, body);
export const deleteBudget = (id: string): Promise<void> => api.delete(`/api/budgets/${id}`);
export const fetchBudgetComparison = (month?: string): Promise<BudgetComparisonItem[]> =>
  api.get<BudgetComparisonItem[]>(`/api/budgets/comparison${month ? `?month=${month}` : ""}`);

export const fetchRecurring = (): Promise<RecurringTransaction[]> => api.get<RecurringTransaction[]>("/api/recurring");
export const createRecurring = (body: RecurringCreate): Promise<RecurringTransaction> => api.post<RecurringTransaction>("/api/recurring", body);
export const updateRecurring = (id: string, body: Partial<RecurringCreate>): Promise<RecurringTransaction> => api.put<RecurringTransaction>(`/api/recurring/${id}`, body);
export const deleteRecurring = (id: string): Promise<void> => api.delete(`/api/recurring/${id}`);
export const fetchCalendar = (days?: number): Promise<CalendarEvent[]> =>
  api.get<CalendarEvent[]>(`/api/recurring/calendar${days ? `?days=${days}` : ""}`);

export const fetchCashflowForecast = (months?: number): Promise<CashflowForecast> =>
  api.get<CashflowForecast>(`/api/cashflow/forecast${months ? `?months=${months}` : ""}`);
```

- [ ] **Step 3: Create `apps/desktop/src/lib/hooks/useBudgets.ts`**

```typescript
import { useCallback, useEffect, useState } from "react";
import {
  Budget, BudgetComparisonItem, BudgetCreate, BudgetUpdate, CalendarEvent,
  CashflowForecast, RecurringCreate, RecurringTransaction,
  createBudget, createRecurring, deleteBudget, deleteRecurring,
  fetchBudgetComparison, fetchBudgets, fetchCalendar, fetchCashflowForecast,
  fetchRecurring, updateBudget, updateRecurring,
} from "@/lib/api/budgets";

export function useBudgets() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setBudgets(await fetchBudgets());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar presupuestos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = useCallback(async (body: BudgetCreate) => {
    await createBudget(body);
    await load();
  }, [load]);

  const update = useCallback(async (id: string, body: BudgetUpdate) => {
    await updateBudget(id, body);
    await load();
  }, [load]);

  const remove = useCallback(async (id: string) => {
    await deleteBudget(id);
    await load();
  }, [load]);

  return { budgets, loading, error, refresh: load, add, update, remove };
}

export function useBudgetComparison(month?: string) {
  const [data, setData] = useState<BudgetComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchBudgetComparison(month));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar comparativa");
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, refresh: load };
}

export function useRecurring() {
  const [recurring, setRecurring] = useState<RecurringTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRecurring(await fetchRecurring());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar recurrentes");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = useCallback(async (body: RecurringCreate) => {
    await createRecurring(body);
    await load();
  }, [load]);

  const update = useCallback(async (id: string, body: Partial<RecurringCreate>) => {
    await updateRecurring(id, body);
    await load();
  }, [load]);

  const remove = useCallback(async (id: string) => {
    await deleteRecurring(id);
    await load();
  }, [load]);

  return { recurring, loading, error, refresh: load, add, update, remove };
}

export function useCalendar(days = 60) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setEvents(await fetchCalendar(days));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar calendario");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);
  return { events, loading, error, refresh: load };
}

export function useCashflowForecast(months = 3) {
  const [data, setData] = useState<CashflowForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchCashflowForecast(months));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar previsión");
    } finally {
      setLoading(false);
    }
  }, [months]);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, refresh: load };
}
```

- [ ] **Step 4: TypeScript check**

```bash
cd apps/desktop
npx tsc --noEmit 2>&1 | tail -10
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/lib/api/budgets.ts apps/desktop/src/lib/hooks/useBudgets.ts
git commit -m "feat(budgets): add frontend types, API client and hooks"
```

---

### Task 6: Frontend — BudgetCard + BudgetTab

**Files:**
- Create: `apps/desktop/src/features/planning/BudgetCard.tsx`
- Create: `apps/desktop/src/features/planning/BudgetFormModal.tsx`
- Create: `apps/desktop/src/features/planning/BudgetTab.tsx`

**Interfaces:**
- Consumes: `useBudgets`, `useBudgetComparison` from `@/lib/hooks/useBudgets`
- Consumes: `Budget`, `BudgetComparisonItem`, `BudgetCreate` from `@/lib/api/budgets`

- [ ] **Step 1: Create `apps/desktop/src/features/planning/BudgetCard.tsx`**

```tsx
import type { BudgetComparisonItem } from "@/lib/api/budgets";

interface Props {
  item: BudgetComparisonItem;
}

export default function BudgetCard({ item }: Props) {
  const pct = Math.min(item.consumption_pct, 100);
  const barColor = item.over_budget
    ? "bg-accent-danger"
    : item.alert
    ? "bg-accent-warning"
    : "bg-accent-teal";

  return (
    <div className="rounded-xl bg-surface-elevated p-4 space-y-3">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-on-dark">{item.category_name}</p>
        <span className={[
          "text-xs font-semibold",
          item.over_budget ? "text-accent-danger" : item.alert ? "text-accent-warning" : "text-stone",
        ].join(" ")}>
          {item.consumption_pct.toFixed(0)}%
        </span>
      </div>

      <div className="h-1.5 w-full rounded-full bg-white/8 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-stone">
        <span>
          {item.actual_amount.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
          {" gastado"}
        </span>
        <span>
          {"de "}
          {item.budget_amount.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
        </span>
      </div>

      {item.over_budget && (
        <p className="text-[11px] text-accent-danger">
          +{Math.abs(item.remaining).toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })} sobre el límite
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create `apps/desktop/src/features/planning/BudgetFormModal.tsx`**

Simple form modal for creating budgets:

```tsx
import { useState } from "react";
import { X } from "lucide-react";
import type { BudgetCreate } from "@/lib/api/budgets";

interface Props {
  onSubmit: (data: BudgetCreate) => Promise<void>;
  onClose: () => void;
}

export default function BudgetFormModal({ onSubmit, onClose }: Props) {
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [threshold, setThreshold] = useState("80");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryId || !amount) return;
    setSaving(true);
    try {
      await onSubmit({ category_id: categoryId, amount: parseFloat(amount), alert_threshold_pct: parseInt(threshold) });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-2xl bg-surface-elevated p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-on-dark">Nuevo presupuesto</h3>
          <button onClick={onClose} className="text-stone hover:text-on-dark"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs text-stone">ID de categoría</label>
            <input
              value={categoryId}
              onChange={e => setCategoryId(e.target.value)}
              placeholder="ej. cat-alimentacion"
              className="w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark placeholder:text-stone focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-stone">Importe mensual (€)</label>
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              placeholder="500"
              min="1"
              step="0.01"
              className="w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark placeholder:text-stone focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-stone">Alerta al {threshold}% del límite</label>
            <input
              type="range" min="50" max="100" step="5"
              value={threshold}
              onChange={e => setThreshold(e.target.value)}
              className="w-full accent-primary"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 rounded-lg bg-white/5 py-2.5 text-sm text-stone hover:text-on-dark transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-primary py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-50">
              {saving ? "Guardando..." : "Crear presupuesto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `apps/desktop/src/features/planning/BudgetTab.tsx`**

```tsx
import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import BudgetCard from "./BudgetCard";
import BudgetFormModal from "./BudgetFormModal";
import { useBudgetComparison, useBudgets } from "@/lib/hooks/useBudgets";

export default function BudgetTab() {
  const { add, refresh } = useBudgets();
  const { data, loading, error } = useBudgetComparison();
  const [showModal, setShowModal] = useState(false);

  const overBudget = data.filter(i => i.over_budget).length;
  const totalBudget = data.reduce((s, i) => s + i.budget_amount, 0);
  const totalSpent = data.reduce((s, i) => s + i.actual_amount, 0);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Cargando presupuestos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-accent-danger">{error}</p>
        <button onClick={refresh} className="rounded-lg bg-white/5 px-4 py-2 text-sm text-on-dark hover:bg-white/8">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Presupuestos</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          Nuevo presupuesto
        </button>
      </div>

      {data.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl bg-surface-elevated">
          <p className="text-sm text-stone">Crea tu primer presupuesto para controlar tus gastos</p>
          <button onClick={() => setShowModal(true)} className="rounded-lg bg-primary px-4 py-2 text-sm text-white">
            Crear presupuesto
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total presupuestado", value: totalBudget.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }) },
              { label: "Total gastado", value: totalSpent.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }) },
              { label: "Sobre límite", value: String(overBudget) },
            ].map(kpi => (
              <div key={kpi.label} className="rounded-xl bg-surface-elevated p-4">
                <p className="text-[11px] uppercase tracking-wide text-stone">{kpi.label}</p>
                <p className="mt-1.5 text-xl font-semibold text-on-dark">{kpi.value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.map(item => <BudgetCard key={item.budget_id} item={item} />)}
          </div>
        </>
      )}

      {showModal && (
        <BudgetFormModal onSubmit={add} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
```

- [ ] **Step 4: TypeScript check**

```bash
cd apps/desktop && npx tsc --noEmit 2>&1 | tail -10
```

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/features/planning/
git commit -m "feat(planning): add BudgetCard, BudgetFormModal and BudgetTab"
```

---

### Task 7: Frontend — RecurringTab + CashflowTab

**Files:**
- Create: `apps/desktop/src/features/planning/RecurringItem.tsx`
- Create: `apps/desktop/src/features/planning/RecurringFormModal.tsx`
- Create: `apps/desktop/src/features/planning/UpcomingCalendar.tsx`
- Create: `apps/desktop/src/features/planning/RecurringTab.tsx`
- Create: `apps/desktop/src/features/planning/CashflowChart.tsx`
- Create: `apps/desktop/src/features/planning/CashflowTab.tsx`

**Interfaces:**
- Consumes: `useRecurring`, `useCalendar`, `useCashflowForecast` from `@/lib/hooks/useBudgets`

- [ ] **Step 1: Create `apps/desktop/src/features/planning/RecurringItem.tsx`**

```tsx
import { Trash2 } from "lucide-react";
import type { RecurringTransaction } from "@/lib/api/budgets";

const FREQ_LABEL: Record<string, string> = {
  monthly: "Mensual",
  weekly: "Semanal",
  yearly: "Anual",
};

interface Props {
  item: RecurringTransaction;
  onDelete: (id: string) => void;
}

export default function RecurringItem({ item, onDelete }: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-surface-elevated px-4 py-3">
      <div className="flex items-center gap-3">
        <span className={["h-2 w-2 rounded-full shrink-0", item.type === "income" ? "bg-accent-teal" : "bg-accent-danger"].join(" ")} />
        <div>
          <p className="text-sm font-medium text-on-dark">{item.name}</p>
          <p className="text-[11px] text-stone">{FREQ_LABEL[item.frequency]} · próximo {new Date(item.next_date).toLocaleDateString("es-ES")}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className={["text-sm font-semibold", item.type === "income" ? "text-accent-teal" : "text-on-dark"].join(" ")}>
          {item.type === "income" ? "+" : "-"}
          {item.amount.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
        </span>
        <button onClick={() => onDelete(item.id)} className="text-stone hover:text-accent-danger transition-colors">
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `apps/desktop/src/features/planning/RecurringFormModal.tsx`**

```tsx
import { useState } from "react";
import { X } from "lucide-react";
import type { RecurringCreate } from "@/lib/api/budgets";

interface Props {
  onSubmit: (data: RecurringCreate) => Promise<void>;
  onClose: () => void;
}

export default function RecurringFormModal({ onSubmit, onClose }: Props) {
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [type, setType] = useState<"income" | "expense">("expense");
  const [frequency, setFrequency] = useState<"monthly" | "weekly" | "yearly">("monthly");
  const [nextDate, setNextDate] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !amount || !nextDate) return;
    setSaving(true);
    try {
      await onSubmit({ name, amount: parseFloat(amount), type, frequency, next_date: nextDate });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const inputClass = "w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark focus:outline-none focus:ring-1 focus:ring-primary";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-2xl bg-surface-elevated p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-on-dark">Añadir recurrente</h3>
          <button onClick={onClose} className="text-stone hover:text-on-dark"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Nombre (ej. Netflix)" className={inputClass} required />

          <div className="grid grid-cols-2 gap-3">
            <select value={type} onChange={e => setType(e.target.value as "income" | "expense")} className={inputClass}>
              <option value="expense">Gasto</option>
              <option value="income">Ingreso</option>
            </select>
            <select value={frequency} onChange={e => setFrequency(e.target.value as "monthly" | "weekly" | "yearly")} className={inputClass}>
              <option value="monthly">Mensual</option>
              <option value="weekly">Semanal</option>
              <option value="yearly">Anual</option>
            </select>
          </div>

          <input type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="Importe (€)" min="0.01" step="0.01" className={inputClass} required />
          <input type="date" value={nextDate} onChange={e => setNextDate(e.target.value)} className={inputClass} required />

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 rounded-lg bg-white/5 py-2.5 text-sm text-stone hover:text-on-dark">Cancelar</button>
            <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-primary py-2.5 text-sm font-medium text-white disabled:opacity-50">
              {saving ? "Guardando..." : "Añadir"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `apps/desktop/src/features/planning/UpcomingCalendar.tsx`**

```tsx
import type { CalendarEvent } from "@/lib/api/budgets";

interface Props {
  events: CalendarEvent[];
}

export default function UpcomingCalendar({ events }: Props) {
  if (events.length === 0) {
    return <p className="py-6 text-center text-sm text-stone">No hay eventos próximos.</p>;
  }

  return (
    <div className="space-y-2">
      {events.slice(0, 10).map((ev, i) => (
        <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-white/4 transition-colors">
          <div className="flex items-center gap-3">
            <span className="w-12 text-[11px] text-stone tabular-nums">
              {new Date(ev.date).toLocaleDateString("es-ES", { day: "numeric", month: "short" })}
            </span>
            <span className="text-sm text-on-dark">{ev.name}</span>
          </div>
          <span className={["text-sm font-medium", ev.type === "income" ? "text-accent-teal" : "text-on-dark"].join(" ")}>
            {ev.type === "income" ? "+" : "-"}
            {ev.amount.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
          </span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Create `apps/desktop/src/features/planning/RecurringTab.tsx`**

```tsx
import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import RecurringItem from "./RecurringItem";
import RecurringFormModal from "./RecurringFormModal";
import UpcomingCalendar from "./UpcomingCalendar";
import { useCalendar, useRecurring } from "@/lib/hooks/useBudgets";

export default function RecurringTab() {
  const { recurring, loading, error, add, remove } = useRecurring();
  const { events } = useCalendar(30);
  const [showModal, setShowModal] = useState(false);

  const expenses = recurring.filter(r => r.type === "expense" && r.active);
  const incomes = recurring.filter(r => r.type === "income" && r.active);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Cargando recurrentes...</span>
      </div>
    );
  }

  if (error) {
    return <p className="py-12 text-center text-sm text-accent-danger">{error}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Transacciones recurrentes</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          Añadir
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-3">
          <p className="text-sm font-medium text-on-dark">Gastos fijos ({expenses.length})</p>
          {expenses.length === 0
            ? <p className="text-sm text-stone">Sin gastos recurrentes.</p>
            : expenses.map(r => <RecurringItem key={r.id} item={r} onDelete={remove} />)
          }
        </div>
        <div className="space-y-3">
          <p className="text-sm font-medium text-on-dark">Ingresos fijos ({incomes.length})</p>
          {incomes.length === 0
            ? <p className="text-sm text-stone">Sin ingresos recurrentes.</p>
            : incomes.map(r => <RecurringItem key={r.id} item={r} onDelete={remove} />)
          }
        </div>
      </div>

      <div className="rounded-xl bg-surface-elevated p-5">
        <p className="mb-3 text-sm font-medium text-on-dark">Próximos 30 días</p>
        <UpcomingCalendar events={events} />
      </div>

      {showModal && <RecurringFormModal onSubmit={add} onClose={() => setShowModal(false)} />}
    </div>
  );
}
```

- [ ] **Step 5: Create `apps/desktop/src/features/planning/CashflowChart.tsx`**

```tsx
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import type { MonthForecast } from "@/lib/api/budgets";

interface Props {
  months: MonthForecast[];
}

export default function CashflowChart({ months }: Props) {
  const data = months.map(m => ({
    name: m.month.slice(0, 7),
    ingresos: m.projected_income,
    gastos: m.projected_expenses,
    balance: m.projected_balance,
  }));

  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 8, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="name" tick={{ fill: "#8d969e", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#8d969e", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
          <Tooltip
            contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
            itemStyle={{ color: "#fff", fontSize: 12 }}
            formatter={(value: number) => [value.toLocaleString("es-ES", { style: "currency", currency: "EUR" }), ""]}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#8d969e" }} />
          <Bar dataKey="ingresos" name="Ingresos" fill="#00a87e" radius={[4, 4, 0, 0]} />
          <Bar dataKey="gastos" name="Gastos" fill="#e23b4a" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 6: Create `apps/desktop/src/features/planning/CashflowTab.tsx`**

```tsx
import { RefreshCw } from "lucide-react";
import CashflowChart from "./CashflowChart";
import { useCashflowForecast } from "@/lib/hooks/useBudgets";

export default function CashflowTab() {
  const { data, loading, error, refresh } = useCashflowForecast(3);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Calculando previsión...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-accent-danger">{error}</p>
        <button onClick={refresh} className="rounded-lg bg-white/5 px-4 py-2 text-sm text-on-dark">Reintentar</button>
      </div>
    );
  }

  if (!data || data.months.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-stone">Añade transacciones recurrentes para mejorar la previsión.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Previsión de cashflow</h2>
        <button onClick={refresh} className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-2 text-xs text-stone hover:text-on-dark transition-colors">
          <RefreshCw size={13} />
          Actualizar
        </button>
      </div>

      <div className="rounded-xl bg-surface-elevated p-5">
        <p className="mb-4 text-sm font-medium text-on-dark">Proyección mensual</p>
        <CashflowChart months={data.months} />
      </div>

      <div className="rounded-xl bg-surface-elevated overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wide text-stone">Mes</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Ingresos</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Gastos</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {data.months.map(m => (
              <tr key={m.month} className="border-b border-white/4">
                <td className="px-4 py-3 text-on-dark">{m.month}</td>
                <td className="px-4 py-3 text-right text-accent-teal">{m.projected_income.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}</td>
                <td className="px-4 py-3 text-right text-accent-danger">{m.projected_expenses.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}</td>
                <td className={["px-4 py-3 text-right font-medium", m.projected_balance >= 0 ? "text-accent-teal" : "text-accent-danger"].join(" ")}>
                  {m.projected_balance >= 0 ? "+" : ""}{m.projected_balance.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 7: TypeScript check**

```bash
cd apps/desktop && npx tsc --noEmit 2>&1 | tail -10
```

- [ ] **Step 8: Commit**

```bash
git add apps/desktop/src/features/planning/
git commit -m "feat(planning): add RecurringTab, CashflowTab and sub-components"
```

---

### Task 8: Frontend — PlanificacionPage + navigation integration

**Files:**
- Create: `apps/desktop/src/pages/PlanificacionPage.tsx`
- Modify: Navigation/router file (locate first)

**Interfaces:**
- Consumes: `BudgetTab`, `RecurringTab`, `CashflowTab` from `@/features/planning/`
- Produces: `/planificacion` route with 3 tabs

- [ ] **Step 1: Locate navigation file**

```bash
grep -r "SpendingPage\|GoalsPage\|route\|Route" apps/desktop/src --include="*.tsx" --include="*.ts" -l | head -5
```

- [ ] **Step 2: Create `apps/desktop/src/pages/PlanificacionPage.tsx`**

```tsx
import { useState } from "react";
import BudgetTab from "@/features/planning/BudgetTab";
import CashflowTab from "@/features/planning/CashflowTab";
import RecurringTab from "@/features/planning/RecurringTab";

type Tab = "presupuestos" | "recurrentes" | "cashflow";

const TABS: { key: Tab; label: string }[] = [
  { key: "presupuestos", label: "Presupuestos" },
  { key: "recurrentes", label: "Recurrentes" },
  { key: "cashflow", label: "Cashflow" },
];

export default function PlanificacionPage() {
  const [active, setActive] = useState<Tab>("presupuestos");

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-on-dark">Planificación</h1>
        <p className="text-sm text-stone">Presupuestos, gastos recurrentes y previsión financiera</p>
      </div>

      <div className="flex gap-1 rounded-xl bg-surface-elevated p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={[
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
              active === tab.key ? "bg-primary text-white" : "text-stone hover:text-on-dark",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {active === "presupuestos" && <BudgetTab />}
      {active === "recurrentes" && <RecurringTab />}
      {active === "cashflow" && <CashflowTab />}
    </div>
  );
}
```

- [ ] **Step 3: Add to navigation**

Read the navigation/router file. Add a "Planificación" link/route pointing to `PlanificacionPage`. Follow the exact same pattern as existing nav items (SpendingPage, GoalsPage, etc.).

- [ ] **Step 4: TypeScript check**

```bash
cd apps/desktop && npx tsc --noEmit 2>&1 | tail -10
```

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/pages/PlanificacionPage.tsx <navigation-file>
git commit -m "feat(planning): add PlanificacionPage with 3-tab planning UI"
```

---

### Task 9: Documentation

**Files:**
- Create: `docs/23_BUDGETS_RECURRING_CASHFLOW.md`
- Modify: `docs/02_ROADMAP.md` (mark 8.6 as Completado)
- Modify: `docs/11_API_CONTRACT.md` (add 5 new endpoints)

- [ ] **Step 1: Create `docs/23_BUDGETS_RECURRING_CASHFLOW.md`**

Write ~100 line doc covering:
- Feature overview
- New DB tables: budgets, recurring_transactions (key fields)
- API endpoints (5 endpoints with response shapes)
- Frontend component tree: `PlanificacionPage → BudgetTab | RecurringTab | CashflowTab`
- Design decisions: recurrentes as templates (not transactions), cashflow = avg(last 3 months) + recurring

- [ ] **Step 2: Update roadmap and API contract**

- [ ] **Step 3: Commit**

```bash
git add docs/
git commit -m "docs(planning): add Phase 8.6 docs and update roadmap/API contract"
```
