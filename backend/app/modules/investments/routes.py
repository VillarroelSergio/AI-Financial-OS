from datetime import date, datetime, timezone
from decimal import Decimal
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.investment import Holding, InvestmentAsset, InvestmentOperation
from app.modules.investments.schemas import (
    AccountSummaryOut,
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
    InvestmentAssetCreate,
    InvestmentAssetOut,
    InvestmentAssetUpdate,
    InvestmentOperationCreate,
    InvestmentOperationOut,
    InvestmentSummaryOut,
    PriceRefreshResultOut,
)

router = APIRouter()
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
ASSET_TYPE_MAP = {
    "stock": "stock",
    "etf": "etf",
    "fund": "fund",
    "crypto": "crypto",
    "bond": "bond",
    "cash": "cash",
    "savings_account": "cash",
}


# ── Assets ────────────────────────────────────────────────────────────────────

@router.get("/assets", response_model=list[InvestmentAssetOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(InvestmentAsset).all()


@router.post("/assets", response_model=InvestmentAssetOut, status_code=201)
def create_asset(payload: InvestmentAssetCreate, db: Session = Depends(get_db)):
    asset = InvestmentAsset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.patch("/assets/{asset_id}", response_model=InvestmentAssetOut)
def update_asset(asset_id: str, payload: InvestmentAssetUpdate, db: Session = Depends(get_db)):
    asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Activo no encontrado", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Activo no encontrado", "details": {}}},
        )
    dependent_count = db.query(Holding).filter(Holding.asset_id == asset_id).count()
    if dependent_count > 0:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "CONFLICT", "message": "El activo tiene posiciones asociadas. Elimina las posiciones primero.", "details": {}}},
        )
    db.delete(asset)
    db.commit()


# ── Holdings helpers ──────────────────────────────────────────────────────────

def _enrich_holding(h: Holding, asset: InvestmentAsset, account_name: str | None = None) -> HoldingOut:
    cost_basis = (h.quantity * h.average_price).quantize(Decimal("0.0001"))
    return_absolute: Decimal | None = None
    return_percent: float | None = None
    accrued_interest: Decimal | None = None

    if h.market_value is not None:
        return_absolute = (h.market_value - cost_basis).quantize(Decimal("0.01"))
        if cost_basis > Decimal("0"):
            return_percent = float(return_absolute / cost_basis * 100)

    if (
        asset.asset_type == "savings_account"
        and h.inception_date is not None
        and h.interest_rate is not None
    ):
        days = (date.today() - h.inception_date).days
        accrued_interest = h.quantity * h.interest_rate * Decimal(days) / Decimal("365")

    warnings: list[str] = []
    raw_name = (asset.name or "").strip()
    raw_symbol = (asset.ticker or "").strip()
    safe_name = raw_name if raw_name and not UUID_RE.match(raw_name) else ""
    safe_symbol = raw_symbol if raw_symbol and not UUID_RE.match(raw_symbol) else None
    display_name = safe_name or safe_symbol or "Activo sin identificar"
    if display_name == "Activo sin identificar":
        warnings.append("Faltan nombre y simbolo normalizados.")
    if UUID_RE.match(raw_name) or UUID_RE.match(raw_symbol):
        warnings.append("Se oculto un identificador interno como etiqueta visible.")
    if asset.price_source in {"mock", "demo", "seed"}:
        warnings.append("Dato demo o semilla; no tratar como dato real.")

    invested_amount = cost_basis.quantize(Decimal("0.01"))
    current_value = h.market_value if h.market_value is not None else Decimal("0")
    unrealized_pnl = (current_value - invested_amount).quantize(Decimal("0.01"))
    unrealized_pnl_pct = float(unrealized_pnl / invested_amount * 100) if invested_amount > 0 else 0.0
    quality_score = 1.0
    if display_name == "Activo sin identificar":
        quality_score -= 0.4
    if h.current_price is None:
        quality_score -= 0.2
        warnings.append("Precio actual no disponible; puede editarse manualmente.")

    return HoldingOut(
        id=h.id,
        account_id=h.account_id,
        asset_id=h.asset_id,
        quantity=h.quantity,
        average_price=h.average_price,
        current_price=h.current_price,
        current_price_currency=h.current_price_currency,
        current_price_updated_at=h.current_price_updated_at,
        market_value=h.market_value,
        interest_rate=h.interest_rate,
        inception_date=h.inception_date,
        created_at=h.created_at,
        updated_at=h.updated_at,
        asset=InvestmentAssetOut.model_validate(asset),
        cost_basis=cost_basis,
        return_absolute=return_absolute,
        return_percent=return_percent,
        accrued_interest=accrued_interest,
        display_name=display_name,
        symbol=safe_symbol,
        asset_type=ASSET_TYPE_MAP.get(asset.asset_type, "unknown"),
        broker=account_name or "Cuenta",
        invested_amount=invested_amount,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=round(unrealized_pnl_pct, 2),
        currency=asset.currency or h.current_price_currency or "EUR",
        is_mock=asset.price_source in {"mock", "demo", "seed"},
        quality_score=max(0.0, round(quality_score, 2)),
        warnings=warnings,
    )


def _get_asset_or_404(asset_id: str, db: Session) -> InvestmentAsset:
    asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Activo no encontrado", "details": {}}},
        )
    return asset


# ── Holdings ──────────────────────────────────────────────────────────────────

@router.get("/holdings", response_model=list[HoldingOut])
def list_holdings(account_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Holding)
    if account_id:
        q = q.filter(Holding.account_id == account_id)
    holdings = q.all()
    account_ids = {h.account_id for h in holdings}
    account_names = {
        a.id: a.name
        for a in db.query(Account).filter(Account.id.in_(account_ids)).all()
    } if account_ids else {}
    return [_enrich_holding(h, _get_asset_or_404(h.asset_id, db), account_names.get(h.account_id)) for h in holdings]


@router.post("/holdings", response_model=HoldingOut, status_code=201)
def create_holding(payload: HoldingCreate, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(payload.asset_id, db)
    data = payload.model_dump()
    if data.get("current_price") is not None and data.get("market_value") is None:
        data["market_value"] = Decimal(str(data["quantity"])) * Decimal(str(data["current_price"]))
    holding = Holding(**data)
    db.add(holding)
    db.commit()
    db.refresh(holding)
    account = db.query(Account).filter(Account.id == holding.account_id).first()
    return _enrich_holding(holding, asset, account.name if account else None)


@router.patch("/holdings/{holding_id}", response_model=HoldingOut)
def update_holding(holding_id: str, payload: HoldingUpdate, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Holding no encontrado", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(holding, field, value)
    if holding.current_price is not None:
        holding.market_value = (holding.quantity * holding.current_price).quantize(Decimal("0.01"))
        holding.current_price_updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(holding)
    asset = _get_asset_or_404(holding.asset_id, db)
    account = db.query(Account).filter(Account.id == holding.account_id).first()
    return _enrich_holding(holding, asset, account.name if account else None)


@router.delete("/holdings/{holding_id}", status_code=204)
def delete_holding(holding_id: str, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Holding no encontrado", "details": {}}},
        )
    db.delete(holding)
    db.commit()


# ── Operations ────────────────────────────────────────────────────────────────

@router.get("/operations", response_model=list[InvestmentOperationOut])
def list_operations(account_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(InvestmentOperation).order_by(InvestmentOperation.date.desc())
    if account_id:
        q = q.filter(InvestmentOperation.account_id == account_id)
    return q.all()


@router.post("/operations", response_model=InvestmentOperationOut, status_code=201)
def create_operation(payload: InvestmentOperationCreate, db: Session = Depends(get_db)):
    op = InvestmentOperation(**payload.model_dump())
    db.add(op)
    db.commit()
    db.refresh(op)
    return op


# ── Summary ───────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=InvestmentSummaryOut)
def get_summary(db: Session = Depends(get_db)):
    holdings = db.query(Holding).all()
    total_value = Decimal("0")
    total_invested = Decimal("0")
    by_account: dict[str, AccountSummaryOut] = {}
    last_updated = None

    for h in holdings:
        cost_basis = h.quantity * h.average_price
        total_invested += cost_basis
        mv = h.market_value if h.market_value is not None else Decimal("0")
        total_value += mv

        if h.account_id not in by_account:
            by_account[h.account_id] = AccountSummaryOut(
                account_id=h.account_id, value=Decimal("0"), invested=Decimal("0")
            )
        by_account[h.account_id].value += mv
        by_account[h.account_id].invested += cost_basis

        if h.current_price_updated_at:
            if last_updated is None or h.current_price_updated_at > last_updated:
                last_updated = h.current_price_updated_at

    return_absolute = total_value - total_invested
    return_percent = (
        float(return_absolute / total_invested * 100) if total_invested > Decimal("0") else 0.0
    )

    return InvestmentSummaryOut(
        total_value=total_value,
        total_invested=total_invested,
        return_absolute=return_absolute,
        return_percent=return_percent,
        currency="EUR",
        by_account=list(by_account.values()),
        last_updated=last_updated,
    )


# ── Price refresh (placeholder — implemented in Task 5) ───────────────────────

@router.post("/prices/refresh", response_model=PriceRefreshResultOut)
def refresh_prices(db: Session = Depends(get_db)):
    from app.modules.investments.price_service import PriceService
    result = PriceService.refresh_prices(db)
    return PriceRefreshResultOut(
        ok=not result.errors,
        updated=result.updated,
        failed=result.failed,
        needs_manual_nav=result.needs_manual_nav,
        updated_items=result.updated_items,
        manual_required=result.manual_required,
        skipped=result.skipped,
        errors=result.errors,
    )


@router.post("/refresh-prices", response_model=PriceRefreshResultOut)
def refresh_prices_alias(db: Session = Depends(get_db)):
    return refresh_prices(db)
