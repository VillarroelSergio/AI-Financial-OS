from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InsightSeverity(str, Enum):
    positive = "positive"
    info = "info"
    warning = "warning"
    critical = "critical"


class InsightType(str, Enum):
    spending_anomaly = "spending_anomaly"
    monthly_comparison = "monthly_comparison"
    savings_rate = "savings_rate"
    cashflow_alert = "cashflow_alert"
    net_worth_change = "net_worth_change"
    investment_allocation = "investment_allocation"
    goal_progress = "goal_progress"
    market_context = "market_context"
    macro_context = "macro_context"
    data_quality = "data_quality"


class DataStatus(str, Enum):
    complete = "complete"
    partial = "partial"
    insufficient = "insufficient"
    empty = "empty"
    error = "error"


class InsightMetricOut(BaseModel):
    label: str
    value: float
    unit: str = ""


class InsightSourceOut(BaseModel):
    type: str
    label: str
    period: str | None = None
    source: str = "local_db"
    updated_at: str | None = None


class InsightActionOut(BaseModel):
    label: str
    target: str
    params: dict[str, Any] = Field(default_factory=dict)


class InsightOut(BaseModel):
    id: str
    type: InsightType
    severity: InsightSeverity
    title: str
    summary: str
    detail: str = ""
    period: str
    impact_area: str
    status: str = "active"
    confidence: float
    priority: float
    data_status: DataStatus
    primary_metric: InsightMetricOut | None = None
    secondary_metrics: list[InsightMetricOut] = Field(default_factory=list)
    sources: list[InsightSourceOut] = Field(default_factory=list)
    actions: list[InsightActionOut] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InsightsSummaryCountOut(BaseModel):
    total: int
    positive: int
    info: int
    warning: int
    critical: int
    partial: int
    insufficient: int


class InsightsSummaryOut(BaseModel):
    period: str
    generated_at: str
    data_status: DataStatus
    insights: list[InsightOut]
    summary: InsightsSummaryCountOut


class NetWorthChangeOut(BaseModel):
    amount: float
    percentage: float


class MonthlyReviewOut(BaseModel):
    period: str
    headline: str
    summary: str
    income: float
    expenses: float
    savings: float
    savings_rate: float
    net_worth_change: NetWorthChangeOut | None = None
    top_positive: list[InsightOut] = Field(default_factory=list)
    top_warnings: list[InsightOut] = Field(default_factory=list)
    top_changes: list[InsightOut] = Field(default_factory=list)
    data_status: DataStatus
    sources: list[InsightSourceOut] = Field(default_factory=list)


class AnomaliesOut(BaseModel):
    period: str
    baseline_months: int
    data_status: DataStatus
    anomalies: list[InsightOut]


class DismissInsightOut(BaseModel):
    insight_id: str
    dismissed_at: str
