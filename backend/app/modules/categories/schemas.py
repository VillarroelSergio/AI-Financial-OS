from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    type: str
    parent_id: str | None = None
    icon: str | None = None
    color: str | None = None


class CategoryOut(BaseModel):
    id: str
    name: str
    parent_id: str | None
    type: str
    icon: str | None
    color: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
