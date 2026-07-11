import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NetWorthSnapshot(Base):
    """Foto mensual del patrimonio (D2/D7). Idempotente por mes: DELETE+INSERT."""

    __tablename__ = "net_worth_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    month: Mapped[str] = mapped_column(String, nullable=False, index=True)  # YYYY-MM
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    net_worth: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # por clase de activo
    data_state: Mapped[str] = mapped_column(String, default="complete")  # complete | partial
    missing_items_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String, default="EUR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
