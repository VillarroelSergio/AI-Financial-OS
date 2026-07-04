from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.security.schemas import BackupOut, IntegrityCheckOut, SecurityStatusOut
from app.modules.security.service import (
    create_backup,
    database_path,
    list_backups,
    run_integrity_check,
)

router = APIRouter()


@router.get("/status", response_model=SecurityStatusOut)
def security_status() -> SecurityStatusOut:
    return SecurityStatusOut(
        app_env=settings.APP_ENV,
        database_filename=database_path().name,
        backups_available=len(list_backups()),
        encryption_ready=True,
        demo_data_policy="demo data must be labeled and excluded from real totals",
    )


@router.get("/backups", response_model=list[BackupOut])
def backups() -> list[dict]:
    return list_backups()


@router.post("/backups", response_model=BackupOut, status_code=201)
def backup(db: Session = Depends(get_db)) -> dict:
    try:
        return create_backup(str(db.bind.url) if db.bind is not None else None)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/integrity", response_model=IntegrityCheckOut)
def integrity(db: Session = Depends(get_db)) -> dict:
    return run_integrity_check(db)
