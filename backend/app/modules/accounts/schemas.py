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
    cash_balance_eur: Decimal = Decimal("0.00")
    portfolio_value_eur: Decimal = Decimal("0.00")
    total_value_eur: Decimal = Decimal("0.00")
    position_count: int = 0

    model_config = {"from_attributes": True}

    @field_serializer(
        "current_balance",
        "cash_balance_eur",
        "portfolio_value_eur",
        "total_value_eur",
    )
    def serialize_balance(self, v: Decimal) -> str:
        return str(v)
