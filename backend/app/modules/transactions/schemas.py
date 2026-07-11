from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class TransactionCreate(BaseModel):
    account_id: str
    category_id: str | None = None
    date: str
    description: str
    amount: Decimal
    currency: str = "EUR"
    type: str
    notes: str | None = None


class ScopeUpdate(BaseModel):
    scope: str  # personal | excluded | pending
    linked_transaction_id: str | None = None


class CurrencyReassign(BaseModel):
    from_currency: str
    to_currency: str
    preview: bool = True


class TransactionUpdate(BaseModel):
    category_id: str | None = None
    date: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    notes: str | None = None


class TransactionOut(BaseModel):
    id: str
    account_id: str
    account_name: str | None = None
    category_id: str | None
    date: str
    description: str
    amount: Decimal
    currency: str
    converted_amount: Decimal | None
    converted_currency: str | None
    type: str
    source: str
    source_name: str | None
    external_id: str | None
    import_batch_id: str | None
    analytics_scope: str = "personal"
    linked_transaction_id: str | None = None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return str(v)

    @field_serializer("converted_amount")
    def serialize_converted_amount(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None
