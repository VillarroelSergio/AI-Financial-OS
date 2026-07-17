"""Controlled personal finance tools for the AI assistant."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.modules.accounts.valuation_service import build_current_valuation
from app.modules.ai.tools.registry import ToolDefinition, tool_registry


def _now_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def _get_net_worth(db: Session, **_: Any) -> dict[str, Any]:
    valuation = build_current_valuation(db)
    return {
        "net_worth": round(float(valuation.net_worth), 2),
        "currency": "EUR",
        "by_type": {key: round(float(value), 2) for key, value in valuation.by_type.items()},
        "accounts_count": len(valuation.accounts),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "quality_score": 1.0,
        "sources": [{"type": "personal_accounts", "provider": "local_db"}],
    }


async def _get_monthly_summary(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    month = month or _now_month()
    if len(month) != 7 or "-" not in month:
        return {"error": "month must be YYYY-MM", "status": "error"}
    txs = db.query(Transaction).filter(Transaction.date.like(f"{month}%")).all()
    income = sum(float(t.amount) for t in txs if t.type == "income")
    expense = abs(sum(float(t.amount) for t in txs if t.type == "expense"))
    savings = income - expense
    savings_rate = round(savings / income, 3) if income > 0 else 0.0
    return {
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "savings": round(savings, 2),
        "savings_rate": savings_rate,
        "transaction_count": len(txs),
        "currency": "EUR",
        "quality_score": 1.0,
        "sources": [{"type": "transactions", "provider": "local_db", "period": month}],
    }


async def _get_spending_by_category(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    month = month or _now_month()
    if len(month) != 7 or "-" not in month:
        return {"error": "month must be YYYY-MM", "status": "error"}
    txs = db.query(Transaction).filter(
        Transaction.date.like(f"{month}%"), Transaction.type == "expense"
    ).all()
    categories = {c.id: c.name for c in db.query(Category).all()}
    by_cat: dict[str, float] = {}
    for t in txs:
        cat_name = categories.get(t.category_id or "", "Sin categoría")
        by_cat[cat_name] = by_cat.get(cat_name, 0.0) + abs(float(t.amount))
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
    return {
        "month": month,
        "categories": [{"name": k, "amount": round(v, 2)} for k, v in sorted_cats],
        "total": round(sum(by_cat.values()), 2),
        "currency": "EUR",
        "quality_score": 1.0,
        "sources": [{"type": "transactions", "provider": "local_db", "period": month}],
    }


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
    if "error" in a or "error" in b:
        return {"error": "Invalid months", "status": "error"}

    return {
        "period_a": a,
        "period_b": b,
        "delta_income": round(float(a["income"]) - float(b["income"]), 2),
        "delta_expense": round(float(a["expense"]) - float(b["expense"]), 2),
        "delta_savings": round(float(a["savings"]) - float(b["savings"]), 2),
        "quality_score": 1.0,
        "sources": [{"type": "transactions", "provider": "local_db"}],
    }


async def _get_savings_rate(db: Session, month: str | None = None, **_: Any) -> dict[str, Any]:
    summary = await _get_monthly_summary(db=db, month=month)
    if "error" in summary:
        return summary
    return {
        "month": summary["month"],
        "savings_rate": summary["savings_rate"],
        "savings": summary["savings"],
        "income": summary["income"],
        "quality_score": 1.0,
        "sources": summary["sources"],
    }


async def _get_goal_progress(db: Session, **_: Any) -> dict[str, Any]:
    goals = db.query(Goal).all()
    if not goals:
        return {"status": "not_available", "message": "No goals configured", "goals": []}
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
            "currency": g.currency or "EUR",
            "deadline": str(g.deadline) if g.deadline else None,
        })
    return {
        "goals": result,
        "quality_score": 1.0,
        "sources": [{"type": "goals", "provider": "local_db"}],
    }


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
