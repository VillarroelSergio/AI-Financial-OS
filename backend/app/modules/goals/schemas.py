from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_serializer

GoalType = Literal["emergency_fund", "housing", "investment", "savings", "custom"]
GoalPriority = Literal["low", "medium", "high"]
GoalStatus = Literal["active", "completed", "paused"]


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: GoalType = "custom"
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    target_date: date | None = None
    monthly_contribution: Decimal | None = Field(default=None, ge=0)
    priority: GoalPriority = "medium"


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: GoalType | None = None
    target_amount: Decimal | None = Field(default=None, gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)
    target_date: date | None = None
    monthly_contribution: Decimal | None = Field(default=None, ge=0)
    priority: GoalPriority | None = None
    status: GoalStatus | None = None


class GoalOut(BaseModel):
    id: str
    name: str
    type: GoalType
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None
    monthly_contribution: Decimal | None
    priority: GoalPriority
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("target_amount", "current_amount", "monthly_contribution")
    def serialize_amount(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


# ── Simulation schemas ────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    inflation_rate: float = Field(default=0.03, ge=0.0, le=0.5)
    max_months: int = Field(default=360, ge=12, le=360)


class MonthlyDataPointOut(BaseModel):
    month: int
    label: str
    conservative: float
    base: float
    optimistic: float


class ScenarioProjectionOut(BaseModel):
    scenario: str
    label: str
    color: str
    annual_growth_rate: float
    months_to_target: Optional[int]
    projected_date: Optional[str]
    achievable_by_target_date: Optional[bool]
    final_amount: float


class SimulationResultOut(BaseModel):
    goal_id: str
    current_amount: float
    target_amount: float
    monthly_contribution: float
    monthly_contribution_needed: Optional[float]
    inflation_rate: float
    inflation_adjusted_target: float
    monthly_data: list[MonthlyDataPointOut]
    scenarios: list[ScenarioProjectionOut]
    target_date: Optional[str]
    generated_at: str


class GoalProgressOut(BaseModel):
    goal_id: str
    progress_pct: float          # 0–100
    remaining: float             # target - current
    on_track: Optional[bool]     # None when no target_date
    base_months_to_target: Optional[int]
    base_projected_date: Optional[str]
