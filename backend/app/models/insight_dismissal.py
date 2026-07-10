from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InsightDismissal(Base):
    """Insight descartado por el usuario (D3: migra el JSON a SQLite).

    Se conserva `insight_id` como clave: los ids son deterministas por periodo
    (`insight_{period}_{type}`), así el descarte sobrevive a reinicios."""

    __tablename__ = "insight_dismissals"

    insight_id: Mapped[str] = mapped_column(String, primary_key=True)
    dismissed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
