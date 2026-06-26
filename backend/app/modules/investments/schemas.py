from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer

# ── Assets ────────────────────────────────────────────────────────────────────

class InvestmentAssetCreate(BaseModel):
    name: str
    ticker: str | None = None
    isin: str | None = None
    asset_type: str
    currency: str = "EUR"
    region: str | None = None
    sector: str | None = None
    price_source: str = "manual"


class InvestmentAssetUpdate(BaseModel):
    name: str | None = None
    ticker: str | None = None
    isin: str | None = None
    currency: str | None = None
    region: str | None = None
    sector: str | None = None
    price_source: str | None = None


class InvestmentAssetOut(BaseModel):
    id: str
    name: str
    ticker: str | None
    isin: str | None
    asset_type: str
    currency: str
    region: str | None
    sector: str | None
    price_source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Holdings ──────────────────────────────────────────────────────────────────

class HoldingCreate(BaseModel):
    account_id: str
    asset_id: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal | None = None
    current_price_currency: str = "EUR"
    market_value: Decimal | None = None
    interest_rate: Decimal | None = None
    inception_date: date | None = None


class HoldingUpdate(BaseModel):
    quantity: Decimal | None = None
    average_price: Decimal | None = None
    current_price: Decimal | None = None
    current_price_currency: str | None = None
    interest_rate: Decimal | None = None
    inception_date: date | None = None


class HoldingOut(BaseModel):
    id: str
    account_id: str
    asset_id: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal | None
    current_price_currency: str
    current_price_updated_at: datetime | None
    market_value: Decimal | None
    interest_rate: Decimal | None
    inception_date: date | None
    created_at: datetime
    updated_at: datetime
    asset: InvestmentAssetOut
    cost_basis: Decimal
    return_absolute: Decimal | None
    return_percent: float | None
    accrued_interest: Decimal | None

    model_config = {"from_attributes": True}

    @field_serializer("quantity", "average_price", "cost_basis")
    def serialize_decimal_required(self, v: Decimal) -> str:
        return str(v)

    @field_serializer("current_price", "interest_rate", "return_absolute", "accrued_interest", "market_value")
    def serialize_decimal_optional(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


# ── Operations ────────────────────────────────────────────────────────────────

class InvestmentOperationCreate(BaseModel):
    account_id: str
    asset_id: str
    date: date
    operation_type: str
    quantity: Decimal | None = None
    price: Decimal | None = None
    amount: Decimal
    currency: str = "EUR"
    fees: Decimal = Decimal("0.00")


class InvestmentOperationOut(BaseModel):
    id: str
    account_id: str
    asset_id: str
    date: date
    operation_type: str
    quantity: Decimal | None
    price: Decimal | None
    amount: Decimal
    currency: str
    fees: Decimal
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount", "fees")
    def serialize_decimal_required(self, v: Decimal) -> str:
        return str(v)

    @field_serializer("quantity", "price")
    def serialize_decimal_optional(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


# ── Summary ───────────────────────────────────────────────────────────────────

class AccountSummaryOut(BaseModel):
    account_id: str
    value: Decimal
    invested: Decimal

    @field_serializer("value", "invested")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


class InvestmentSummaryOut(BaseModel):
    total_value: Decimal
    total_invested: Decimal
    return_absolute: Decimal
    return_percent: float
    currency: str
    by_account: list[AccountSummaryOut]
    last_updated: datetime | None

    @field_serializer("total_value", "total_invested", "return_absolute")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


# ── Price refresh ─────────────────────────────────────────────────────────────

class PriceRefreshResultOut(BaseModel):
    updated: int
    failed: list[str]
    needs_manual_nav: list[str]
