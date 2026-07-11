import calendar
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.investment import Holding
from app.models.transaction import Transaction
from app.modules.dashboard.schemas import (
    CategorySpending,
    CategorySpendingDetailOut,
    CategoryTransaction,
    OverviewOut,
    SpendingOut,
    SpendingYearsOut,
)

router = APIRouter()


def _period_filter(month: str | None, year: int | None) -> tuple[str, str, int]:
    if year is not None:
        period_prefix = str(year)
        days = 366 if calendar.isleap(year) else 365
        return period_prefix, "year", days
    period_prefix = month or datetime.now(timezone.utc).strftime("%Y-%m")
    year_number, month_number = (int(part) for part in period_prefix.split("-"))
    return period_prefix, "month", calendar.monthrange(year_number, month_number)[1]


def _to_eur(amount: Decimal, currency: str | None, rates: dict[str, float | None]) -> Decimal:
    currency = (currency or "EUR").upper()
    if currency == "EUR" or not amount:
        return amount
    if currency not in rates:
        from app.modules.investments.price_coverage_audit import fetch_fx_rate

        rates[currency] = fetch_fx_rate(currency)[0]
    rate = rates[currency]
    # ponytail: sin tipo de cambio disponible se suma sin convertir (comportamiento previo)
    if not rate:
        return amount
    return (amount / Decimal(str(rate))).quantize(Decimal("0.01"))


@router.get("/overview", response_model=OverviewOut)
def get_overview(db: Session = Depends(get_db)) -> OverviewOut:
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712

    rates: dict[str, float | None] = {}
    balances = {a.id: _to_eur(a.current_balance, a.currency, rates) for a in accounts}
    liquidity = sum(
        (balances[a.id] for a in accounts if a.type in ("cash", "bank", "savings")),
        Decimal("0"),
    )
    # Valoración de cartera (market_value ya está en EUR, igual que /investments/summary)
    portfolio_value = sum(
        (h.market_value for h in db.query(Holding).all() if h.market_value is not None),
        Decimal("0"),
    )
    investments = (
        sum((balances[a.id] for a in accounts if a.type in ("broker", "investment")), Decimal("0"))
        + portfolio_value
    )
    net_worth = sum(balances.values(), Decimal("0")) + portfolio_value

    month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    month_txs = (
        db.query(Transaction)
        .filter(
            Transaction.date.like(f"{month_prefix}%"),
            Transaction.analytics_scope == "personal",
        )
        .all()
    )

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


@router.get("/spending/monthly")
def get_spending_monthly(
    months: int = Query(12, ge=1, le=36),
    year: int | None = Query(None, ge=1900, le=2200, description="Si se indica, devuelve enero-diciembre de ese año"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Serie mensual de ingreso/gasto/ahorro para la tendencia de Gastos."""
    if year is not None:
        prefixes = [f"{year}-{m:02d}" for m in range(1, 13)]
    else:
        now = datetime.now(timezone.utc)
        prefixes = []
        y, month = now.year, now.month
        for _ in range(months):
            prefixes.append(f"{y}-{month:02d}")
            month -= 1
            if month == 0:
                y, month = y - 1, 12
        prefixes.reverse()

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.date >= f"{prefixes[0]}-01",
            Transaction.date <= f"{prefixes[-1]}-31",
            Transaction.analytics_scope == "personal",
        )
        .all()
    )
    by_month: dict[str, dict[str, Decimal]] = {p: {"income": Decimal("0"), "expense": Decimal("0")} for p in prefixes}
    for t in txs:
        prefix = str(t.date)[:7]
        if prefix not in by_month:
            continue
        if t.type == "income":
            by_month[prefix]["income"] += t.amount
        elif t.type == "expense":
            by_month[prefix]["expense"] += abs(t.amount)

    return [
        {
            "month": p,
            "income": str(v["income"]),
            "expense": str(v["expense"]),
            "savings": str(v["income"] - v["expense"]),
        }
        for p, v in by_month.items()
    ]


@router.get("/spending/years", response_model=SpendingYearsOut)
def get_spending_years(db: Session = Depends(get_db)) -> SpendingYearsOut:
    rows = db.query(Transaction.date).all()
    years = sorted({int(str(row[0])[:4]) for row in rows if row[0] and len(str(row[0])) >= 4}, reverse=True)
    return SpendingYearsOut(years=years)


@router.get("/spending", response_model=SpendingOut)
def get_spending(
    month: str | None = Query(None, description="YYYY-MM"),
    year: int | None = Query(None, description="YYYY"),
    db: Session = Depends(get_db),
) -> SpendingOut:
    period_prefix, period_type, days_in_period = _period_filter(month, year)

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.date.like(f"{period_prefix}%"),
            Transaction.analytics_scope == "personal",
        )
        .all()
    )

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
        pct = float(amount / total_expense * 100) if total_expense > 0 else 0.0
        result.append(
            CategorySpending(
                category_id=cat_id,
                category=cat_name,
                amount=str(amount),
                percentage=round(pct, 1),
            )
        )

    net_savings = total_income - total_expense
    savings_rate = float(net_savings / total_income * 100) if total_income > 0 else 0.0

    return SpendingOut(
        month=period_prefix,
        period_type=period_type,
        total_expense=str(total_expense),
        total_income=str(total_income),
        net_savings=str(net_savings),
        savings_rate=round(savings_rate, 1),
        transaction_count=len(txs),
        average_daily_expense=str((total_expense / Decimal(days_in_period)).quantize(Decimal("0.01"))),
        by_category=result,
    )


@router.get("/spending/category-detail", response_model=CategorySpendingDetailOut)
def get_spending_category_detail(
    category_id: str | None = Query(None),
    month: str | None = Query(None, description="YYYY-MM"),
    year: int | None = Query(None, description="YYYY"),
    db: Session = Depends(get_db),
) -> CategorySpendingDetailOut:
    period_prefix, period_type, _days_in_period = _period_filter(month, year)
    period_txs = (
        db.query(Transaction)
        .filter(
            Transaction.date.like(f"{period_prefix}%"),
            Transaction.analytics_scope == "personal",
        )
        .all()
    )
    expense_txs = [t for t in period_txs if t.type == "expense"]
    total_expense = abs(sum((t.amount for t in expense_txs), Decimal("0")))

    detail_txs = [t for t in expense_txs if t.category_id == category_id]
    total = abs(sum((t.amount for t in detail_txs), Decimal("0")))
    percentage = float(total / total_expense * 100) if total_expense > 0 else 0.0
    average = total / Decimal(len(detail_txs)) if detail_txs else Decimal("0")

    categories = {c.id: c for c in db.query(Category).all()}
    accounts = {a.id: a for a in db.query(Account).all()}
    category_name = categories[category_id].name if category_id and category_id in categories else "Sin categoria"

    return CategorySpendingDetailOut(
        category_id=category_id,
        category=category_name,
        period=period_prefix,
        period_type=period_type,
        total=str(total.quantize(Decimal("0.01"))),
        percentage=round(percentage, 1),
        transaction_count=len(detail_txs),
        average_transaction=str(average.quantize(Decimal("0.01"))),
        transactions=[
            CategoryTransaction(
                id=t.id,
                date=t.date,
                description=t.description,
                account_name=accounts[t.account_id].name if t.account_id in accounts else "Cuenta desconocida",
                amount=str(t.amount),
                currency=t.currency,
                category=category_name,
                type=t.type,
                notes=t.notes,
            )
            for t in sorted(detail_txs, key=lambda tx: tx.date, reverse=True)
        ],
    )
