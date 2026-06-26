"""Market Intelligence API routes."""
from fastapi import APIRouter, Query
from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import (
    AiDatasheetOut, BondSnapshotOut, ForexSnapshotOut,
    MacroSnapshotOut, MarketSnapshotOut, NewsSnapshotOut,
)

router = APIRouter()


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
