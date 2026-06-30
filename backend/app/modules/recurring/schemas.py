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


class RecurringCandidate(BaseModel):
    id: str
    name: str
    description: str
    amount: Decimal
    amount_min: Decimal
    amount_max: Decimal
    currency: str
    type: str
    frequency: str
    next_date: date
    confidence: float
    transaction_count: int
    transaction_ids: list[str]
    category_id: str | None
    account_id: str | None
    evidence: list[str]
