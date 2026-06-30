from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
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

    # Build the YYYY-MM prefix for string-based date filtering
    month_prefix = f"{year}-{mon:02d}"

    budgets = db.query(Budget).filter(Budget.active == True).all()
    result: list[BudgetComparisonItem] = []

    for budget in budgets:
        cat = db.get(Category, budget.category_id)
        cat_name = cat.name if cat else budget.category_id

        # Transaction.date is stored as a String (ISO format), use LIKE for month filtering
        actual_q = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.category_id == budget.category_id,
                Transaction.type == "expense",
                Transaction.date.like(f"{month_prefix}%"),
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
