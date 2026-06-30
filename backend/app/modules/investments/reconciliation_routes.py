"""Endpoint for Portfolio Reconciliation report."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.investment import Holding, InvestmentAsset
from app.modules.investments.reconciliation_service import (
    compute_reconciliation,
)
from app.modules.investments.routes import _enrich_holding

router = APIRouter()


class CompletenessOut(BaseModel):
    confirmed_pct: float
    estimated_pct: float
    manual_pct: float
    no_price_pct: float


class ReconciliationHoldingOut(BaseModel):
    holding_id: str
    display_name: str
    ticker: str | None
    quality_state: str
    value_eur: float
    weight_pct: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    currency: str
    requires_fx: bool
    broker: str
    sector: str | None
    asset_type: str


class WeightItemOut(BaseModel):
    key: str
    weight_pct: float


class ConcentrationAlertOut(BaseModel):
    type: str
    key: str
    weight_pct: float
    threshold_pct: float


class ReconciliationReportOut(BaseModel):
    generated_at: datetime
    portfolio_value_eur: float
    completeness: CompletenessOut
    holdings: list[ReconciliationHoldingOut]
    weights_by: dict[str, list[WeightItemOut]]
    concentration_alerts: list[ConcentrationAlertOut]


@router.get("/reconciliation", response_model=ReconciliationReportOut)
def get_reconciliation(db: Session = Depends(get_db)) -> ReconciliationReportOut:
    try:
        rows = (
            db.query(Holding, InvestmentAsset)
            .join(InvestmentAsset, Holding.asset_id == InvestmentAsset.id)
            .all()
        )
        account_ids = {h.account_id for h, _ in rows}
        account_names = {
            a.id: a.name
            for a in db.query(Account).filter(Account.id.in_(account_ids)).all()
        } if account_ids else {}
        enriched = [_enrich_holding(h, asset, account_names.get(h.account_id)) for h, asset in rows]
        report = compute_reconciliation(enriched)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al calcular calidad de cartera: {exc}") from exc

    return ReconciliationReportOut(
        generated_at=report.generated_at,
        portfolio_value_eur=report.portfolio_value_eur,
        completeness=CompletenessOut(
            confirmed_pct=report.completeness.confirmed_pct,
            estimated_pct=report.completeness.estimated_pct,
            manual_pct=report.completeness.manual_pct,
            no_price_pct=report.completeness.no_price_pct,
        ),
        holdings=[
            ReconciliationHoldingOut(
                holding_id=rh.holding_id,
                display_name=rh.display_name,
                ticker=rh.ticker,
                quality_state=rh.quality_state.value,
                value_eur=rh.value_eur,
                weight_pct=rh.weight_pct,
                unrealized_pnl=rh.unrealized_pnl,
                unrealized_pnl_pct=rh.unrealized_pnl_pct,
                currency=rh.currency,
                requires_fx=rh.requires_fx,
                broker=rh.broker,
                sector=rh.sector,
                asset_type=rh.asset_type,
            )
            for rh in report.holdings
        ],
        weights_by={
            dim: [WeightItemOut(key=w.key, weight_pct=w.weight_pct) for w in items]
            for dim, items in report.weights_by.items()
        },
        concentration_alerts=[
            ConcentrationAlertOut(
                type=a.type, key=a.key,
                weight_pct=a.weight_pct, threshold_pct=a.threshold_pct,
            )
            for a in report.concentration_alerts
        ],
    )
