import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
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


class HoldingValueHistory(Base):
    __tablename__ = "holding_value_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    holding_id: Mapped[str] = mapped_column(String, ForeignKey("holdings.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    source: Mapped[str] = mapped_column(String, default="manual")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FundValuationSnapshot(Base):
    """Valor manual de un fondo en una fecha (modal 'Actualizar valor', INV-3).

    Un snapshot por (holding, date). Fuente de la gráfica de evolución. Spec §2.2.
    Rendimiento en fecha t = market_value(t) − contributed_total(t).
    """
    __tablename__ = "fund_valuation_snapshots"
    __table_args__ = (
        UniqueConstraint("holding_id", "date", name="uq_fund_snapshot_holding_date"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    holding_id: Mapped[str] = mapped_column(String, ForeignKey("holdings.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # valor total de la posición
    contributed_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)  # aportado acumulado
    units: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)  # nº participaciones (opcional, peso)
    nav: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)  # valor liquidativo por participación
    currency: Mapped[str] = mapped_column(String, default="EUR")
    source: Mapped[str] = mapped_column(String, default="manual")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SavingsAccountConfig(Base):
    """Configuración del motor de intereses de una cuenta remunerada (INV-4). Spec §2.2.

    Una config por Account (type=savings). El tipo puede ser el de la facilidad de
    depósito del BCE, fijo o manual, con ajuste spread_bps.
    """
    __tablename__ = "savings_account_configs"
    __table_args__ = (
        UniqueConstraint("account_id", name="uq_savings_config_account"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    opened_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    rate_source: Mapped[str] = mapped_column(String, default="ecb_deposit_facility")  # ecb_deposit_facility | fixed | manual
    fixed_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)  # % anual (solo fixed)
    spread_bps: Mapped[int] = mapped_column(Integer, default=0)  # puntos básicos sobre la referencia
    compounding: Mapped[str] = mapped_column(String, default="monthly")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReferenceRateObservation(Base):
    """Histórico de un tipo de referencia macro cacheado en el SQLite de la app.

    Poblado por reference_rate_service desde ECB SDMX (fallback FRED). El motor de
    intereses (INV-4) lee de aquí y funciona offline una vez ingestado.
    """
    __tablename__ = "reference_rate_observations"
    __table_args__ = (
        UniqueConstraint("rate_id", "effective_date", name="uq_reference_rate_date"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rate_id: Mapped[str] = mapped_column(String, nullable=False)  # p.ej. ECB_DFR
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)  # % anual
    source: Mapped[str] = mapped_column(String, default="ecb")
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
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
