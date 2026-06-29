"""Portfolio Import Assistant — FastAPI routes.

Endpoints:
  POST /api/investments/import/parse-text       – parse pasted broker text
  POST /api/investments/import/validate         – validate a batch of positions
  POST /api/investments/import/check-duplicates – check against existing holdings
  POST /api/investments/import/confirm          – create holdings (requires explicit call)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.investments.portfolio_import_service import (
    ConfirmedPosition,
    RawPosition,
    ValidatedPosition,
    create_holding_from_import,
    find_duplicates,
    parse_text_positions,
    validate_position,
)

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ParseTextRequest(BaseModel):
    text: str


class RawPositionOut(BaseModel):
    raw_name: str
    quantity: Optional[float]
    current_value: Optional[float]
    current_value_currency: Optional[str]
    return_pct: Optional[float]
    raw_text: str


class ValidatePositionRequest(BaseModel):
    raw_name: str
    quantity: Optional[float] = None
    current_value: Optional[float] = None
    current_value_currency: Optional[str] = None
    return_pct: Optional[float] = None
    raw_text: str = ""


class ValidateBatchRequest(BaseModel):
    positions: list[ValidatePositionRequest]


class ValidatedPositionOut(BaseModel):
    id: str
    raw_name: str
    quantity: Optional[float]
    current_value: Optional[float]
    current_value_currency: Optional[str]
    return_pct: Optional[float]
    raw_text: str

    estimated_cost: Optional[float]
    is_cost_estimated: bool

    selected_ticker: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    asset_type: str
    resolution_status: str
    resolution_confidence: float
    requires_confirmation: bool

    price: Optional[float]
    price_currency: Optional[str]
    eur_price: Optional[float]
    fx_rate: Optional[float]
    coverage_status: Optional[str]

    import_status: str
    notes: list[str]


class CheckDuplicatesRequest(BaseModel):
    ticker: str
    account_id: Optional[str] = None


class CheckDuplicatesOut(BaseModel):
    ticker: str
    account_id: Optional[str]
    duplicate_holding_ids: list[str]
    has_duplicates: bool


class ConfirmPositionIn(BaseModel):
    raw_name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    currency: str = "EUR"
    asset_type: str = "stock"
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    current_price_currency: str = "EUR"
    price_source: str = "auto"
    account_id: str
    is_manual: bool = False
    is_cost_estimated: bool = False
    notes: list[str] = []


class ConfirmBatchRequest(BaseModel):
    positions: list[ConfirmPositionIn]


class ImportedHoldingOut(BaseModel):
    holding_id: str
    asset_id: str
    raw_name: str
    ticker: Optional[str]
    quantity: float
    average_price: float
    current_price: Optional[float]
    account_id: str
    is_manual: bool


class ConfirmBatchOut(BaseModel):
    imported: list[ImportedHoldingOut]
    failed: list[str]
    total: int
    imported_count: int


# ── Route helpers ─────────────────────────────────────────────────────────────

def _validated_to_out(v: ValidatedPosition) -> ValidatedPositionOut:
    return ValidatedPositionOut(
        id=v.id,
        raw_name=v.raw_name,
        quantity=v.quantity,
        current_value=v.current_value,
        current_value_currency=v.current_value_currency,
        return_pct=v.return_pct,
        raw_text=v.raw_text,
        estimated_cost=v.estimated_cost,
        is_cost_estimated=v.is_cost_estimated,
        selected_ticker=v.selected_ticker,
        exchange=v.exchange,
        currency=v.currency,
        asset_type=v.asset_type,
        resolution_status=v.resolution_status,
        resolution_confidence=v.resolution_confidence,
        requires_confirmation=v.requires_confirmation,
        price=v.price,
        price_currency=v.price_currency,
        eur_price=v.eur_price,
        fx_rate=v.fx_rate,
        coverage_status=v.coverage_status,
        import_status=v.import_status,
        notes=v.notes,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/parse-text", response_model=list[RawPositionOut])
def parse_text(payload: ParseTextRequest) -> list[RawPositionOut]:
    """Extract raw positions from pasted broker text (local parsing, no external calls)."""
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "EMPTY_TEXT", "message": "El texto pegado está vacío."}},
        )
    raw = parse_text_positions(payload.text)
    return [
        RawPositionOut(
            raw_name=p.raw_name,
            quantity=p.quantity,
            current_value=p.current_value,
            current_value_currency=p.current_value_currency,
            return_pct=p.return_pct,
            raw_text=p.raw_text,
        )
        for p in raw
    ]


@router.post("/validate", response_model=list[ValidatedPositionOut])
def validate_batch(payload: ValidateBatchRequest) -> list[ValidatedPositionOut]:
    """Validate a batch of positions: resolve instrument + fetch price coverage."""
    if not payload.positions:
        return []
    results = []
    for req in payload.positions:
        v = validate_position(
            raw_name=req.raw_name,
            quantity=req.quantity,
            current_value=req.current_value,
            current_value_currency=req.current_value_currency,
            return_pct=req.return_pct,
            raw_text=req.raw_text,
        )
        results.append(_validated_to_out(v))
    return results


@router.post("/check-duplicates", response_model=CheckDuplicatesOut)
def check_duplicates(
    payload: CheckDuplicatesRequest,
    db: Session = Depends(get_db),
) -> CheckDuplicatesOut:
    """Check whether a ticker already has a holding in the account."""
    ids = find_duplicates(payload.ticker, payload.account_id, db)
    return CheckDuplicatesOut(
        ticker=payload.ticker,
        account_id=payload.account_id,
        duplicate_holding_ids=ids,
        has_duplicates=len(ids) > 0,
    )


@router.post("/confirm", response_model=ConfirmBatchOut)
def confirm_import(
    payload: ConfirmBatchRequest,
    db: Session = Depends(get_db),
) -> ConfirmBatchOut:
    """Create holdings from confirmed positions.

    Called only after the user has explicitly reviewed and confirmed the data.
    No holding is created without passing through this endpoint deliberately.
    """
    if not payload.positions:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "NO_POSITIONS", "message": "No hay posiciones para importar."}},
        )

    imported: list[ImportedHoldingOut] = []
    failed: list[str] = []

    for pos in payload.positions:
        try:
            confirmed = ConfirmedPosition(
                raw_name=pos.raw_name,
                ticker=pos.ticker,
                exchange=pos.exchange,
                currency=pos.currency,
                asset_type=pos.asset_type,
                quantity=pos.quantity,
                average_price=pos.average_price,
                current_price=pos.current_price,
                current_price_currency=pos.current_price_currency,
                price_source=pos.price_source,
                account_id=pos.account_id,
                is_manual=pos.is_manual,
                notes=pos.notes,
                is_cost_estimated=pos.is_cost_estimated,
            )
            holding = create_holding_from_import(confirmed, db)
            imported.append(
                ImportedHoldingOut(
                    holding_id=holding.id,
                    asset_id=holding.asset_id,
                    raw_name=pos.raw_name,
                    ticker=pos.ticker,
                    quantity=float(holding.quantity),
                    average_price=float(holding.average_price),
                    current_price=float(holding.current_price) if holding.current_price else None,
                    account_id=holding.account_id,
                    is_manual=pos.is_manual,
                )
            )
        except Exception as exc:
            failed.append(f"{pos.raw_name}: {exc}")

    return ConfirmBatchOut(
        imported=imported,
        failed=failed,
        total=len(payload.positions),
        imported_count=len(imported),
    )
