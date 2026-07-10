from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class AccountCreate(BaseModel):
    name: str
    type: str
    institution: str | None = None
    currency: str = "EUR"
    current_balance: Decimal = Decimal("0.00")
    is_liability: bool = False


class AccountUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    institution: str | None = None
    currency: str | None = None
    current_balance: Decimal | None = None
    is_active: bool | None = None
    is_liability: bool | None = None


class AccountOut(BaseModel):
    id: str
    name: str
    type: str
    institution: str | None
    currency: str
    current_balance: Decimal
    is_active: bool
    is_liability: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("current_balance")
    def serialize_balance(self, v: Decimal) -> str:
        return str(v)
