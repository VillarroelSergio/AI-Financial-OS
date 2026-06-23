# Fase 1 — Financial Core MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el núcleo financiero determinista: modelos de datos, CRUD de cuentas/categorías/movimientos, dashboard Overview y Spending, y pantalla de Ajustes — todo conectado entre frontend React y backend FastAPI.

**Architecture:** Backend-first por módulo: primero los modelos SQLAlchemy y schemas Pydantic, luego las rutas FastAPI, finalmente el frontend React que consume la API. Cada tarea es independientemente testeable. El frontend usa el API client (`src/lib/api/client.ts`) ya existente.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, SQLite, Pydantic v2, React 18, TypeScript, Tailwind CSS (design tokens ya configurados), Recharts, shadcn/ui

## Global Constraints

- IDs: UUID (`str` en Python, `uuid4()` para generación)
- Importes: `Decimal` en Python, `str` en JSON (nunca `float`)
- Fechas: ISO `YYYY-MM-DD`, datetimes en UTC
- Idioma UI: español en todos los labels, placeholders y mensajes
- Estilo: Dark Premium — usar tokens Tailwind: `surface-card`, `surface-elevated`, `on-dark`, `stone`, `hairline-dark`, `accent-teal`, `accent-danger`
- Moneda por defecto: EUR
- NO implementar IA, scraping, automatización bancaria ni lectura de email
- shadcn/ui y Recharts son obligatorios para componentes UI y gráficas
- Base URL backend: `http://127.0.0.1:8000`
- Base URL frontend dev: `http://localhost:1420`
- Working directory backend: `d:/FinancialAgent/AI-Financial-OS/backend`
- Working directory frontend: `d:/FinancialAgent/AI-Financial-OS/apps/desktop`

---

## Task 1: SQLAlchemy Models + DB Initialization

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/account.py`
- Create: `backend/app/models/category.py`
- Create: `backend/app/models/transaction.py`
- Create: `backend/app/models/settings.py`
- Modify: `backend/app/core/database.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `Account`, `Category`, `Transaction`, `AppSetting` ORM classes importables desde `app.models`
- Produces: función `create_tables()` que crea todas las tablas en SQLite
- Produces: `get_db()` session dependency (ya existe, no cambiar la firma)

- [ ] **Step 1: Crear `backend/app/models/account.py`**

```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # cash|bank|broker|savings|investment|mortgage|other
    institution: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Crear `backend/app/models/category.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # income|expense|transfer|investment
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 3: Crear `backend/app/models/transaction.py`**

```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[str] = mapped_column(String, nullable=False)  # YYYY-MM-DD
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    converted_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    converted_currency: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # income|expense|transfer|investment
    source: Mapped[str] = mapped_column(String, default="manual")  # manual|csv|pdf|system
    source_name: Mapped[str | None] = mapped_column(String, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Crear `backend/app/models/settings.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    value_json: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 5: Crear `backend/app/models/__init__.py`**

```python
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.settings import AppSetting

__all__ = ["Account", "Category", "Transaction", "AppSetting"]
```

- [ ] **Step 6: Modificar `backend/app/core/database.py` para crear tablas al arrancar**

Añadir al final del archivo (después de la clase `Base`):

```python
def create_tables() -> None:
    # Importar modelos para que Base los registre antes del create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 7: Modificar `backend/app/main.py` para llamar `create_tables()` al arrancar**

Añadir después de las importaciones existentes y antes de crear `app`:

```python
from app.core.database import create_tables

# Al final del archivo, añadir lifespan o llamada directa:
@app.on_event("startup")
async def startup() -> None:
    create_tables()
```

> Nota: `on_event("startup")` está deprecado en FastAPI moderno pero funciona y es más simple. La alternativa es `lifespan` context manager, pero no hace falta migrar ahora.

- [ ] **Step 8: Verificar que el backend arranca sin errores**

```bash
cd d:/FinancialAgent/AI-Financial-OS/backend
uv run uvicorn app.main:app --reload --port 8000
```

Esperado: servidor arranca, se crean tablas `accounts`, `categories`, `transactions`, `app_settings` en `data/financial.db`. Verificar con:

```bash
python -c "import sqlite3; conn = sqlite3.connect('data/financial.db'); print([r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"
```

Esperado output: `['accounts', 'categories', 'transactions', 'app_settings']`

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/ backend/app/core/database.py backend/app/main.py
git commit -m "feat: add SQLAlchemy models and DB auto-creation for Fase 1"
```

---

## Task 2: Accounts CRUD Backend

**Files:**
- Create: `backend/app/modules/accounts/schemas.py`
- Modify: `backend/app/modules/accounts/routes.py`

**Interfaces:**
- Consumes: `Account` ORM desde `app.models`, `get_db` desde `app.core.database`
- Produces: endpoints `GET /api/accounts`, `POST /api/accounts`, `PATCH /api/accounts/{id}`, `DELETE /api/accounts/{id}`

- [ ] **Step 1: Crear `backend/app/modules/accounts/schemas.py`**

```python
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

class AccountCreate(BaseModel):
    name: str
    type: str  # cash|bank|broker|savings|investment|mortgage|other
    institution: str | None = None
    currency: str = "EUR"
    current_balance: Decimal = Decimal("0.00")

class AccountUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    institution: str | None = None
    currency: str | None = None
    current_balance: Decimal | None = None
    is_active: bool | None = None

class AccountOut(BaseModel):
    id: str
    name: str
    type: str
    institution: str | None
    currency: str
    current_balance: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: object) -> None:
        # Serializar Decimal como str
        object.__setattr__(self, "current_balance", str(self.current_balance))
```

- [ ] **Step 2: Implementar `backend/app/modules/accounts/routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.account import Account
from app.modules.accounts.schemas import AccountCreate, AccountUpdate, AccountOut

router = APIRouter()

@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)) -> list[Account]:
    return db.query(Account).filter(Account.is_active == True).all()  # noqa: E712

@router.post("", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: str, payload: AccountUpdate, db: Session = Depends(get_db)) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Cuenta no encontrada", "details": {}}})
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account

@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: str, db: Session = Depends(get_db)) -> None:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Cuenta no encontrada", "details": {}}})
    account.is_active = False
    db.commit()
```

- [ ] **Step 3: Verificar con curl**

```bash
# Crear cuenta
curl -s -X POST http://127.0.0.1:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"BBVA","type":"bank","institution":"BBVA","currency":"EUR","current_balance":"1000.00"}' | python -m json.tool

# Listar cuentas
curl -s http://127.0.0.1:8000/api/accounts | python -m json.tool
```

Esperado: JSON con cuenta creada y lista con esa cuenta.

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/accounts/
git commit -m "feat: accounts CRUD endpoints"
```

---

## Task 3: Categories CRUD + Seed Backend

**Files:**
- Create: `backend/app/modules/categories/schemas.py`
- Modify: `backend/app/modules/categories/routes.py`
- Create: `backend/app/seeds/categories.py`
- Modify: `backend/app/main.py` (llamar seed en startup si categorías vacías)

**Interfaces:**
- Consumes: `Category` ORM desde `app.models`, `get_db` desde `app.core.database`
- Produces: endpoints `GET /api/categories`, `POST /api/categories`
- Produces: 15 categorías sistema precargadas en primera ejecución

- [ ] **Step 1: Crear `backend/app/modules/categories/schemas.py`**

```python
from datetime import datetime
from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name: str
    type: str  # income|expense|transfer|investment
    parent_id: str | None = None
    icon: str | None = None
    color: str | None = None

class CategoryOut(BaseModel):
    id: str
    name: str
    parent_id: str | None
    type: str
    icon: str | None
    color: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Implementar `backend/app/modules/categories/routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.category import Category
from app.modules.categories.schemas import CategoryCreate, CategoryOut

router = APIRouter()

@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).order_by(Category.name).all()

@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
```

- [ ] **Step 3: Crear directorio y `backend/app/seeds/__init__.py`**

```python
# vacío
```

- [ ] **Step 4: Crear `backend/app/seeds/categories.py`**

```python
from sqlalchemy.orm import Session
from app.models.category import Category

SYSTEM_CATEGORIES = [
    {"name": "Alimentación", "type": "expense", "icon": "shopping-cart", "color": "#00a87e"},
    {"name": "Restaurante", "type": "expense", "icon": "utensils", "color": "#494fdf"},
    {"name": "Casa", "type": "expense", "icon": "home", "color": "#ec7e00"},
    {"name": "Transporte", "type": "expense", "icon": "car", "color": "#8d969e"},
    {"name": "Ocio", "type": "expense", "icon": "gamepad-2", "color": "#b09000"},
    {"name": "Comunicaciones", "type": "expense", "icon": "smartphone", "color": "#505a63"},
    {"name": "Salud", "type": "expense", "icon": "heart-pulse", "color": "#e23b4a"},
    {"name": "Mascotas", "type": "expense", "icon": "paw-print", "color": "#00a87e"},
    {"name": "Regalos", "type": "expense", "icon": "gift", "color": "#4f55f1"},
    {"name": "Ropa", "type": "expense", "icon": "shirt", "color": "#b09000"},
    {"name": "Deportes", "type": "expense", "icon": "dumbbell", "color": "#494fdf"},
    {"name": "Salario", "type": "income", "icon": "briefcase", "color": "#00a87e"},
    {"name": "Ahorros", "type": "income", "icon": "piggy-bank", "color": "#494fdf"},
    {"name": "Depósitos", "type": "investment", "icon": "landmark", "color": "#ec7e00"},
    {"name": "Otros", "type": "expense", "icon": "circle-ellipsis", "color": "#505a63"},
]

def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    for data in SYSTEM_CATEGORIES:
        cat = Category(**data, is_system=True)
        db.add(cat)
    db.commit()
```

- [ ] **Step 5: Modificar startup en `backend/app/main.py` para llamar seed**

En la función `startup()` existente, añadir:

```python
from app.core.database import create_tables, SessionLocal
from app.seeds.categories import seed_categories

@app.on_event("startup")
async def startup() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
```

- [ ] **Step 6: Verificar seed y endpoints**

```bash
curl -s http://127.0.0.1:8000/api/categories | python -m json.tool
```

Esperado: lista de 15 categorías sistema.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/categories/ backend/app/seeds/
git commit -m "feat: categories CRUD + seed 15 system categories"
```

---

## Task 4: Transactions CRUD Backend

**Files:**
- Create: `backend/app/modules/transactions/schemas.py`
- Modify: `backend/app/modules/transactions/routes.py`

**Interfaces:**
- Consumes: `Transaction` ORM desde `app.models`, `get_db` desde `app.core.database`
- Produces: endpoints `GET /api/transactions` (con filtros), `POST /api/transactions`, `PATCH /api/transactions/{id}`, `DELETE /api/transactions/{id}`

- [ ] **Step 1: Crear `backend/app/modules/transactions/schemas.py`**

```python
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class TransactionCreate(BaseModel):
    account_id: str
    category_id: str | None = None
    date: str  # YYYY-MM-DD
    description: str
    amount: Decimal
    currency: str = "EUR"
    type: str  # income|expense|transfer|investment
    notes: str | None = None

class TransactionUpdate(BaseModel):
    category_id: str | None = None
    date: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    notes: str | None = None

class TransactionOut(BaseModel):
    id: str
    account_id: str
    category_id: str | None
    date: str
    description: str
    amount: str
    currency: str
    converted_amount: str | None
    converted_currency: str | None
    type: str
    source: str
    source_name: str | None
    external_id: str | None
    import_batch_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: object) -> None:
        object.__setattr__(self, "amount", str(self.amount))
        if self.converted_amount is not None:
            object.__setattr__(self, "converted_amount", str(self.converted_amount))
```

- [ ] **Step 2: Implementar `backend/app/modules/transactions/routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.transaction import Transaction
from app.modules.transactions.schemas import TransactionCreate, TransactionUpdate, TransactionOut

router = APIRouter()

@router.get("", response_model=list[TransactionOut])
def list_transactions(
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    type: str | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    q = db.query(Transaction)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if from_date:
        q = q.filter(Transaction.date >= from_date)
    if to_date:
        q = q.filter(Transaction.date <= to_date)
    if type:
        q = q.filter(Transaction.type == type)
    if source:
        q = q.filter(Transaction.source == source)
    return q.order_by(Transaction.date.desc()).all()

@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> Transaction:
    tx = Transaction(**payload.model_dump(), source="manual")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(tx_id: str, payload: TransactionUpdate, db: Session = Depends(get_db)) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Movimiento no encontrado", "details": {}}})
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx

@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: str, db: Session = Depends(get_db)) -> None:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Movimiento no encontrado", "details": {}}})
    db.delete(tx)
    db.commit()
```

- [ ] **Step 3: Verificar con curl**

```bash
# Crear transacción (reemplazar account_id y category_id con IDs reales del paso anterior)
curl -s -X POST http://127.0.0.1:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"account_id":"<id>","date":"2026-06-23","description":"Mercadona","amount":"-42.30","currency":"EUR","type":"expense"}' | python -m json.tool

# Listar con filtro
curl -s "http://127.0.0.1:8000/api/transactions?type=expense" | python -m json.tool
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/transactions/
git commit -m "feat: transactions CRUD with filters"
```

---

## Task 5: Dashboard Overview + Spending Backend

**Files:**
- Create: `backend/app/modules/dashboard/schemas.py`
- Modify: `backend/app/modules/dashboard/routes.py`

**Interfaces:**
- Consumes: `Transaction`, `Account`, `Category` ORM, `get_db`
- Produces: `GET /api/dashboard/overview`, `GET /api/dashboard/spending?month=YYYY-MM`

- [ ] **Step 1: Crear `backend/app/modules/dashboard/schemas.py`**

```python
from pydantic import BaseModel

class CategorySpending(BaseModel):
    category_id: str | None
    category: str
    amount: str
    percentage: float

class OverviewOut(BaseModel):
    net_worth: str
    liquidity: str
    investments: str
    monthly_income: str
    monthly_expense: str
    monthly_savings: str
    savings_rate: float
    currency: str

class SpendingOut(BaseModel):
    month: str
    total_expense: str
    total_income: str
    by_category: list[CategorySpending]
```

- [ ] **Step 2: Implementar `backend/app/modules/dashboard/routes.py`**

```python
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.modules.dashboard.schemas import CategorySpending, OverviewOut, SpendingOut

router = APIRouter()

@router.get("/overview", response_model=OverviewOut)
def get_overview(db: Session = Depends(get_db)) -> OverviewOut:
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712

    net_worth = sum(a.current_balance for a in accounts)
    liquidity = sum(
        a.current_balance for a in accounts
        if a.type in ("cash", "bank", "savings")
    )
    investments = sum(
        a.current_balance for a in accounts
        if a.type in ("broker", "investment")
    )

    now = datetime.now(timezone.utc)
    month_prefix = now.strftime("%Y-%m")
    month_txs = db.query(Transaction).filter(Transaction.date.like(f"{month_prefix}%")).all()

    monthly_income = sum(t.amount for t in month_txs if t.type == "income")
    monthly_expense = abs(sum(t.amount for t in month_txs if t.type == "expense"))
    monthly_savings = monthly_income - monthly_expense
    savings_rate = float(monthly_savings / monthly_income) if monthly_income > 0 else 0.0

    return OverviewOut(
        net_worth=str(net_worth),
        liquidity=str(liquidity),
        investments=str(investments),
        monthly_income=str(monthly_income),
        monthly_expense=str(monthly_expense),
        monthly_savings=str(monthly_savings),
        savings_rate=round(savings_rate, 3),
        currency="EUR",
    )

@router.get("/spending", response_model=SpendingOut)
def get_spending(month: str = Query(..., description="YYYY-MM"), db: Session = Depends(get_db)) -> SpendingOut:
    txs = db.query(Transaction).filter(Transaction.date.like(f"{month}%")).all()

    total_income = sum(t.amount for t in txs if t.type == "income")
    expense_txs = [t for t in txs if t.type == "expense"]
    total_expense = abs(sum(t.amount for t in expense_txs))

    # Agrupar por categoría
    by_cat: dict[str | None, Decimal] = {}
    for t in expense_txs:
        by_cat[t.category_id] = by_cat.get(t.category_id, Decimal("0")) + abs(t.amount)

    categories = {c.id: c for c in db.query(Category).all()}
    result: list[CategorySpending] = []
    for cat_id, amount in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        cat_name = categories[cat_id].name if cat_id and cat_id in categories else "Sin categoría"
        pct = float(amount / total_expense) if total_expense > 0 else 0.0
        result.append(CategorySpending(category_id=cat_id, category=cat_name, amount=str(amount), percentage=round(pct, 3)))

    return SpendingOut(
        month=month,
        total_expense=str(total_expense),
        total_income=str(total_income),
        by_category=result,
    )
```

- [ ] **Step 3: Verificar endpoints**

```bash
curl -s http://127.0.0.1:8000/api/dashboard/overview | python -m json.tool
curl -s "http://127.0.0.1:8000/api/dashboard/spending?month=2026-06" | python -m json.tool
```

Esperado: respuesta válida (ceros si no hay datos, sin errores 500).

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/dashboard/
git commit -m "feat: dashboard overview and spending endpoints"
```

---

## Task 6: Settings Backend

**Files:**
- Create: `backend/app/modules/settings/schemas.py`
- Modify: `backend/app/modules/settings/routes.py`
- Modify: `backend/app/seeds/categories.py` (añadir seed settings)

**Interfaces:**
- Consumes: `AppSetting` ORM, `get_db`
- Produces: `GET /api/settings`, `PATCH /api/settings/{key}`

- [ ] **Step 1: Crear `backend/app/modules/settings/schemas.py`**

```python
from datetime import datetime
from pydantic import BaseModel

class SettingOut(BaseModel):
    id: str
    key: str
    value_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class SettingUpdate(BaseModel):
    value_json: str
```

- [ ] **Step 2: Implementar `backend/app/modules/settings/routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.settings import AppSetting
from app.modules.settings.schemas import SettingOut, SettingUpdate

router = APIRouter()

@router.get("", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db)) -> list[AppSetting]:
    return db.query(AppSetting).all()

@router.patch("/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)) -> AppSetting:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Configuración no encontrada", "details": {}}})
    setting.value_json = payload.value_json
    db.commit()
    db.refresh(setting)
    return setting
```

- [ ] **Step 3: Añadir seed de settings por defecto**

Crear `backend/app/seeds/settings.py`:

```python
import json
from sqlalchemy.orm import Session
from app.models.settings import AppSetting

DEFAULT_SETTINGS = [
    ("app.language", "es"),
    ("theme.mode", "dark"),
    ("app.currency", "EUR"),
]

def seed_settings(db: Session) -> None:
    for key, value in DEFAULT_SETTINGS:
        if not db.query(AppSetting).filter(AppSetting.key == key).first():
            db.add(AppSetting(key=key, value_json=json.dumps(value)))
    db.commit()
```

- [ ] **Step 4: Añadir `seed_settings` al startup en `main.py`**

```python
from app.seeds.settings import seed_settings

# En la función startup():
seed_settings(db)
```

- [ ] **Step 5: Verificar**

```bash
curl -s http://127.0.0.1:8000/api/settings | python -m json.tool
```

Esperado: lista con 3 settings (`app.language`, `theme.mode`, `app.currency`).

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/settings/ backend/app/seeds/
git commit -m "feat: settings CRUD backend + default settings seed"
```

---

## Task 7: Frontend API Layer + Formatters

**Files:**
- Create: `apps/desktop/src/lib/api/accounts.ts`
- Create: `apps/desktop/src/lib/api/categories.ts`
- Create: `apps/desktop/src/lib/api/transactions.ts`
- Create: `apps/desktop/src/lib/api/dashboard.ts`
- Create: `apps/desktop/src/lib/api/settings.ts`
- Create: `apps/desktop/src/lib/formatters/currency.ts`
- Create: `apps/desktop/src/lib/hooks/useAccounts.ts`
- Create: `apps/desktop/src/lib/hooks/useCategories.ts`
- Create: `apps/desktop/src/lib/hooks/useTransactions.ts`
- Create: `apps/desktop/src/lib/hooks/useDashboard.ts`

**Interfaces:**
- Consumes: `api` client desde `@/lib/api/client`, tipos desde `@/lib/types`
- Produces: funciones `fetchAccounts()`, `createAccount()`, `updateAccount()`, `deleteAccount()`, análogos para categories/transactions, `fetchOverview()`, `fetchSpending(month)`
- Produces: `formatCurrency(amount, currency?)`, `formatPercent(ratio)`
- Produces: hooks `useAccounts()`, `useCategories()`, `useTransactions(filters?)`, `useOverview()`, `useSpending(month)`

- [ ] **Step 1: Crear `apps/desktop/src/lib/api/accounts.ts`**

```typescript
import { api } from "./client";
import type { Account } from "@/lib/types";

export interface AccountCreate {
  name: string;
  type: string;
  institution?: string;
  currency?: string;
  current_balance?: string;
}

export interface AccountUpdate {
  name?: string;
  type?: string;
  institution?: string;
  currency?: string;
  current_balance?: string;
  is_active?: boolean;
}

export const fetchAccounts = () => api.get<Account[]>("/api/accounts");
export const createAccount = (data: AccountCreate) => api.post<Account>("/api/accounts", data);
export const updateAccount = (id: string, data: AccountUpdate) => api.patch<Account>(`/api/accounts/${id}`, data);
export const deleteAccount = (id: string) => api.delete<void>(`/api/accounts/${id}`);
```

- [ ] **Step 2: Crear `apps/desktop/src/lib/api/categories.ts`**

```typescript
import { api } from "./client";
import type { Category } from "@/lib/types";

export interface CategoryCreate {
  name: string;
  type: string;
  parent_id?: string;
  icon?: string;
  color?: string;
}

export const fetchCategories = () => api.get<Category[]>("/api/categories");
export const createCategory = (data: CategoryCreate) => api.post<Category>("/api/categories", data);
```

- [ ] **Step 3: Crear `apps/desktop/src/lib/api/transactions.ts`**

```typescript
import { api } from "./client";
import type { Transaction } from "@/lib/types";

export interface TransactionCreate {
  account_id: string;
  category_id?: string;
  date: string;
  description: string;
  amount: string;
  currency?: string;
  type: string;
  notes?: string;
}

export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  from_date?: string;
  to_date?: string;
  type?: string;
}

export const fetchTransactions = (filters?: TransactionFilters) => {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  }
  const qs = params.toString();
  return api.get<Transaction[]>(`/api/transactions${qs ? `?${qs}` : ""}`);
};

export const createTransaction = (data: TransactionCreate) =>
  api.post<Transaction>("/api/transactions", data);

export const deleteTransaction = (id: string) =>
  api.delete<void>(`/api/transactions/${id}`);
```

- [ ] **Step 4: Crear `apps/desktop/src/lib/api/dashboard.ts`**

```typescript
import { api } from "./client";
import type { DashboardOverview } from "@/lib/types";

export interface CategorySpending {
  category_id: string | null;
  category: string;
  amount: string;
  percentage: number;
}

export interface SpendingData {
  month: string;
  total_expense: string;
  total_income: string;
  by_category: CategorySpending[];
}

export const fetchOverview = () => api.get<DashboardOverview>("/api/dashboard/overview");
export const fetchSpending = (month: string) =>
  api.get<SpendingData>(`/api/dashboard/spending?month=${month}`);
```

- [ ] **Step 5: Crear `apps/desktop/src/lib/api/settings.ts`**

```typescript
import { api } from "./client";

export interface AppSetting {
  id: string;
  key: string;
  value_json: string;
  created_at: string;
  updated_at: string;
}

export const fetchSettings = () => api.get<AppSetting[]>("/api/settings");
export const updateSetting = (key: string, value_json: string) =>
  api.patch<AppSetting>(`/api/settings/${key}`, { value_json });
```

- [ ] **Step 6: Crear `apps/desktop/src/lib/formatters/currency.ts`**

```typescript
export function formatCurrency(amount: string | number, currency = "EUR"): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatPercent(ratio: number): string {
  return new Intl.NumberFormat("es-ES", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(ratio);
}

export function formatNumber(amount: string | number): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
}
```

- [ ] **Step 7: Crear `apps/desktop/src/lib/hooks/useAccounts.ts`**

```typescript
import { useState, useEffect, useCallback } from "react";
import { fetchAccounts, createAccount, updateAccount, deleteAccount, type AccountCreate, type AccountUpdate } from "@/lib/api/accounts";
import type { Account } from "@/lib/types";

export function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAccounts(await fetchAccounts());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar cuentas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = async (data: AccountCreate) => {
    const account = await createAccount(data);
    setAccounts(prev => [...prev, account]);
    return account;
  };

  const update = async (id: string, data: AccountUpdate) => {
    const account = await updateAccount(id, data);
    setAccounts(prev => prev.map(a => a.id === id ? account : a));
    return account;
  };

  const remove = async (id: string) => {
    await deleteAccount(id);
    setAccounts(prev => prev.filter(a => a.id !== id));
  };

  return { accounts, loading, error, reload: load, add, update, remove };
}
```

- [ ] **Step 8: Crear `apps/desktop/src/lib/hooks/useCategories.ts`**

```typescript
import { useState, useEffect } from "react";
import { fetchCategories } from "@/lib/api/categories";
import type { Category } from "@/lib/types";

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const byId = (id: string) => categories.find(c => c.id === id);

  return { categories, loading, byId };
}
```

- [ ] **Step 9: Crear `apps/desktop/src/lib/hooks/useTransactions.ts`**

```typescript
import { useState, useEffect, useCallback } from "react";
import { fetchTransactions, createTransaction, deleteTransaction, type TransactionCreate, type TransactionFilters } from "@/lib/api/transactions";
import type { Transaction } from "@/lib/types";

export function useTransactions(filters?: TransactionFilters) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTransactions(await fetchTransactions(filters));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar movimientos");
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => { load(); }, [load]);

  const add = async (data: TransactionCreate) => {
    const tx = await createTransaction(data);
    setTransactions(prev => [tx, ...prev]);
    return tx;
  };

  const remove = async (id: string) => {
    await deleteTransaction(id);
    setTransactions(prev => prev.filter(t => t.id !== id));
  };

  return { transactions, loading, error, reload: load, add, remove };
}
```

- [ ] **Step 10: Crear `apps/desktop/src/lib/hooks/useDashboard.ts`**

```typescript
import { useState, useEffect } from "react";
import { fetchOverview, fetchSpending, type SpendingData } from "@/lib/api/dashboard";
import type { DashboardOverview } from "@/lib/types";

export function useOverview() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}

export function useSpending(month: string) {
  const [data, setData] = useState<SpendingData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSpending(month)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [month]);

  return { data, loading };
}
```

- [ ] **Step 11: Verificar TypeScript compila sin errores**

```bash
cd d:/FinancialAgent/AI-Financial-OS/apps/desktop
npx tsc --noEmit
```

Esperado: sin errores.

- [ ] **Step 12: Commit**

```bash
git add apps/desktop/src/lib/
git commit -m "feat: frontend API layer, formatters and data hooks"
```

---

## Task 8: Shared UI Components

**Files:**
- Create: `apps/desktop/src/components/ui/MetricCard.tsx`
- Create: `apps/desktop/src/components/ui/EmptyState.tsx`
- Create: `apps/desktop/src/components/ui/TypeBadge.tsx`
- Create: `apps/desktop/src/components/ui/Spinner.tsx`

**Interfaces:**
- Produces: `<MetricCard label trend value delta/>`, `<EmptyState icon title description action/>`, `<TypeBadge type/>`, `<Spinner />`

- [ ] **Step 1: Crear `apps/desktop/src/components/ui/Spinner.tsx`**

```tsx
export default function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`h-5 w-5 animate-spin rounded-full border-2 border-hairline-dark border-t-primary ${className}`}
    />
  );
}
```

- [ ] **Step 2: Crear `apps/desktop/src/components/ui/MetricCard.tsx`**

```tsx
interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaPositive?: boolean;
  sublabel?: string;
}

export default function MetricCard({ label, value, delta, deltaPositive, sublabel }: MetricCardProps) {
  return (
    <div className="bg-surface-card rounded-md p-xl border border-hairline-dark">
      <p className="text-caption text-stone uppercase tracking-widest mb-xs">{label}</p>
      <p className="text-heading-md text-on-dark">{value}</p>
      {delta && (
        <p className={`text-caption mt-xs ${deltaPositive ? "text-accent-teal" : "text-accent-danger"}`}>
          {delta}
        </p>
      )}
      {sublabel && <p className="text-caption text-stone mt-xs">{sublabel}</p>}
    </div>
  );
}
```

- [ ] **Step 3: Crear `apps/desktop/src/components/ui/EmptyState.tsx`**

```tsx
interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-3xl text-center">
      <p className="text-heading-sm text-on-dark-mute">{title}</p>
      <p className="text-body-sm text-stone mt-xs max-w-xs">{description}</p>
      {action && <div className="mt-xl">{action}</div>}
    </div>
  );
}
```

- [ ] **Step 4: Crear `apps/desktop/src/components/ui/TypeBadge.tsx`**

```tsx
const TYPE_STYLES: Record<string, string> = {
  income: "bg-accent-teal/10 text-accent-teal",
  expense: "bg-accent-danger/10 text-accent-danger",
  transfer: "bg-primary/10 text-primary",
  investment: "bg-accent-warning/10 text-accent-warning",
};

const TYPE_LABELS: Record<string, string> = {
  income: "Ingreso",
  expense: "Gasto",
  transfer: "Transferencia",
  investment: "Inversión",
};

export default function TypeBadge({ type }: { type: string }) {
  return (
    <span className={`inline-block rounded-sm px-xs py-[2px] text-caption font-medium ${TYPE_STYLES[type] ?? "bg-surface-elevated text-stone"}`}>
      {TYPE_LABELS[type] ?? type}
    </span>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/components/ui/
git commit -m "feat: shared UI components (MetricCard, EmptyState, TypeBadge, Spinner)"
```

---

## Task 9: Overview Page

**Files:**
- Modify: `apps/desktop/src/features/overview/OverviewPage.tsx`

**Interfaces:**
- Consumes: `useOverview` de `@/lib/hooks/useDashboard`, `formatCurrency`, `formatPercent` de `@/lib/formatters/currency`, `MetricCard` de `@/components/ui/MetricCard`, `Spinner` de `@/components/ui/Spinner`

- [ ] **Step 1: Implementar `apps/desktop/src/features/overview/OverviewPage.tsx`**

```tsx
import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useOverview } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

export default function OverviewPage() {
  const { data, loading } = useOverview();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner />
      </div>
    );
  }

  const d = data ?? {
    net_worth: "0",
    liquidity: "0",
    investments: "0",
    monthly_income: "0",
    monthly_expense: "0",
    monthly_savings: "0",
    savings_rate: 0,
    currency: "EUR",
  };

  const savings = parseFloat(d.monthly_savings);

  return (
    <div className="p-2xl space-y-xl">
      <div>
        <h1 className="text-display-lg text-on-dark">Resumen</h1>
        <p className="text-body-sm text-stone mt-xs">Tu situación financiera actual</p>
      </div>

      <div className="grid grid-cols-3 gap-lg">
        <MetricCard label="Patrimonio neto" value={formatCurrency(d.net_worth)} />
        <MetricCard label="Liquidez" value={formatCurrency(d.liquidity)} />
        <MetricCard label="Inversiones" value={formatCurrency(d.investments)} />
      </div>

      <div className="grid grid-cols-3 gap-lg">
        <MetricCard label="Ingresos del mes" value={formatCurrency(d.monthly_income)} deltaPositive />
        <MetricCard label="Gastos del mes" value={formatCurrency(d.monthly_expense)} />
        <MetricCard
          label="Ahorro del mes"
          value={formatCurrency(d.monthly_savings)}
          delta={`Tasa de ahorro: ${formatPercent(d.savings_rate)}`}
          deltaPositive={savings >= 0}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar en la app que la pantalla Resumen muestra las métricas**

Con backend y frontend corriendo:
- Navegar a `/` (Resumen)
- Sin datos: todos los valores deben mostrar `0,00 €`
- Sin errores en consola

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/features/overview/
git commit -m "feat: overview page with financial metrics"
```

---

## Task 10: Accounts Page

**Files:**
- Modify: `apps/desktop/src/features/accounts/AccountsPage.tsx`

**Interfaces:**
- Consumes: `useAccounts` de `@/lib/hooks/useAccounts`, `formatCurrency` de `@/lib/formatters/currency`, `EmptyState`, `Spinner`, `TypeBadge`

- [ ] **Step 1: Implementar `apps/desktop/src/features/accounts/AccountsPage.tsx`**

```tsx
import { useState } from "react";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { formatCurrency } from "@/lib/formatters/currency";
import type { AccountCreate } from "@/lib/api/accounts";

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  cash: "Efectivo", bank: "Banco", broker: "Broker",
  savings: "Ahorros", investment: "Inversión", mortgage: "Hipoteca", other: "Otro",
};

export default function AccountsPage() {
  const { accounts, loading, add, remove } = useAccounts();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AccountCreate>({ name: "", type: "bank", currency: "EUR", current_balance: "0.00" });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await add(form);
      setShowForm(false);
      setForm({ name: "", type: "bank", currency: "EUR", current_balance: "0.00" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><Spinner /></div>;

  return (
    <div className="p-2xl space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Cuentas</h1>
          <p className="text-body-sm text-stone mt-xs">{accounts.length} cuenta{accounts.length !== 1 ? "s" : ""}</p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors"
        >
          Nueva cuenta
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-surface-card border border-hairline-dark rounded-md p-xl space-y-lg">
          <h2 className="text-heading-sm text-on-dark">Nueva cuenta</h2>
          <div className="grid grid-cols-2 gap-lg">
            <div className="space-y-xs">
              <label className="text-caption text-stone">Nombre</label>
              <input
                required
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Ej. BBVA"
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Tipo</label>
              <select
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.type}
                onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
              >
                {Object.entries(ACCOUNT_TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Saldo inicial</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.current_balance}
                onChange={e => setForm(f => ({ ...f, current_balance: e.target.value }))}
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Institución</label>
              <input
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.institution ?? ""}
                onChange={e => setForm(f => ({ ...f, institution: e.target.value }))}
                placeholder="Opcional"
              />
            </div>
          </div>
          <div className="flex gap-sm justify-end">
            <button type="button" onClick={() => setShowForm(false)} className="px-lg py-sm text-stone text-body-sm hover:text-on-dark transition-colors">Cancelar</button>
            <button type="submit" disabled={saving} className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright disabled:opacity-50 transition-colors">
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      )}

      {accounts.length === 0 ? (
        <EmptyState
          title="Sin cuentas"
          description="Añade tu primera cuenta para empezar a registrar movimientos."
          action={<button onClick={() => setShowForm(true)} className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors">Añadir cuenta</button>}
        />
      ) : (
        <div className="space-y-sm">
          {accounts.map(account => (
            <div key={account.id} className="bg-surface-card border border-hairline-dark rounded-md p-xl flex items-center justify-between">
              <div>
                <p className="text-body-md text-on-dark">{account.name}</p>
                <p className="text-caption text-stone mt-xs">{ACCOUNT_TYPE_LABELS[account.type] ?? account.type}{account.institution ? ` · ${account.institution}` : ""}</p>
              </div>
              <div className="flex items-center gap-xl">
                <p className="text-heading-sm text-on-dark">{formatCurrency(account.current_balance, account.currency)}</p>
                <button onClick={() => remove(account.id)} className="text-stone hover:text-accent-danger text-caption transition-colors">Eliminar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar en la app**

- Navegar a `/accounts`
- Estado vacío visible con botón "Añadir cuenta"
- Crear una cuenta → aparece en la lista con saldo formateado
- Eliminar cuenta → desaparece de la lista

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/features/accounts/
git commit -m "feat: accounts page with CRUD UI"
```

---

## Task 11: Transactions Page

**Files:**
- Modify: `apps/desktop/src/features/transactions/TransactionsPage.tsx`

**Interfaces:**
- Consumes: `useTransactions` de `@/lib/hooks/useTransactions`, `useAccounts`, `useCategories`, `formatCurrency`, `TypeBadge`, `EmptyState`, `Spinner`

- [ ] **Step 1: Implementar `apps/desktop/src/features/transactions/TransactionsPage.tsx`**

```tsx
import { useState } from "react";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";
import TypeBadge from "@/components/ui/TypeBadge";
import { useTransactions } from "@/lib/hooks/useTransactions";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useCategories } from "@/lib/hooks/useCategories";
import { formatCurrency } from "@/lib/formatters/currency";
import type { TransactionCreate } from "@/lib/api/transactions";

export default function TransactionsPage() {
  const [filters, setFilters] = useState<{ type?: string; from_date?: string; to_date?: string }>({});
  const { transactions, loading, add, remove } = useTransactions(filters);
  const { accounts } = useAccounts();
  const { categories } = useCategories();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TransactionCreate>({
    account_id: "", category_id: "", date: new Date().toISOString().slice(0, 10),
    description: "", amount: "", currency: "EUR", type: "expense",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await add({ ...form, category_id: form.category_id || undefined });
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><Spinner /></div>;

  const getCategoryName = (id: string | null) => id ? (categories.find(c => c.id === id)?.name ?? "—") : "—";
  const getAccountName = (id: string) => accounts.find(a => a.id === id)?.name ?? id;

  return (
    <div className="p-2xl space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Movimientos</h1>
          <p className="text-body-sm text-stone mt-xs">{transactions.length} movimiento{transactions.length !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={() => setShowForm(v => !v)} className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors">
          Nuevo movimiento
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-sm">
        {["", "income", "expense", "transfer", "investment"].map(t => (
          <button
            key={t}
            onClick={() => setFilters(f => ({ ...f, type: t || undefined }))}
            className={`px-md py-xs text-caption rounded-sm transition-colors ${filters.type === (t || undefined) ? "bg-surface-elevated text-on-dark" : "text-stone hover:text-on-dark"}`}
          >
            {t === "" ? "Todos" : t === "income" ? "Ingresos" : t === "expense" ? "Gastos" : t === "transfer" ? "Transferencias" : "Inversiones"}
          </button>
        ))}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-surface-card border border-hairline-dark rounded-md p-xl space-y-lg">
          <h2 className="text-heading-sm text-on-dark">Nuevo movimiento</h2>
          <div className="grid grid-cols-2 gap-lg">
            <div className="space-y-xs">
              <label className="text-caption text-stone">Descripción</label>
              <input required className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Ej. Mercadona" />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Importe</label>
              <input required type="number" step="0.01" className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="Ej. -42.30" />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Tipo</label>
              <select className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                <option value="expense">Gasto</option>
                <option value="income">Ingreso</option>
                <option value="transfer">Transferencia</option>
                <option value="investment">Inversión</option>
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Fecha</label>
              <input required type="date" className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Cuenta</label>
              <select required className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.account_id} onChange={e => setForm(f => ({ ...f, account_id: e.target.value }))}>
                <option value="">Seleccionar cuenta</option>
                {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Categoría</label>
              <select className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
                <option value="">Sin categoría</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-sm justify-end">
            <button type="button" onClick={() => setShowForm(false)} className="px-lg py-sm text-stone text-body-sm hover:text-on-dark transition-colors">Cancelar</button>
            <button type="submit" disabled={saving} className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright disabled:opacity-50 transition-colors">
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      )}

      {transactions.length === 0 ? (
        <EmptyState title="Sin movimientos" description="Añade movimientos manuales o importa un CSV." action={<button onClick={() => setShowForm(true)} className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors">Añadir movimiento</button>} />
      ) : (
        <div className="bg-surface-card border border-hairline-dark rounded-md overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-hairline-dark">
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Fecha</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Descripción</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Cuenta</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Categoría</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Tipo</th>
                <th className="text-right px-xl py-md text-caption text-stone font-medium">Importe</th>
                <th className="px-xl py-md" />
              </tr>
            </thead>
            <tbody>
              {transactions.map(tx => {
                const amount = parseFloat(tx.amount);
                return (
                  <tr key={tx.id} className="border-b border-divider-soft hover:bg-surface-elevated/30 transition-colors">
                    <td className="px-xl py-md text-body-sm text-stone">{tx.date}</td>
                    <td className="px-xl py-md text-body-sm text-on-dark">{tx.description}</td>
                    <td className="px-xl py-md text-body-sm text-stone">{getAccountName(tx.account_id)}</td>
                    <td className="px-xl py-md text-body-sm text-stone">{getCategoryName(tx.category_id)}</td>
                    <td className="px-xl py-md"><TypeBadge type={tx.type} /></td>
                    <td className={`px-xl py-md text-right text-body-sm font-medium ${amount >= 0 ? "text-accent-teal" : "text-on-dark"}`}>
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                    <td className="px-xl py-md">
                      <button onClick={() => remove(tx.id)} className="text-stone hover:text-accent-danger text-caption transition-colors">Eliminar</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar en la app**

- Estado vacío con botón de añadir
- Formulario con cuentas y categorías del backend en los selects
- Crear movimiento → aparece en tabla
- Filtros por tipo funcionan
- Eliminar movimiento → desaparece

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/features/transactions/
git commit -m "feat: transactions page with table, filters and CRUD"
```

---

## Task 12: Spending Page

**Files:**
- Modify: `apps/desktop/src/features/spending/SpendingPage.tsx`

**Interfaces:**
- Consumes: `useSpending` de `@/lib/hooks/useDashboard`, `formatCurrency`, `formatPercent`, `Spinner`, `EmptyState`
- Consumes: `PieChart`, `Pie`, `Cell`, `Tooltip`, `Legend` de `recharts`

- [ ] **Step 1: Implementar `apps/desktop/src/features/spending/SpendingPage.tsx`**

```tsx
import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import Spinner from "@/components/ui/Spinner";
import MetricCard from "@/components/ui/MetricCard";
import EmptyState from "@/components/ui/EmptyState";
import { useSpending } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

const CHART_COLORS = ["#494fdf","#00a87e","#ec7e00","#e23b4a","#b09000","#8d969e","#4f55f1","#505a63"];

function getCurrentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export default function SpendingPage() {
  const [month, setMonth] = useState(getCurrentMonth);
  const { data, loading } = useSpending(month);

  const prevMonth = () => {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m - 2, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };
  const nextMonth = () => {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  if (loading) return <div className="flex justify-center items-center h-64"><Spinner /></div>;

  const hasCategoryData = data && data.by_category.length > 0;
  const chartData = data?.by_category.map(c => ({ name: c.category, value: parseFloat(c.amount) })) ?? [];

  return (
    <div className="p-2xl space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Gastos</h1>
          <p className="text-body-sm text-stone mt-xs">Análisis de gastos mensual</p>
        </div>
        <div className="flex items-center gap-md">
          <button onClick={prevMonth} className="text-stone hover:text-on-dark text-heading-sm transition-colors">‹</button>
          <span className="text-body-md text-on-dark w-24 text-center">{month}</span>
          <button onClick={nextMonth} className="text-stone hover:text-on-dark text-heading-sm transition-colors">›</button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-lg">
        <MetricCard label="Gasto total" value={formatCurrency(data?.total_expense ?? "0")} />
        <MetricCard label="Ingreso total" value={formatCurrency(data?.total_income ?? "0")} deltaPositive />
      </div>

      {!hasCategoryData ? (
        <EmptyState title="Sin datos" description="No hay gastos registrados para este mes." />
      ) : (
        <div className="grid grid-cols-2 gap-xl">
          <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
            <h2 className="text-heading-sm text-on-dark mb-xl">Por categoría</h2>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} paddingAngle={2}>
                  {chartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{ background: "#1e2124", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
            <h2 className="text-heading-sm text-on-dark mb-xl">Desglose</h2>
            <div className="space-y-sm">
              {data?.by_category.map((cat, i) => (
                <div key={cat.category_id ?? cat.category} className="flex items-center justify-between">
                  <div className="flex items-center gap-sm">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="text-body-sm text-on-dark">{cat.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-body-sm text-on-dark">{formatCurrency(cat.amount)}</span>
                    <span className="text-caption text-stone ml-sm">{formatPercent(cat.percentage)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar en la app**

- Navegar a `/spending`
- Sin datos: métricas en cero + EmptyState
- Con movimientos de tipo expense: gráfica de tarta y desglose por categoría
- Navegación de mes anterior/siguiente funciona

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/features/spending/
git commit -m "feat: spending page with pie chart and category breakdown"
```

---

## Task 13: Settings Page

**Files:**
- Modify: `apps/desktop/src/features/settings/SettingsPage.tsx`

**Interfaces:**
- Consumes: `fetchSettings`, `updateSetting` de `@/lib/api/settings`, `Spinner`

- [ ] **Step 1: Implementar `apps/desktop/src/features/settings/SettingsPage.tsx`**

```tsx
import { useState, useEffect } from "react";
import Spinner from "@/components/ui/Spinner";
import { fetchSettings, updateSetting, type AppSetting } from "@/lib/api/settings";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings().then(setSettings).finally(() => setLoading(false));
  }, []);

  const getValue = (key: string) => {
    const s = settings.find(s => s.key === key);
    if (!s) return "";
    try { return JSON.parse(s.value_json); } catch { return s.value_json; }
  };

  const handleUpdate = async (key: string, value: string) => {
    setSaving(key);
    try {
      const updated = await updateSetting(key, JSON.stringify(value));
      setSettings(prev => prev.map(s => s.key === key ? updated : s));
    } finally {
      setSaving(null);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><Spinner /></div>;

  return (
    <div className="p-2xl space-y-xl max-w-2xl">
      <div>
        <h1 className="text-display-lg text-on-dark">Ajustes</h1>
        <p className="text-body-sm text-stone mt-xs">Configuración de la aplicación</p>
      </div>

      <div className="bg-surface-card border border-hairline-dark rounded-md divide-y divide-hairline-dark">
        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Idioma</p>
            <p className="text-caption text-stone mt-xs">Idioma de la interfaz</p>
          </div>
          <select
            className="bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
            value={getValue("app.language")}
            onChange={e => handleUpdate("app.language", e.target.value)}
            disabled={saving === "app.language"}
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
        </div>

        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Moneda</p>
            <p className="text-caption text-stone mt-xs">Moneda predeterminada</p>
          </div>
          <select
            className="bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
            value={getValue("app.currency")}
            onChange={e => handleUpdate("app.currency", e.target.value)}
            disabled={saving === "app.currency"}
          >
            <option value="EUR">EUR — Euro</option>
            <option value="USD">USD — Dólar</option>
            <option value="GBP">GBP — Libra</option>
          </select>
        </div>

        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Tema</p>
            <p className="text-caption text-stone mt-xs">Modo visual de la aplicación</p>
          </div>
          <span className="text-body-sm text-stone">Dark Premium</span>
        </div>
      </div>

      <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
        <p className="text-heading-sm text-on-dark mb-xs">Asistente IA</p>
        <p className="text-body-sm text-stone">Disponible en Fase 6. Preparado para Ollama y LM Studio.</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar en la app**

- Navegar a `/settings`
- Settings cargados del backend (idioma: es, moneda: EUR)
- Cambiar idioma o moneda → actualiza en backend (verificar con curl)

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/features/settings/
git commit -m "feat: settings page with language and currency configuration"
```

---

## Self-Review

### Spec coverage check

| Requirement (Fase 1 Roadmap) | Task que lo cubre |
|---|---|
| CRUD de cuentas | Task 2 (backend) + Task 10 (frontend) |
| CRUD de categorías | Task 3 (backend) + Task 7 hooks |
| CRUD de movimientos | Task 4 (backend) + Task 11 (frontend) |
| Modelo ingresos/gastos | Task 4 (amount positivo/negativo) |
| Cálculo de patrimonio | Task 5 (GET /api/dashboard/overview) |
| Cálculo de cashflow mensual | Task 5 (monthly_income, monthly_expense) |
| Dashboard Overview | Task 5 + Task 9 |
| Dashboard Spending | Task 5 + Task 12 |
| Estados vacíos | Task 8 (EmptyState) usado en Tasks 10, 11, 12 |
| Datos mock opcionales | Task 3 seed 15 categorías, Task 6 seed settings |
| Pantalla Settings | Task 6 (backend) + Task 13 (frontend) |

### Placeholder scan: ninguno detectado.

### Type consistency

- `AccountCreate` definido en Task 7 Step 1, usado en Task 10 ✓
- `TransactionCreate` definido en Task 7 Step 3, usado en Task 11 ✓
- `useOverview()` retorna `{ data: DashboardOverview | null, loading: boolean }`, consumido en Task 9 ✓
- `useSpending(month)` retorna `{ data: SpendingData | null, loading: boolean }`, consumido en Task 12 ✓
- `formatCurrency(amount, currency?)` definido en Task 7 Step 6, firma usada consistentemente ✓
