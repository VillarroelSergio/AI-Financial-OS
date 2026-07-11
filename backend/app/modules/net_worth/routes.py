"""Endpoints de patrimonio (INS-4). Snapshots solo por acción explícita del usuario."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.net_worth import service
from app.modules.net_worth.schemas import (
    BalanceSheetOut,
    ReadinessOut,
    SnapshotCreate,
    SnapshotOut,
)

router = APIRouter()


def _default_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


@router.get("/balance-sheet", response_model=BalanceSheetOut)
def get_balance_sheet(
    month: str | None = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
) -> BalanceSheetOut:
    return service.build_balance_sheet(db, month or _default_month())


@router.get("/snapshots", response_model=list[SnapshotOut])
def get_snapshots(
    date_from: str | None = Query(None, alias="from", description="YYYY-MM"),
    date_to: str | None = Query(None, alias="to", description="YYYY-MM"),
    db: Session = Depends(get_db),
) -> list[SnapshotOut]:
    return service.list_snapshots(db, date_from, date_to)


@router.get("/snapshot-readiness", response_model=ReadinessOut)
def get_snapshot_readiness(
    month: str | None = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
) -> ReadinessOut:
    return service.evaluate_readiness(db, month or _default_month())


@router.post("/snapshots", response_model=SnapshotOut, status_code=201)
def post_snapshot(payload: SnapshotCreate, db: Session = Depends(get_db)) -> SnapshotOut:
    try:
        return service.create_snapshot(db, payload.month, payload.force_partial)
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="Faltan elementos por actualizar. Cierra como parcial o completa la checklist.",
        )
