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
