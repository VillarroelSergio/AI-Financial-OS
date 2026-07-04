"""Helpers compartidos entre engines y storage de financial_knowledge."""
import uuid
from datetime import datetime, timezone


def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)
