import datetime as dt
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
    asset_type: str | None = None
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


class HoldingMerge(BaseModel):
    source_id: str
    target_id: str


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
    display_name: str
    symbol: str | None
    asset_type: str
    broker: str
    invested_amount: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    currency: str
    is_mock: bool
    quality_score: float
    warnings: list[str]

    model_config = {"from_attributes": True}

    @field_serializer("quantity", "average_price", "cost_basis")
    def serialize_decimal_required(self, v: Decimal) -> str:
        return str(v)

    @field_serializer(
        "current_price",
        "interest_rate",
        "return_absolute",
        "accrued_interest",
        "market_value",
        "invested_amount",
        "unrealized_pnl",
    )
    def serialize_decimal_optional(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


# ── Holding value history ─────────────────────────────────────────────────────

class HoldingValueHistoryCreate(BaseModel):
    price: Decimal
    currency: str = "EUR"
    recorded_at: datetime | None = None


class HoldingValueHistoryUpdate(BaseModel):
    price: Decimal | None = None
    recorded_at: datetime | None = None


class HoldingValueHistoryOut(BaseModel):
    id: str
    holding_id: str
    price: Decimal
    currency: str
    source: str
    recorded_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


# ── Fund valuation snapshots (INV-3) ──────────────────────────────────────────

class FundCreate(BaseModel):
    """Alta de fondo (spec §3): crea asset(fund) + holding + primer snapshot."""
    name: str
    account_id: str
    contributed: Decimal
    value: Decimal
    date: dt.date
    currency: str = "EUR"
    units: Decimal | None = None   # nº participaciones (opcional)
    nav: Decimal | None = None     # valor liquidativo por participación (opcional)


class FundSnapshotCreate(BaseModel):
    date: dt.date
    market_value: Decimal
    contributed_total: Decimal | None = None
    units: Decimal | None = None
    nav: Decimal | None = None
    currency: str = "EUR"
    note: str | None = None


class FundSnapshotUpdate(BaseModel):
    date: dt.date | None = None
    market_value: Decimal | None = None
    contributed_total: Decimal | None = None
    units: Decimal | None = None
    nav: Decimal | None = None
    note: str | None = None


class FundSnapshotOut(BaseModel):
    id: str
    holding_id: str
    date: dt.date
    market_value: Decimal
    contributed_total: Decimal | None
    units: Decimal | None
    nav: Decimal | None
    currency: str
    source: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("market_value")
    def serialize_value(self, v: Decimal) -> str:
        return str(v)

    @field_serializer("contributed_total", "units", "nav")
    def serialize_optional_decimal(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


# ── Savings accounts (INV-4) ──────────────────────────────────────────────────

class SavingsCreate(BaseModel):
    """Alta de cuenta remunerada (spec §3). account_id existente o new_account_name."""
    account_id: str | None = None
    new_account_name: str | None = None
    institution: str | None = None
    opened_at: date
    balance: Decimal
    rate_source: str = "ecb_deposit_facility"    # ecb_deposit_facility | fixed | manual
    fixed_rate: Decimal | None = None            # % anual (fixed | manual)
    spread_bps: int = 0


class SavingsConfigUpdate(BaseModel):
    opened_at: date | None = None
    rate_source: str | None = None
    fixed_rate: Decimal | None = None
    spread_bps: int | None = None


class SavingsConfigOut(BaseModel):
    id: str
    account_id: str
    opened_at: date | None
    rate_source: str
    fixed_rate: Decimal | None
    spread_bps: int
    compounding: str

    model_config = {"from_attributes": True}

    @field_serializer("fixed_rate")
    def serialize_rate(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


class SavingsMonthPointOut(BaseModel):
    month: str
    balance_start: Decimal
    annual_rate: Decimal
    interest: Decimal
    contributions: Decimal
    balance_end: Decimal

    @field_serializer("balance_start", "annual_rate", "interest", "contributions", "balance_end")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


class SavingsProjectionOut(BaseModel):
    points: list[SavingsMonthPointOut]
    total_interest: Decimal
    total_contributions: Decimal
    current_balance: Decimal
    current_rate: Decimal | None
    estimated: bool = False

    @field_serializer("total_interest", "total_contributions", "current_balance")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)

    @field_serializer("current_rate")
    def serialize_rate(self, v: Decimal | None) -> str | None:
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
    pending_valuation_count: int = 0
    pending_valuation_invested: Decimal = Decimal("0")

    @field_serializer("total_value", "total_invested", "return_absolute", "pending_valuation_invested")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


# ── Price refresh ─────────────────────────────────────────────────────────────

class PriceRefreshUpdatedOut(BaseModel):
    holding_id: str
    name: str
    symbol: str | None
    old_price: Decimal | None
    new_price: Decimal
    currency: str
    source: str

    @field_serializer("old_price", "new_price")
    def serialize_decimal_optional(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None


class PriceRefreshManualRequiredOut(BaseModel):
    holding_id: str
    name: str
    symbol: str | None
    asset_type: str
    reason: str


class PriceRefreshSkippedOut(BaseModel):
    holding_id: str
    name: str
    asset_type: str
    reason: str


class PriceRefreshResultOut(BaseModel):
    ok: bool = True
    updated: int
    failed: list[str]
    needs_manual_nav: list[str]
    updated_items: list[PriceRefreshUpdatedOut] = []
    manual_required: list[PriceRefreshManualRequiredOut] = []
    skipped: list[PriceRefreshSkippedOut] = []
    errors: list[str] = []
