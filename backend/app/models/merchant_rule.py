import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MerchantRule(Base):
    """Regla aprendida de una corrección manual: comercio → categoría.

    ponytail: match por descripción normalizada exacta; si los bancos añaden
    sufijos variables (nº de operación), pasar a match por prefijo de tokens.
    """

    __tablename__ = "merchant_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    category_id: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
