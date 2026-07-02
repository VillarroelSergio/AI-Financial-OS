import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.insights import repository, service
from app.modules.insights.schemas import (
    AnomaliesOut,
    DismissInsightOut,
    InsightsSummaryOut,
    MonthlyReviewOut,
)

router = APIRouter()
_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def _validate_period(period: str | None) -> str | None:
    if period and not _PERIOD_RE.match(period):
        raise HTTPException(status_code=422, detail="period must be YYYY-MM")
    return period


@router.get("", response_model=InsightsSummaryOut)
def get_insights(
    period: str | None = Query(None),
    type: str | None = Query(None),
    severity: str | None = Query(None),
    impact_area: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    include_dismissed: bool = Query(False),
    db: Session = Depends(get_db),
) -> InsightsSummaryOut:
    _validate_period(period)
    return service.get_insights(db, period, type, severity, impact_area, limit, include_dismissed)


@router.get("/monthly-review", response_model=MonthlyReviewOut)
def get_monthly_review(
    period: str | None = Query(None),
    db: Session = Depends(get_db),
) -> MonthlyReviewOut:
    _validate_period(period)
    return service.get_monthly_review(db, period)


@router.get("/anomalies", response_model=AnomaliesOut)
def get_anomalies(
    period: str | None = Query(None),
    baseline_months: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
) -> AnomaliesOut:
    _validate_period(period)
    return service.get_anomalies(db, period, baseline_months)


@router.get("/data-quality", response_model=InsightsSummaryOut)
def get_data_quality(
    period: str | None = Query(None),
    db: Session = Depends(get_db),
) -> InsightsSummaryOut:
    _validate_period(period)
    return service.get_data_quality(db, period)


@router.post("/refresh", response_model=InsightsSummaryOut)
def refresh_insights(
    period: str | None = Query(None),
    db: Session = Depends(get_db),
) -> InsightsSummaryOut:
    _validate_period(period)
    return service.get_insights(db, period)


@router.post("/{insight_id}/dismiss", response_model=DismissInsightOut)
def dismiss_insight(insight_id: str) -> DismissInsightOut:
    if not insight_id or len(insight_id) > 200:
        raise HTTPException(status_code=422, detail="Invalid insight_id")
    dismissed_at = repository.dismiss(insight_id)
    return DismissInsightOut(insight_id=insight_id, dismissed_at=dismissed_at)
