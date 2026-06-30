from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class HouseholdBillCreate(BaseModel):
    provider: str
    service_type: str
    period_start: date
    period_end: date
    amount: Decimal
    currency: str = "EUR"
    category_id: str | None = None
    is_recurring: bool = True
    due_date: date | None = None
    paid_at: date | None = None
    notes: str | None = None


class HouseholdBillUpdate(BaseModel):
    provider: str | None = None
    service_type: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    amount: Decimal | None = None
    currency: str | None = None
    category_id: str | None = None
    is_recurring: bool | None = None
    due_date: date | None = None
    paid_at: date | None = None
    notes: str | None = None


class HouseholdBillOut(HouseholdBillCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class HouseholdBillSummaryItem(BaseModel):
    service_type: str
    provider: str
    bills_count: int
    last_amount: float
    previous_amount: float | None
    change_pct: float | None
    average_amount: float
    next_estimate: float
    anomaly: bool
    latest_period: str


class HouseholdBillSummary(BaseModel):
    generated_at: datetime
    total_monthly_estimate: float
    items: list[HouseholdBillSummaryItem]
