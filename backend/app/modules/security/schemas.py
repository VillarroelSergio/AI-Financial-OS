from datetime import datetime

from pydantic import BaseModel


class BackupOut(BaseModel):
    filename: str
    path: str
    size_bytes: int
    created_at: datetime


class IntegrityCheckOut(BaseModel):
    status: str
    database_ok: bool
    tables: list[str]
    issues: list[str]


class SecurityStatusOut(BaseModel):
    app_env: str
    database_path: str
    backups_available: int
    encryption_ready: bool
    demo_data_policy: str
