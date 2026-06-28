"""Controlled personal finance tools for the AI assistant."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.modules.ai.tools.envelope import fail, ok, source, utc_now
from app.modules.ai.tools.registry import ToolDefinition, tool_registry


def _now_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def _get_net_worth(db: Session, **_: Any) -> dict[str, Any]:
    try:
        accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
        net_worth = sum(float(a.current_balance) for a in accounts)
        by_type: dict[str, float] = {}
        for a in accounts:
            by_type[a.type] = by_type.get(a.type, 0.0) + float(a.current_balance)
        data = {
            "net_worth": round(net_worth, 2),
            "currency": "EUR",
            "by_type": by_type,
            "accounts_count": len(accounts),
            "observed_at": utc_now(),
        }
        return ok("get_net_worth", data, sources=[source(source_type="personal_accounts", provider="local_db", quality_score=1.0)])
    except Exception as exc:
        return fail("get_net_worth", "net worth not available", str(exc))


async def _get_monthly_summary(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    month = month or _now_month()
    if len(month) != 7 or "-" not in month:
        return fail("get_monthly_summary", "month must be YYYY-MM")
    txs = db.query(Transaction).filter(Transaction.date.like(f"{month}%")).all()
    income = sum(float(t.amount) for t in txs if t.type == "income")
    expense = abs(sum(float(t.amount) for t in txs if t.type == "expense"))
    savings = income - expense
    savings_rate = round(savings / income, 3) if income > 0 else 0.0
    data = {
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "savings": round(savings, 2),
        "savings_rate": savings_rate,
        "transaction_count": len(txs),
        "currency": "EUR",
    }
    return ok("get_monthly_summary", data, sources=[source(source_type="transactions", provider="local_db", observed_at=month, quality_score=1.0)])


async def _get_spending_by_category(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    month = month or _now_month()
    if len(month) != 7 or "-" not in month:
        return fail("get_spending_by_category", "month must be YYYY-MM")
    txs = db.query(Transaction).filter(
        Transaction.date.like(f"{month}%"), Transaction.type == "expense"
    ).all()
    categories = {c.id: c.name for c in db.query(Category).all()}
    by_cat: dict[str, float] = {}
    for t in txs:
        cat_name = categories.get(t.category_id or "", "Sin categoría")
        by_cat[cat_name] = by_cat.get(cat_name, 0.0) + abs(float(t.amount))
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
    data = {
        "month": month,
        "categories": [{"name": k, "amount": round(v, 2)} for k, v in sorted_cats],
        "total": round(sum(by_cat.values()), 2),
        "currency": "EUR",
    }
    return ok("get_spending_by_category", data, sources=[source(source_type="transactions", provider="local_db", observed_at=month, quality_score=1.0)])


async def _compare_periods(
    db: Session,
    month_a: str | None = None,
    month_b: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    if not month_a:
        month_a = now.strftime("%Y-%m")
    if not month_b:
        prev_month = now.month - 1
        prev_year = now.year if prev_month > 0 else now.year - 1
        prev_month = prev_month if prev_month > 0 else 12
        month_b = f"{prev_year}-{prev_month:02d}"

    async def _summary(m: str) -> dict[str, Any]:
        return await _get_monthly_summary(db=db, month=m)

    a = await _summary(month_a)
    b = await _summary(month_b)
    if not a.get("ok") or not b.get("ok"):
        return fail("compare_periods", "Invalid months")
    a_data = a["data"]
    b_data = b["data"]

    data = {
        "period_a": a_data,
        "period_b": b_data,
        "delta_income": round(float(a_data["income"]) - float(b_data["income"]), 2),
        "delta_expense": round(float(a_data["expense"]) - float(b_data["expense"]), 2),
        "delta_savings": round(float(a_data["savings"]) - float(b_data["savings"]), 2),
    }
    return ok("compare_periods", data, sources=(a.get("sources") or []) + (b.get("sources") or []), quality_score=1.0)


async def _get_savings_rate(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    summary = await _get_monthly_summary(db=db, month=month)
    if not summary.get("ok"):
        return summary
    data = summary["data"]
    return ok("get_savings_rate", {
        "month": data["month"],
        "savings_rate": data["savings_rate"],
        "savings": data["savings"],
        "income": data["income"],
    }, sources=summary.get("sources") or [], quality_score=summary.get("quality_score"))


async def _get_goal_progress(db: Session, **_: Any) -> dict[str, Any]:
    goals = db.query(Goal).all()
    if not goals:
        return ok("get_goal_progress", {"goals": [], "message": "No goals configured"}, warnings=["No goals configured"])
    result = []
    for g in goals:
        target = float(g.target_amount)
        current = float(g.current_amount or Decimal("0"))
        progress = round(current / target, 3) if target > 0 else 0.0
        result.append({
            "id": g.id,
            "name": g.name,
            "target_amount": target,
            "current_amount": current,
            "progress": progress,
            "currency": "EUR",
            "target_date": str(g.target_date) if g.target_date else None,
            "monthly_contribution": float(g.monthly_contribution) if g.monthly_contribution else None,
            "priority": g.priority,
            "status": g.status,
        })
    return ok("get_goal_progress", {"goals": result}, sources=[source(source_type="goals", provider="local_db", quality_score=1.0)])


# ── Registration ──────────────────────────────────────────────────────────────

tool_registry.register(ToolDefinition(
    name="get_net_worth",
    description="Returns current net worth and account balances breakdown.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_net_worth,
))

tool_registry.register(ToolDefinition(
    name="get_monthly_summary",
    description="Returns income, expenses, savings and savings rate for a given month.",
    input_schema={
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "YYYY-MM format. Defaults to current month."},
        },
    },
    handler=_get_monthly_summary,
))

tool_registry.register(ToolDefinition(
    name="get_spending_by_category",
    description="Returns expense breakdown by category for a given month.",
    input_schema={
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "YYYY-MM format. Defaults to current month."},
        },
    },
    handler=_get_spending_by_category,
))

tool_registry.register(ToolDefinition(
    name="compare_periods",
    description="Compares two months: income, expenses, savings. Defaults to current vs previous month.",
    input_schema={
        "type": "object",
        "properties": {
            "month_a": {"type": "string", "description": "YYYY-MM (default: current month)"},
            "month_b": {"type": "string", "description": "YYYY-MM (default: previous month)"},
        },
    },
    handler=_compare_periods,
))

tool_registry.register(ToolDefinition(
    name="get_savings_rate",
    description="Returns savings rate for a given month.",
    input_schema={
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "YYYY-MM format. Defaults to current month."},
        },
    },
    handler=_get_savings_rate,
))

tool_registry.register(ToolDefinition(
    name="get_goal_progress",
    description="Returns progress toward all configured financial goals.",
    input_schema={"type": "object", "properties": {}},
    handler=_get_goal_progress,
))
