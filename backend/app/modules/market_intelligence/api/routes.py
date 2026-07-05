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


@router.get("/rates/ecb-deposit-facility")
def get_ecb_deposit_facility(
    from_: str | None = Query(default=None, alias="from"),
    db: Session = Depends(get_db),
) -> dict:
    """Histórico del tipo de facilidad de depósito del BCE (spec §3, interno).

    Sirve el cache de `ReferenceRateObservation`; si está vacío, ingesta primero."""
    from datetime import date

    from app.models.investment import ReferenceRateObservation
    from app.modules.investments.reference_rate_service import ECB_DFR, ingest_deposit_facility_history

    if db.query(ReferenceRateObservation).filter(ReferenceRateObservation.rate_id == ECB_DFR).count() == 0:
        try:
            ingest_deposit_facility_history(db)
        except Exception:  # noqa: BLE001 — sin red, se devuelve lo que haya (vacío)
            pass

    q = db.query(ReferenceRateObservation).filter(ReferenceRateObservation.rate_id == ECB_DFR)
    if from_:
        try:
            q = q.filter(ReferenceRateObservation.effective_date >= date.fromisoformat(from_))
        except ValueError:
            pass
    rows = q.order_by(ReferenceRateObservation.effective_date.asc()).all()
    return {
        "rate_id": ECB_DFR,
        "observations": [
            {"date": r.effective_date.isoformat(), "rate": str(r.rate), "source": r.source}
            for r in rows
        ],
    }


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
