from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings


def database_path(url: str | None = None) -> Path:
    url = url or settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", "", 1)).resolve()
    parsed = urlparse(url)
    return Path(parsed.path).resolve()


def backup_dir() -> Path:
    path = database_path().parent / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup(source_url: str | None = None) -> dict:
    source = database_path(source_url)
    if not source.exists():
        raise FileNotFoundError(f"No existe la base de datos: {source}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir() / f"financial-{timestamp}.db"
    shutil.copy2(source, destination)
    stat = destination.stat()
    _prune_backups(keep=20)
    return {
        "filename": destination.name,
        "path": str(destination),
        "size_bytes": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
    }


def _prune_backups(keep: int) -> None:
    """Retiene los `keep` backups más recientes; el resto se borra."""
    paths = sorted(backup_dir().glob("financial-*.db"), reverse=True)
    for path in paths[keep:]:
        path.unlink(missing_ok=True)


def list_backups() -> list[dict]:
    backups = []
    for path in sorted(backup_dir().glob("financial-*.db"), reverse=True):
        stat = path.stat()
        backups.append(
            {
                "filename": path.name,
                "path": str(path),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            }
        )
    return backups


def run_integrity_check(db: Session) -> dict:
    issues: list[str] = []
    database_ok = True
    path = database_path(str(db.bind.url) if db.bind is not None else None)
    if path.exists():
        conn = sqlite3.connect(path)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            database_ok = bool(result and result[0] == "ok")
            if not database_ok:
                issues.append(f"sqlite_integrity_check={result[0] if result else 'empty'}")
        finally:
            conn.close()
    else:
        database_ok = False
        issues.append("database_file_missing")

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database_ok = False
        issues.append(f"sqlalchemy_connection_failed: {exc}")

    tables = sorted(inspect(db.bind).get_table_names()) if db.bind is not None else []
    required = {"accounts", "transactions", "categories", "documents", "document_chunks"}
    missing = sorted(required.difference(tables))
    issues.extend(f"missing_table:{table}" for table in missing)

    return {
        "status": "ok" if database_ok and not missing else "degraded",
        "database_ok": database_ok,
        "tables": tables,
        "issues": issues,
    }
