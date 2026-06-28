"""Financial Knowledge API router."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.financial_knowledge import service
from app.modules.financial_knowledge.schemas import (
    AIDatasheetOut, FinancialSignalOut, KnowledgeSnapshotOut,
    MarketRegimeOut, PersonalImpactOut, RecomputeResultOut,
)

router = APIRouter()


@router.get("/snapshot", response_model=KnowledgeSnapshotOut)
def get_snapshot():
    return service.get_snapshot()


@router.get("/regime", response_model=Optional[MarketRegimeOut])
def get_regime():
    return service.get_regime()


@router.get("/signals", response_model=list[FinancialSignalOut])
def get_signals():
    return service.get_signals()


@router.get("/personal-impact", response_model=list[PersonalImpactOut])
def get_personal_impact():
    return service.get_personal_impacts()


@router.get("/datasheet", response_model=Optional[AIDatasheetOut])
def get_datasheet():
    return service.get_ai_datasheet()


@router.post("/recompute", response_model=RecomputeResultOut)
def recompute(db: Session = Depends(get_db)):
    return service.recompute(db=db)
