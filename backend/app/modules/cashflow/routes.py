from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction

router = APIRouter()


class MonthForecast(BaseModel):
    month: str
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


def _monthly_avg(db: Session, tx_type: str, months: int = 3) -> Decimal:
    """Compute average monthly amount for the last `months` months using string-prefix matching."""
    today = date.today()
    totals: list[Decimal] = []
    for i in range(months):
        # Walk back month by month
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        month_prefix = f"{y}-{m:02d}"
        total = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == tx_type,
            Transaction.date.like(f"{month_prefix}%"),
        ).scalar()
        totals.append(Decimal(total or 0))
    if not totals:
        return Decimal(0)
    return sum(totals) / Decimal(len(totals))


def _next_occurrences(rt: RecurringTransaction, from_date: date, months: int) -> list[date]:
    """Return all occurrence dates for a recurring transaction within the next `months` months."""
    end_date = date(
        from_date.year + (from_date.month + months - 1) // 12,
        (from_date.month + months - 1) % 12 + 1,
        1,
    )
    occurrences: list[date] = []
    current = rt.next_date
    if isinstance(current, str):
        current = date.fromisoformat(current)

    freq = rt.frequency
    if freq == "monthly":
        # Generate monthly dates starting from next_date
        d = current
        while d < end_date:
            if d >= from_date:
                occurrences.append(d)
            # Advance by one month
            m = d.month + 1
            y = d.year
            if m > 12:
                m = 1
                y += 1
            try:
                d = d.replace(year=y, month=m)
            except ValueError:
                # Handle e.g. day=31 in a month with fewer days
                import calendar
                last_day = calendar.monthrange(y, m)[1]
                d = d.replace(year=y, month=m, day=last_day)
    elif freq == "weekly":
        d = current
        while d < end_date:
            if d >= from_date:
                occurrences.append(d)
            d += timedelta(weeks=1)
    elif freq == "yearly":
        d = current
        while d < end_date:
            if d >= from_date:
                occurrences.append(d)
            try:
                d = d.replace(year=d.year + 1)
            except ValueError:
                d = d.replace(year=d.year + 1, day=28)
    else:
        # Unknown frequency — just use next_date if in range
        if from_date <= current < end_date:
            occurrences.append(current)

    return occurrences


@router.get("/forecast", response_model=CashflowForecast)
def get_cashflow_forecast(
    months: int = Query(default=3, ge=1, le=12),
    db: Session = Depends(get_db),
) -> CashflowForecast:
    """
    Return a month-by-month cashflow forecast for the next `months` months.

    Each month entry contains:
    - month: "YYYY-MM"
    - projected_income: sum of recurring income occurrences + historical avg if no recurring
    - projected_expenses: sum of recurring expense occurrences + historical avg if no recurring
    - projected_balance: projected_income - projected_expenses
    - historical_avg_income: 3-month historical average income
    - historical_avg_expenses: 3-month historical average expenses
    - recurring_income: sum of recurring income for the month
    - recurring_expenses: sum of recurring expenses for the month
    """
    today = date.today()

    # Historical monthly averages (fallback when no recurring transactions)
    avg_income = _monthly_avg(db, "income")
    avg_expense = _monthly_avg(db, "expense")

    # Load all active recurring transactions
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.active == True  # noqa: E712
    ).all()

    month_forecasts: list[MonthForecast] = []
    for i in range(months):
        m = today.month + i
        y = today.year
        while m > 12:
            m -= 12
            y += 1
        month_label = f"{y}-{m:02d}"
        month_start = date(y, m, 1)

        # Sum recurring transactions for this month
        rec_income = Decimal(0)
        rec_expense = Decimal(0)
        has_recurring = len(recurring) > 0

        for rt in recurring:
            occurrences = _next_occurrences(rt, month_start, 1)
            amount = Decimal(rt.amount or 0)
            if rt.type == "income":
                rec_income += amount * len(occurrences)
            elif rt.type == "expense":
                rec_expense += amount * len(occurrences)

        projected_income = float(rec_income if has_recurring else avg_income)
        projected_expenses = float(rec_expense if has_recurring else avg_expense)

        month_forecasts.append(MonthForecast(
            month=month_label,
            projected_income=projected_income,
            projected_expenses=projected_expenses,
            projected_balance=projected_income - projected_expenses,
            historical_avg_income=float(avg_income),
            historical_avg_expenses=float(avg_expense),
            recurring_income=float(rec_income),
            recurring_expenses=float(rec_expense),
        ))

    return CashflowForecast(
        generated_at=datetime.now(timezone.utc),
        months=month_forecasts,
    )
