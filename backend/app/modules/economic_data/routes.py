from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.economic_data import service
from app.modules.economic_data.schemas import (
    IndicatorOut,
    MacroSnapshotOut,
    PersonalImpactOut,
)

router = APIRouter()


@router.get("/snapshot", response_model=MacroSnapshotOut)
def get_snapshot():
    return service.get_snapshot()


@router.get("/indicators", response_model=list[IndicatorOut])
def list_indicators(
    region: str | None = Query(default=None),
    indicator: str | None = Query(default=None),
):
    return service.get_indicators(region=region, indicator=indicator)


@router.post("/refresh", response_model=MacroSnapshotOut)
def refresh_data():
    result = service.refresh_snapshot()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una actualización de datos económicos en curso",
        )
    return result


@router.get("/impact", response_model=PersonalImpactOut)
def get_personal_impact(db: Session = Depends(get_db)):
    return service.get_personal_impact(db)
