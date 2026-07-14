"""Market Intelligence API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut,
    BondSnapshotOut,
    EconomyOverviewOut,
    ForexSnapshotOut,
    InstrumentHistoryOut,
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

    ECO-3: solo lectura. Un GET nunca ingesta (regla "leer nunca ingesta"); la ingesta
    programada del módulo de inversiones rellena `ReferenceRateObservation`. Si aún no hay
    dato, se devuelve `status: no_data` en vez de disparar red en el request."""
    from datetime import date

    from app.models.investment import ReferenceRateObservation
    from app.modules.investments.reference_rate_service import ECB_DFR

    q = db.query(ReferenceRateObservation).filter(ReferenceRateObservation.rate_id == ECB_DFR)
    if from_:
        try:
            q = q.filter(ReferenceRateObservation.effective_date >= date.fromisoformat(from_))
        except ValueError:
            pass
    rows = q.order_by(ReferenceRateObservation.effective_date.asc()).all()
    return {
        "rate_id": ECB_DFR,
        "status": "ok" if rows else "no_data",
        "observations": [
            {"date": r.effective_date.isoformat(), "rate": str(r.rate), "source": r.source}
            for r in rows
        ],
    }


@router.get("/economy/overview", response_model=EconomyOverviewOut)
def get_economy_overview(db: Session = Depends(get_db)):
    """ECO-6: vista agregada de Economía en una sola llamada (macro agrupado + impacto +
    bonos + forex + economía personal)."""
    return service.get_economy_overview(db)


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


@router.get("/history/{indicator_code}", response_model=InstrumentHistoryOut)
def get_instrument_history(indicator_code: str, range: str = Query(default="max")):
    """MKT-6: serie EOD de un instrumento para la ficha de detalle. Solo lectura desde
    SQLite; nunca ingesta síncrona. `range` se valida contra la serie real (ECO-2)."""
    return service.get_instrument_history(indicator_code, range_key=range)


@router.get("/sparklines")
def get_sparklines(codes: str = Query(...), points: int = Query(default=30)) -> dict[str, list[float]]:
    """MKT-8: últimos cierres por instrumento (codes separados por coma) para mini-gráficas
    de fila. Una sola consulta, solo lectura."""
    ids = [c.strip() for c in codes.split(",") if c.strip()]
    return service.get_sparklines(ids, points=points)


@router.get("/ai-datasheet", response_model=AiDatasheetOut)
def get_ai_datasheet(scope: str = Query(default="daily")):
    return service.get_ai_datasheet(scope=scope)
