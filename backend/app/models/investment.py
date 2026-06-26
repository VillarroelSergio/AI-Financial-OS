import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InvestmentAsset(Base):
    __tablename__ = "investment_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    asset_type: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    price_source: Mapped[str] = mapped_column(String, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(String, ForeignKey("investment_assets.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    current_price_currency: Mapped[str] = mapped_column(String, default="EUR")
    current_price_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    inception_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InvestmentOperation(Base):
    __tablename__ = "investment_operations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(String, ForeignKey("investment_assets.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    operation_type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    source: Mapped[str] = mapped_column(String, default="manual")
    import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
