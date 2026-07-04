"""Market Intelligence API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut,
    BondSnapshotOut,
    ForexSnapshotOut,
    MacroSnapshotOut,
    MarketSnapshotOut,
    NewsSnapshotOut,
    PersonalImpactOut,
)

router = APIRouter()


@router.get("/personal-impact", response_model=PersonalImpactOut)
def get_personal_impact(db: Session = Depends(get_db)):
    from app.modules.market_intelligence.api.impact import compute_personal_impact
    return compute_personal_impact(db)


@router.get("/personal-economy")
def get_personal_economy(db: Session = Depends(get_db)) -> dict:
    """Cruce macro↔finanzas personales: inflación propia, salario real, Euríbor, fiscal."""
    from app.modules.market_intelligence.api.personal_economy import compute_personal_economy
    return compute_personal_economy(db)


@router.get("/ingest-status")
def ingest_status() -> dict:
    from app.modules.market_intelligence.ingestion.startup import get_ingest_status
    return get_ingest_status()


@router.get("/snapshot/macro", response_model=MacroSnapshotOut)
def get_macro_snapshot():
    return service.get_macro_snapshot()


@router.get("/snapshot/market", response_model=MarketSnapshotOut)
def get_market_snapshot():
    return service.get_market_snapshot()


@router.get("/snapshot/forex", response_model=ForexSnapshotOut)
def get_forex_snapshot():
    return service.get_forex_snapshot()


@router.get("/snapshot/bonds", response_model=BondSnapshotOut)
def get_bond_snapshot():
    return service.get_bond_snapshot()


@router.get("/snapshot/news", response_model=NewsSnapshotOut)
def get_news_snapshot(limit: int = Query(default=20, le=100)):
    return service.get_news_snapshot(limit=limit)


@router.get("/ai-datasheet", response_model=AiDatasheetOut)
def get_ai_datasheet(scope: str = Query(default="daily")):
    return service.get_ai_datasheet(scope=scope)
