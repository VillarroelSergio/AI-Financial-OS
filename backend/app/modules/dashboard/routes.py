from datetime import datetime, timezone
from decimal import Decimal

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

    net_worth = sum((a.current_balance for a in accounts), Decimal("0"))
    liquidity = sum(
        (a.current_balance for a in accounts if a.type in ("cash", "bank", "savings")),
        Decimal("0"),
    )
    investments = sum(
        (a.current_balance for a in accounts if a.type in ("broker", "investment")),
        Decimal("0"),
    )

    month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    month_txs = db.query(Transaction).filter(Transaction.date.like(f"{month_prefix}%")).all()

    monthly_income = sum((t.amount for t in month_txs if t.type == "income"), Decimal("0"))
    monthly_expense = abs(sum((t.amount for t in month_txs if t.type == "expense"), Decimal("0")))
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

    total_income = sum((t.amount for t in txs if t.type == "income"), Decimal("0"))
    expense_txs = [t for t in txs if t.type == "expense"]
    total_expense = abs(sum((t.amount for t in expense_txs), Decimal("0")))

    by_cat: dict[str | None, Decimal] = {}
    for t in expense_txs:
        by_cat[t.category_id] = by_cat.get(t.category_id, Decimal("0")) + abs(t.amount)

    categories = {c.id: c for c in db.query(Category).all()}
    result: list[CategorySpending] = []
    for cat_id, amount in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        cat_name = categories[cat_id].name if cat_id and cat_id in categories else "Sin categoría"
        pct = float(amount / total_expense) if total_expense > 0 else 0.0
        result.append(
            CategorySpending(
                category_id=cat_id,
                category=cat_name,
                amount=str(amount),
                percentage=round(pct, 3),
            )
        )

    return SpendingOut(
        month=month,
        total_expense=str(total_expense),
        total_income=str(total_income),
        by_category=result,
    )
