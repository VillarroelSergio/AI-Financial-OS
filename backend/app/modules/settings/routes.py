from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.settings import AppSetting
from app.modules.settings.schemas import SettingOut, SettingUpdate

router = APIRouter()


@router.get("", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db)) -> list[AppSetting]:
    return db.query(AppSetting).all()


@router.patch("/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)) -> AppSetting:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Configuración no encontrada", "details": {}}},
        )
    setting.value_json = payload.value_json
    db.commit()
    db.refresh(setting)
    return setting
