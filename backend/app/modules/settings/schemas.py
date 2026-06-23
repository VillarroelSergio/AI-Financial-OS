from datetime import datetime

from pydantic import BaseModel


class SettingOut(BaseModel):
    id: str
    key: str
    value_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value_json: str
