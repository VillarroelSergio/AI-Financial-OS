import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0)
    mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    import_batch_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
