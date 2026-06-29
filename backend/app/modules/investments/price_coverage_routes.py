"""Endpoints for Portfolio Price Coverage Audit."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.investments.price_coverage_audit import (
    DEFAULT_ASSETS,
    run_audit,
)

router = APIRouter()


# ── Pydantic response schemas ─────────────────────────────────────────────────

class TickerCandidateOut(BaseModel):
    ticker: str
    yfinance_symbol: str
    name: str
    exchange: str
    currency: str
    asset_type: str
    confidence: float


class AssetResolutionOut(BaseModel):
    asset_name: str
    candidates: list[TickerCandidateOut]
    selected: Optional[TickerCandidateOut]
    status: str


class CoverageAssetOut(BaseModel):
    asset_name: str
    selected_ticker: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    provider: Optional[str]
    price: Optional[float]
    price_currency: Optional[str]
    requires_fx_conversion: bool
    last_update: Optional[datetime]
    freshness_hours: Optional[float]
    from_cache: bool
    status: str
    confidence: float
    notes: list[str]
    # FX / EUR valuation
    fx_rate: Optional[float] = None
    fx_currency_pair: Optional[str] = None
    eur_price: Optional[float] = None
    fx_updated_at: Optional[datetime] = None


class AuditSummaryOut(BaseModel):
    total: int
    with_price: int
    eur_valued: int
    fx_pending: int
    ambiguous: int
    manual: int
    unavailable: int
    error: int


class AuditReportOut(BaseModel):
    generated_at: datetime
    summary: AuditSummaryOut
    assets: list[CoverageAssetOut]


class AuditRequestAsset(BaseModel):
    name: str


class AuditRequest(BaseModel):
    assets: list[AuditRequestAsset] = []
    force_refresh: bool = False


class ResolveRequest(BaseModel):
    asset_name: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/default-assets", response_model=list[str])
def get_default_assets() -> list[str]:
    return DEFAULT_ASSETS


@router.post("/audit", response_model=AuditReportOut)
def run_price_audit(body: AuditRequest) -> AuditReportOut:
    names = [a.name for a in body.assets] if body.assets else DEFAULT_ASSETS
    report = run_audit(names)
    return AuditReportOut(
        generated_at=report.generated_at,
        summary=AuditSummaryOut(**report.summary.__dict__),
        assets=[CoverageAssetOut(**r.__dict__) for r in report.assets],
    )


@router.post("/resolve", response_model=AssetResolutionOut)
def resolve_asset_endpoint(body: ResolveRequest) -> AssetResolutionOut:
    resolution = resolve_asset(body.asset_name)
    return AssetResolutionOut(
        asset_name=resolution.asset_name,
        candidates=[TickerCandidateOut(**c.__dict__) for c in resolution.candidates],
        selected=TickerCandidateOut(**resolution.selected.__dict__)
        if resolution.selected
        else None,
        status=resolution.status,
    )
