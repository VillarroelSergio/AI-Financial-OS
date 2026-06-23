from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.investment import InvestmentAsset
from app.modules.investments.schemas import (
    InvestmentAssetCreate, InvestmentAssetOut, InvestmentAssetUpdate,
)

router = APIRouter()


@router.get("/assets", response_model=list[InvestmentAssetOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(InvestmentAsset).all()


@router.post("/assets", response_model=InvestmentAssetOut, status_code=201)
def create_asset(payload: InvestmentAssetCreate, db: Session = Depends(get_db)):
    asset = InvestmentAsset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.patch("/assets/{asset_id}", response_model=InvestmentAssetOut)
def update_asset(asset_id: str, payload: InvestmentAssetUpdate, db: Session = Depends(get_db)):
    asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Activo no encontrado", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Activo no encontrado", "details": {}}},
        )
    db.delete(asset)
    db.commit()
