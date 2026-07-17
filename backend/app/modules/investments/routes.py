import re
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.investment import (
    FundValuationSnapshot,
    Holding,
    HoldingValueHistory,
    InvestmentAsset,
    InvestmentOperation,
    SavingsAccountConfig,
)
from app.modules.investments.schemas import (
    AccountSummaryOut,
    FundCreate,
    FundSnapshotCreate,
    FundSnapshotOut,
    FundSnapshotUpdate,
    HoldingCreate,
    HoldingMerge,
    HoldingOut,
    HoldingUpdate,
    HoldingValueHistoryCreate,
    HoldingValueHistoryOut,
    HoldingValueHistoryUpdate,
    InvestmentAssetCreate,
    InvestmentAssetOut,
    InvestmentAssetUpdate,
    InvestmentOperationCreate,
    InvestmentOperationOut,
    InvestmentSummaryOut,
    PriceRefreshResultOut,
    SavingsConfigOut,
    SavingsConfigUpdate,
    SavingsCreate,
    SavingsMonthPointOut,
    SavingsProjectionOut,
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


def _get_portfolio_account_or_error(account_id: str, db: Session) -> Account:
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_active == True,  # noqa: E712
    ).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Cartera no encontrada", "details": {}}},
        )
    if account.type not in {"broker", "investment"}:
        raise HTTPException(
            status_code=422,
            detail={"error": {
                "code": "INVALID_PORTFOLIO_ACCOUNT",
                "message": "Las acciones y fondos deben estar vinculados a una cartera o broker",
                "details": {"account_type": account.type},
            }},
        )
    return account


# ── Assets ────────────────────────────────────────────────────────────────────

@router.get("/assets/search")
def search_asset_candidates(q: str):
    """Candidatos de ticker para el alta de activos (registro conocido + yfinance)."""
    from app.modules.investments.asset_resolution import search_assets

    return [
        {
            "ticker": c.ticker,
            "name": c.name,
            "exchange": c.exchange,
            "currency": c.currency,
            "asset_type": c.asset_type,
            "requires_confirmation": c.requires_confirmation,
            "confirmation_note": c.confirmation_note,
        }
        for c in search_assets(q)
    ]


@router.get("/assets", response_model=list[InvestmentAssetOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(InvestmentAsset).all()


@router.post("/assets", response_model=InvestmentAssetOut, status_code=201)
def create_asset(payload: InvestmentAssetCreate, db: Session = Depends(get_db)):
    from app.modules.investments.asset_resolution import resolve_asset

    data = payload.model_dump()
    # Autorresolución: completa ticker cualificado (IBE → IBE.MC) y divisa para que
    # el refresco de precios funcione sin pasos manuales.
    resolution = resolve_asset(data.get("ticker") or data.get("name") or "")
    if resolution.selected is None and data.get("name"):
        resolution = resolve_asset(data["name"])
    candidate = resolution.selected
    if candidate:
        if not data.get("ticker") or "." not in (data.get("ticker") or ""):
            data["ticker"] = candidate.ticker
        if candidate.currency:
            # La divisa de cotización la fija el mercado del ticker, no el formulario.
            data["currency"] = candidate.currency
        data["price_source"] = "yfinance"
    elif data.get("asset_type") in {"stock", "etf"}:
        # Una acción/ETF que ningún proveedor reconoce no puede seguirse: no se guarda.
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "UNRESOLVED_TICKER",
                    "message": "No se reconoce esa acción. Busca por nombre o usa el ticker de mercado (p. ej. IBE.MC, AAPL).",
                    "details": {"ticker": data.get("ticker"), "name": data.get("name")},
                }
            },
        )
    asset = InvestmentAsset(**data)
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

def _enrich_holding(
    h: Holding,
    asset: InvestmentAsset,
    account_name: str | None = None,
    reported_return_pct: Decimal | None = None,
) -> HoldingOut:
    cost_basis = (h.quantity * h.average_price).quantize(Decimal("0.0001"))
    return_absolute: Decimal | None = None
    return_percent: float | None = None
    accrued_interest: Decimal | None = None

    if h.market_value is not None:
        return_absolute = (h.market_value - cost_basis).quantize(Decimal("0.01"))
        if cost_basis > Decimal("0"):
            return_percent = float(return_absolute / cost_basis * 100)
        if reported_return_pct is not None:
            return_percent = float(reported_return_pct)

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


def _record_history(db: Session, holding: Holding, price: Decimal, currency: str, source: str) -> None:
    db.add(HoldingValueHistory(holding_id=holding.id, price=price, currency=currency, source=source))


def _sync_holding_from_latest_history(db: Session, holding: Holding) -> None:
    """Tras editar/borrar una entrada de historial, el precio actual del holding
    debe reflejar siempre la entrada más reciente (o quedar vacío si no hay ninguna)."""
    latest = (
        db.query(HoldingValueHistory)
        .filter(HoldingValueHistory.holding_id == holding.id)
        .order_by(HoldingValueHistory.recorded_at.desc())
        .first()
    )
    if latest:
        holding.current_price = latest.price
        holding.current_price_currency = latest.currency
        holding.current_price_updated_at = latest.recorded_at
        holding.market_value = (holding.quantity * latest.price).quantize(Decimal("0.01"))
    else:
        holding.current_price = None
        holding.current_price_updated_at = None
        holding.market_value = None


def _sync_holding_from_latest_snapshot(db: Session, holding: Holding) -> None:
    """El valor del fondo se toma del snapshot manual más reciente (INV-3).
    market_value = valor total del snapshot; current_price = valor/cantidad."""
    latest = (
        db.query(FundValuationSnapshot)
        .filter(FundValuationSnapshot.holding_id == holding.id)
        .order_by(FundValuationSnapshot.date.desc())
        .first()
    )
    if latest:
        holding.market_value = latest.market_value.quantize(Decimal("0.01"))
        holding.current_price_currency = latest.currency
        holding.current_price_updated_at = latest.created_at
        if latest.contributed_total is not None and holding.quantity > 0:
            holding.average_price = (
                latest.contributed_total / holding.quantity
            ).quantize(Decimal("0.0001"))
        if holding.quantity and holding.quantity > 0:
            holding.current_price = (latest.market_value / holding.quantity).quantize(Decimal("0.0001"))
    else:
        holding.current_price = None
        holding.current_price_updated_at = None
        holding.market_value = None


def _performance_from_snapshots(db: Session, holding: Holding, asset: InvestmentAsset) -> dict | None:
    """Serie de evolución del valor total desde los snapshots manuales del fondo (INV-3).
    Devuelve None si no hay snapshots."""
    rows = (
        db.query(FundValuationSnapshot)
        .filter(FundValuationSnapshot.holding_id == holding.id)
        .order_by(FundValuationSnapshot.date.asc())
        .all()
    )
    if not rows:
        return None
    series = [
        {"date": r.date.isoformat(), "price": round(float(r.market_value), 2)}
        for r in rows
    ]
    entry_value = float(rows[0].market_value)
    current_value = float(rows[-1].market_value)
    return {
        "holding_id": holding.id,
        "name": asset.name,
        "ticker": asset.ticker,
        "currency": asset.currency,
        "entry_date": rows[0].date.isoformat(),
        "entry_price": round(entry_value, 2),
        "entry_source": "fund_snapshot",
        "current_price": round(current_value, 2),
        "change_pct": round((current_value / entry_value - 1) * 100, 2) if entry_value > 0 else None,
        "series": series,
    }


def _performance_from_history(db: Session, holding: Holding, asset: InvestmentAsset) -> dict | None:
    """Serie de evolución construida desde el histórico manual/guardado del holding.
    Devuelve None si no hay ninguna entrada. Fallback de /performance (BUG-INV-5)."""
    rows = (
        db.query(HoldingValueHistory)
        .filter(HoldingValueHistory.holding_id == holding.id)
        .order_by(HoldingValueHistory.recorded_at.asc())
        .all()
    )
    if not rows:
        return None
    series = [
        {"date": r.recorded_at.date().isoformat(), "price": round(float(r.price), 4)}
        for r in rows
    ]
    entry_price = float(holding.average_price) if holding.average_price else float(rows[0].price)
    current_price = float(rows[-1].price)
    return {
        "holding_id": holding.id,
        "name": asset.name,
        "ticker": asset.ticker,
        "currency": asset.currency,
        "entry_date": rows[0].recorded_at.date().isoformat(),
        "entry_price": round(entry_price, 4),
        "entry_source": "history",
        "current_price": round(current_price, 4),
        "change_pct": round((current_price / entry_price - 1) * 100, 2) if entry_price > 0 else None,
        "series": series,
    }


def _get_holding_or_404(holding_id: str, db: Session) -> Holding:
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Holding no encontrado", "details": {}}},
        )
    return holding


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
    asset_ids = {h.asset_id for h in holdings}
    assets = {
        asset.id: asset
        for asset in db.query(InvestmentAsset).filter(
            InvestmentAsset.id.in_(asset_ids)
        ).all()
    } if asset_ids else {}
    fund_ids = {
        h.id for h in holdings
        if assets[h.asset_id].asset_type == "fund"
    }
    latest_reported_returns: dict[str, Decimal | None] = {}
    if fund_ids:
        snapshots = (
            db.query(FundValuationSnapshot)
            .filter(FundValuationSnapshot.holding_id.in_(fund_ids))
            .order_by(
                FundValuationSnapshot.holding_id,
                FundValuationSnapshot.date.desc(),
                FundValuationSnapshot.created_at.desc(),
            )
            .all()
        )
        for snapshot in snapshots:
            latest_reported_returns.setdefault(
                snapshot.holding_id, snapshot.reported_return_pct
            )
    return [
        _enrich_holding(
            h,
            assets[h.asset_id],
            account_names.get(h.account_id),
            latest_reported_returns.get(h.id),
        )
        for h in holdings
    ]


@router.post("/holdings", response_model=HoldingOut, status_code=201)
def create_holding(payload: HoldingCreate, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(payload.asset_id, db)
    if asset.asset_type not in {"cash", "savings_account"}:
        _get_portfolio_account_or_error(payload.account_id, db)
    data = payload.model_dump()
    if asset.asset_type in {"stock", "etf"}:
        # Una posición en acciones sin cantidad o sin precio de compra no tiene sentido.
        if Decimal(str(data.get("quantity") or 0)) <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "INVALID_QUANTITY", "message": "Indica cuántas acciones tienes (mayor que 0)", "details": {}}},
            )
        if Decimal(str(data.get("average_price") or 0)) <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "INVALID_PRICE", "message": "Indica el precio medio de compra (mayor que 0)", "details": {}}},
            )
    if data.get("current_price") is not None and data.get("market_value") is None:
        data["market_value"] = Decimal(str(data["quantity"])) * Decimal(str(data["current_price"]))
    holding = Holding(**data)
    db.add(holding)
    db.flush()
    if holding.current_price is not None and holding.current_price > 0:
        _record_history(db, holding, holding.current_price, holding.current_price_currency, source="manual")
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
    changes = payload.model_dump(exclude_none=True)
    if "account_id" in changes:
        asset = _get_asset_or_404(holding.asset_id, db)
        if asset.asset_type not in {"cash", "savings_account"}:
            _get_portfolio_account_or_error(changes["account_id"], db)
    price_changed = "current_price" in changes
    for field, value in changes.items():
        setattr(holding, field, value)
    if holding.current_price is not None:
        holding.market_value = (holding.quantity * holding.current_price).quantize(Decimal("0.01"))
        holding.current_price_updated_at = datetime.now(timezone.utc)
        if price_changed and holding.current_price > 0:
            _record_history(db, holding, holding.current_price, holding.current_price_currency, source="manual")
    db.commit()
    db.refresh(holding)
    asset = _get_asset_or_404(holding.asset_id, db)
    account = db.query(Account).filter(Account.id == holding.account_id).first()
    return _enrich_holding(holding, asset, account.name if account else None)


@router.get("/holdings/{holding_id}/history", response_model=list[HoldingValueHistoryOut])
def list_holding_history(holding_id: str, db: Session = Depends(get_db)):
    _get_holding_or_404(holding_id, db)
    return (
        db.query(HoldingValueHistory)
        .filter(HoldingValueHistory.holding_id == holding_id)
        .order_by(HoldingValueHistory.recorded_at.desc())
        .all()
    )


@router.post("/holdings/{holding_id}/history", response_model=HoldingValueHistoryOut, status_code=201)
def add_holding_history(holding_id: str, payload: HoldingValueHistoryCreate, db: Session = Depends(get_db)):
    holding = _get_holding_or_404(holding_id, db)
    entry = HoldingValueHistory(holding_id=holding_id, source="manual", **payload.model_dump(exclude_none=True))
    db.add(entry)
    db.flush()
    _sync_holding_from_latest_history(db, holding)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/holdings/{holding_id}/history/{entry_id}", response_model=HoldingValueHistoryOut)
def update_holding_history(holding_id: str, entry_id: str, payload: HoldingValueHistoryUpdate, db: Session = Depends(get_db)):
    holding = _get_holding_or_404(holding_id, db)
    entry = (
        db.query(HoldingValueHistory)
        .filter(HoldingValueHistory.id == entry_id, HoldingValueHistory.holding_id == holding_id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Entrada de historial no encontrada", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.flush()
    _sync_holding_from_latest_history(db, holding)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/holdings/{holding_id}/history/{entry_id}", status_code=204)
def delete_holding_history(holding_id: str, entry_id: str, db: Session = Depends(get_db)):
    holding = _get_holding_or_404(holding_id, db)
    entry = (
        db.query(HoldingValueHistory)
        .filter(HoldingValueHistory.id == entry_id, HoldingValueHistory.holding_id == holding_id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Entrada de historial no encontrada", "details": {}}},
        )
    db.delete(entry)
    db.flush()
    _sync_holding_from_latest_history(db, holding)
    db.commit()


# ── Fondos (INV-3, spec §3) ───────────────────────────────────────────────────

def _fund_snapshot_out(entry: FundValuationSnapshot) -> FundSnapshotOut:
    return FundSnapshotOut.model_validate(entry)


@router.post("/funds", response_model=HoldingOut, status_code=201)
def create_fund(payload: FundCreate, db: Session = Depends(get_db)):
    """Alta de fondo: crea asset(fund, manual) + holding + primer snapshot (spec §3)."""
    account = _get_portfolio_account_or_error(payload.account_id, db)
    asset = InvestmentAsset(
        name=payload.name, asset_type="fund", currency=payload.currency, price_source="manual",
    )
    db.add(asset)
    db.flush()
    holding = Holding(
        account_id=payload.account_id, asset_id=asset.id,
        quantity=Decimal("1"), average_price=payload.contributed,
        market_value=payload.value, current_price_currency=payload.currency,
        inception_date=payload.date,
    )
    db.add(holding)
    db.flush()
    db.add(FundValuationSnapshot(
        holding_id=holding.id, date=payload.date, market_value=payload.value,
        contributed_total=payload.contributed, units=payload.units, nav=payload.nav,
        reported_return_pct=payload.reported_return_pct,
        currency=payload.currency, source="manual",
    ))
    # SessionLocal usa autoflush=False: el snapshot debe persistirse antes de
    # consultarlo para sincronizar el valor inicial del holding.
    db.flush()
    _sync_holding_from_latest_snapshot(db, holding)
    db.commit()
    db.refresh(holding)
    return _enrich_holding(
        holding, asset, account.name, payload.reported_return_pct
    )


@router.get("/funds/{holding_id}/snapshots", response_model=list[FundSnapshotOut])
def list_fund_snapshots(holding_id: str, db: Session = Depends(get_db)):
    _get_holding_or_404(holding_id, db)
    return (
        db.query(FundValuationSnapshot)
        .filter(FundValuationSnapshot.holding_id == holding_id)
        .order_by(FundValuationSnapshot.date.desc())
        .all()
    )


@router.post("/funds/{holding_id}/snapshots", response_model=FundSnapshotOut, status_code=201)
def add_fund_snapshot(holding_id: str, payload: FundSnapshotCreate, db: Session = Depends(get_db)):
    """Alta o actualización del valor de un fondo en una fecha ('Actualizar valor').
    Upsert por fecha: reenviar la misma fecha actualiza el snapshot existente."""
    holding = _get_holding_or_404(holding_id, db)
    existing = (
        db.query(FundValuationSnapshot)
        .filter(
            FundValuationSnapshot.holding_id == holding_id,
            FundValuationSnapshot.date == payload.date,
        )
        .first()
    )
    if existing:
        for field, value in payload.model_dump(exclude={"date"}, exclude_none=True).items():
            setattr(existing, field, value)
        entry = existing
    else:
        entry = FundValuationSnapshot(holding_id=holding_id, source="manual", **payload.model_dump())
        db.add(entry)
    db.flush()
    _sync_holding_from_latest_snapshot(db, holding)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/funds/snapshots/{snapshot_id}", response_model=FundSnapshotOut)
def update_fund_snapshot(snapshot_id: str, payload: FundSnapshotUpdate, db: Session = Depends(get_db)):
    entry = db.query(FundValuationSnapshot).filter(FundValuationSnapshot.id == snapshot_id).first()
    if not entry:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Snapshot no encontrado", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.flush()
    holding = _get_holding_or_404(entry.holding_id, db)
    _sync_holding_from_latest_snapshot(db, holding)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/funds/snapshots/{snapshot_id}", status_code=204)
def delete_fund_snapshot(snapshot_id: str, db: Session = Depends(get_db)):
    entry = db.query(FundValuationSnapshot).filter(FundValuationSnapshot.id == snapshot_id).first()
    if not entry:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Snapshot no encontrado", "details": {}}},
        )
    holding = _get_holding_or_404(entry.holding_id, db)
    db.delete(entry)
    db.flush()
    _sync_holding_from_latest_snapshot(db, holding)
    db.commit()


# ── Cuentas remuneradas (INV-4, spec §3) ──────────────────────────────────────

def _savings_current_balance(db: Session, account: Account) -> Decimal:
    """Saldo actual: valor del holding de ahorro de la cuenta, o el balance de la cuenta."""
    holding = (
        db.query(Holding)
        .join(InvestmentAsset, InvestmentAsset.id == Holding.asset_id)
        .filter(Holding.account_id == account.id, InvestmentAsset.asset_type == "savings_account")
        .first()
    )
    if holding is not None and holding.market_value is not None:
        return holding.market_value
    return account.current_balance or Decimal("0")


def _savings_inputs(account: Account, config: SavingsAccountConfig, start_balance: Decimal):
    from app.modules.investments.savings_service import SavingsInputs
    return SavingsInputs(
        opened_at=config.opened_at or account.created_at.date(),
        start_balance=start_balance,
        rate_source=config.rate_source,
        fixed_rate=config.fixed_rate,
        spread_bps=config.spread_bps or 0,
        account_id=account.id,
    )


def _get_account_or_404(account_id: str, db: Session) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Cuenta no encontrada", "details": {}}},
        )
    return account


@router.post("/savings", response_model=SavingsConfigOut, status_code=201)
def create_savings(payload: SavingsCreate, db: Session = Depends(get_db)):
    """Alta de cuenta remunerada: cuenta (existente o nueva) + holding + config (spec §3)."""
    if payload.account_id:
        account = _get_account_or_404(payload.account_id, db)
        account.current_balance = payload.balance
    elif payload.new_account_name:
        account = Account(
            name=payload.new_account_name, type="savings", institution=payload.institution,
            currency="EUR", current_balance=payload.balance,
        )
        db.add(account)
        db.flush()
    else:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "MISSING_ACCOUNT", "message": "Indica account_id o new_account_name", "details": {}}},
        )
    if db.query(SavingsAccountConfig).filter(SavingsAccountConfig.account_id == account.id).first():
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "ALREADY_CONFIGURED", "message": "La cuenta ya tiene configuración de ahorro", "details": {}}},
        )
    # Holding que representa el saldo en la cartera (asset_type=savings_account).
    asset = InvestmentAsset(name=account.name, asset_type="savings_account", currency="EUR", price_source="manual")
    db.add(asset)
    db.flush()
    fixed_fraction = (payload.fixed_rate / Decimal("100")) if payload.fixed_rate is not None else None
    db.add(Holding(
        account_id=account.id, asset_id=asset.id,
        quantity=payload.balance, average_price=Decimal("1"), market_value=payload.balance,
        interest_rate=fixed_fraction, inception_date=payload.opened_at,
    ))
    config = SavingsAccountConfig(
        account_id=account.id, opened_at=payload.opened_at, rate_source=payload.rate_source,
        fixed_rate=payload.fixed_rate, spread_bps=payload.spread_bps,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/savings/{account_id}/projection", response_model=SavingsProjectionOut)
def get_savings_projection(account_id: str, as_of: date | None = None, db: Session = Depends(get_db)):
    """Serie mensual de intereses + total (motor determinista INV-4, spec §2.3).

    V1: si no se conoce el saldo inicial, se retro-calcula desde el saldo actual
    asumiendo sin movimientos y se marca estimated=True."""
    from app.modules.investments.savings_service import compute_schedule, estimate_start_balance

    account = _get_account_or_404(account_id, db)
    config = db.query(SavingsAccountConfig).filter(SavingsAccountConfig.account_id == account_id).first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "La cuenta no tiene configuración de ahorro", "details": {}}},
        )
    if config.rate_source == "ecb_deposit_facility":
        from app.modules.investments.reference_rate_service import ensure_deposit_facility_history
        ensure_deposit_facility_history(db)
    current_balance = _savings_current_balance(db, account)
    base = _savings_inputs(account, config, current_balance)
    start_balance = estimate_start_balance(db, base, current_balance, as_of)
    base.start_balance = start_balance
    schedule = compute_schedule(db, base, as_of)
    return SavingsProjectionOut(
        # schedule.points son dataclasses MonthPoint; pydantic no las coacciona solo.
        points=[SavingsMonthPointOut.model_validate(p, from_attributes=True) for p in schedule.points],
        total_interest=schedule.total_interest,
        total_contributions=schedule.total_contributions,
        current_balance=schedule.current_balance,
        current_rate=schedule.current_rate,
        estimated=True,
    )


@router.get("/savings/{account_id}", response_model=SavingsConfigOut)
def get_savings(account_id: str, db: Session = Depends(get_db)):
    config = db.query(SavingsAccountConfig).filter(SavingsAccountConfig.account_id == account_id).first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Sin configuración de ahorro", "details": {}}},
        )
    return config


@router.put("/savings/{account_id}", response_model=SavingsConfigOut)
def update_savings(account_id: str, payload: SavingsConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(SavingsAccountConfig).filter(SavingsAccountConfig.account_id == account_id).first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Sin configuración de ahorro", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    # Sincroniza el holding de ahorro para que la tarjeta (TAE, fecha) refleje la config.
    holding = (
        db.query(Holding)
        .join(InvestmentAsset, InvestmentAsset.id == Holding.asset_id)
        .filter(Holding.account_id == account_id, InvestmentAsset.asset_type == "savings_account")
        .first()
    )
    if holding is not None:
        if config.fixed_rate is not None:
            holding.interest_rate = config.fixed_rate / Decimal("100")
        if config.opened_at is not None:
            holding.inception_date = config.opened_at
    db.commit()
    db.refresh(config)
    return config


@router.delete("/savings/{account_id}", status_code=204)
def delete_savings(account_id: str, db: Session = Depends(get_db)):
    config = db.query(SavingsAccountConfig).filter(SavingsAccountConfig.account_id == account_id).first()
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Sin configuración de ahorro", "details": {}}},
        )
    db.delete(config)
    db.commit()


@router.post("/holdings/merge", response_model=HoldingOut)
def merge_holdings(payload: HoldingMerge, db: Session = Depends(get_db)):
    """Fusiona dos posiciones duplicadas en la de destino (BUG-INV-1).

    Suma cantidades, promedia el precio de entrada ponderado por cantidad y reasigna
    el histórico y las operaciones del origen al destino (sin borrado físico de
    operaciones). El holding origen se elimina."""
    if payload.source_id == payload.target_id:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "SAME_HOLDING", "message": "Origen y destino no pueden ser el mismo holding", "details": {}}},
        )
    source = _get_holding_or_404(payload.source_id, db)
    target = _get_holding_or_404(payload.target_id, db)

    total_qty = source.quantity + target.quantity
    if total_qty > 0:
        target.average_price = (
            (source.quantity * source.average_price + target.quantity * target.average_price) / total_qty
        ).quantize(Decimal("0.0001"))
    target.quantity = total_qty

    if source.market_value is not None or target.market_value is not None:
        target.market_value = (
            (source.market_value or Decimal("0")) + (target.market_value or Decimal("0"))
        ).quantize(Decimal("0.01"))

    # Reasignar histórico y operaciones del origen al destino: se conserva todo el
    # rastro bajo la posición superviviente (mitigación de riesgo del plan §7).
    db.query(HoldingValueHistory).filter(HoldingValueHistory.holding_id == source.id).update(
        {HoldingValueHistory.holding_id: target.id}
    )
    # Snapshots de fondo: reasignar, descartando fechas que ya existan en el destino
    # (el constraint único (holding_id, date) las rechazaría).
    target_dates = {
        s.date for s in db.query(FundValuationSnapshot).filter(
            FundValuationSnapshot.holding_id == target.id
        )
    }
    for snap in db.query(FundValuationSnapshot).filter(FundValuationSnapshot.holding_id == source.id):
        if snap.date in target_dates:
            db.delete(snap)
        else:
            snap.holding_id = target.id
    db.query(InvestmentOperation).filter(
        InvestmentOperation.asset_id == source.asset_id,
        InvestmentOperation.account_id == source.account_id,
    ).update(
        {InvestmentOperation.asset_id: target.asset_id, InvestmentOperation.account_id: target.account_id}
    )

    db.delete(source)
    db.commit()
    db.refresh(target)
    asset = _get_asset_or_404(target.asset_id, db)
    account = db.query(Account).filter(Account.id == target.account_id).first()
    return _enrich_holding(target, asset, account.name if account else None)


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


@router.get("/holdings/{holding_id}/performance")
def get_holding_performance(holding_id: str, db: Session = Depends(get_db)) -> dict:
    """Evolución del precio desde la compra registrada hasta hoy, en la divisa nativa del activo."""
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Holding no encontrado", "details": {}}},
        )
    asset = _get_asset_or_404(holding.asset_id, db)
    if not asset.ticker:
        # Sin ticker (fondos, cuentas): la evolución sale de los snapshots de valor del
        # fondo (INV-3) o, si no hay, del histórico de precios guardado.
        stored = _performance_from_snapshots(db, holding, asset) or _performance_from_history(db, holding, asset)
        if stored is not None:
            return stored
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "NO_TICKER", "message": "El activo no tiene ticker; añade valoraciones manuales para ver su evolución", "details": {}}},
        )

    buy = (
        db.query(InvestmentOperation)
        .filter(
            InvestmentOperation.asset_id == asset.id,
            InvestmentOperation.account_id == holding.account_id,
            InvestmentOperation.operation_type == "buy",
        )
        .order_by(InvestmentOperation.date.asc())
        .first()
    )
    entry_date = buy.date if buy else (holding.inception_date or holding.created_at.date())
    entry_price = buy.price if buy and buy.price is not None else holding.average_price
    entry_source = "operation" if buy else "holding"

    import yfinance as yf

    try:
        hist = yf.Ticker(asset.ticker).history(start=entry_date.isoformat(), auto_adjust=False)
        closes = hist["Close"].dropna()
    except Exception:
        closes = None
    if closes is None or closes.empty:
        # El proveedor no devolvió serie (ticker sin cobertura, red caída): antes de
        # rendirse, usar el histórico propio guardado en cada refresco (BUG-INV-5).
        stored = _performance_from_history(db, holding, asset)
        if stored is not None:
            return stored
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "NO_PRICE_HISTORY", "message": f"Sin histórico de precios para {asset.ticker}", "details": {}}},
        )

    # ponytail: downsample a <=240 puntos; suficiente para la gráfica, sin tabla de histórico en DB
    step = max(1, len(closes) // 240)
    series = [
        {"date": idx.date().isoformat(), "price": round(float(v), 4)}
        for idx, v in closes.iloc[::step].items()
    ]
    last_date = closes.index[-1].date().isoformat()
    if series[-1]["date"] != last_date:
        series.append({"date": last_date, "price": round(float(closes.iloc[-1]), 4)})

    current_price = float(closes.iloc[-1])
    entry = float(entry_price) if entry_price else 0.0
    return {
        "holding_id": holding.id,
        "name": asset.name,
        "ticker": asset.ticker,
        "currency": asset.currency,
        "entry_date": entry_date.isoformat(),
        "entry_price": round(entry, 4),
        "entry_source": entry_source,
        "current_price": round(current_price, 4),
        "change_pct": round((current_price / entry - 1) * 100, 2) if entry > 0 else None,
        "series": series,
    }


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
    asset_ids = {h.asset_id for h in holdings}
    asset_types = {
        asset.id: asset.asset_type
        for asset in db.query(InvestmentAsset).filter(
            InvestmentAsset.id.in_(asset_ids),
        ).all()
    } if asset_ids else {}
    fund_asset_ids = {
        asset_id for asset_id, asset_type in asset_types.items()
        if asset_type == "fund"
    }
    fund_ids = [h.id for h in holdings if h.asset_id in fund_asset_ids]
    latest_fund_snapshots: dict[str, FundValuationSnapshot] = {}
    if fund_ids:
        snapshots = (
            db.query(FundValuationSnapshot)
            .filter(FundValuationSnapshot.holding_id.in_(fund_ids))
            .order_by(
                FundValuationSnapshot.holding_id,
                FundValuationSnapshot.date.desc(),
                FundValuationSnapshot.created_at.desc(),
            )
            .all()
        )
        for snapshot in snapshots:
            latest_fund_snapshots.setdefault(snapshot.holding_id, snapshot)
    total_value = Decimal("0")
    total_invested = Decimal("0")
    performance_value = Decimal("0")
    pending_count = 0
    pending_invested = Decimal("0")
    by_account: dict[str, AccountSummaryOut] = {}
    last_updated = None
    fund_reported_weighted_sum = Decimal("0")
    fund_reported_weight = Decimal("0")

    for h in holdings:
        cost_basis = h.quantity * h.average_price
        excluded_from_pnl = asset_types.get(h.asset_id) in {"savings_account", "cash"}
        # Un holding sin valoración (fondo sin snapshot, precio no disponible) no puede
        # entrar en el KPI global: infla "Aportado" contra un valor 0 y rompe la
        # rentabilidad (BUG-INV-1). Se contabiliza aparte para avisar, no en silencio.
        if h.market_value is None:
            if not excluded_from_pnl:
                pending_count += 1
                pending_invested += cost_basis
            continue

        total_value += h.market_value

        latest_snapshot = latest_fund_snapshots.get(h.id)
        if latest_snapshot and latest_snapshot.reported_return_pct is not None:
            weight = latest_snapshot.contributed_total or cost_basis
            if weight > Decimal("0"):
                fund_reported_weighted_sum += latest_snapshot.reported_return_pct * weight
                fund_reported_weight += weight

        if h.account_id not in by_account:
            by_account[h.account_id] = AccountSummaryOut(
                account_id=h.account_id, value=Decimal("0"), invested=Decimal("0")
            )
        by_account[h.account_id].value += h.market_value

        # Una cuenta remunerada es ahorro con intereses: forma parte del valor total y
        # del patrimonio, pero no es capital aportado a una inversión ni debe diluir
        # el porcentaje de P&L de acciones/fondos.
        if excluded_from_pnl:
            continue

        total_invested += cost_basis
        performance_value += h.market_value
        by_account[h.account_id].invested += cost_basis

        if h.current_price_updated_at:
            if last_updated is None or h.current_price_updated_at > last_updated:
                last_updated = h.current_price_updated_at

    return_absolute = performance_value - total_invested
    return_percent = (
        float(return_absolute / total_invested * 100) if total_invested > Decimal("0") else 0.0
    )
    fund_reported_return_percent = (
        float(fund_reported_weighted_sum / fund_reported_weight)
        if fund_reported_weight > Decimal("0")
        else None
    )
    cents = Decimal("0.01")

    return InvestmentSummaryOut(
        total_value=total_value.quantize(cents),
        total_invested=total_invested.quantize(cents),
        return_absolute=return_absolute.quantize(cents),
        return_percent=return_percent,
        currency="EUR",
        by_account=list(by_account.values()),
        last_updated=last_updated,
        pending_valuation_count=pending_count,
        pending_valuation_invested=pending_invested.quantize(cents),
        fund_reported_return_percent=fund_reported_return_percent,
    )


@router.get("/holdings/portfolio-evolution")
def get_portfolio_evolution(db: Session = Depends(get_db)) -> dict:
    """Evolución mensual agregada del valor de la cartera (INV-6).

    Por mes combina el valor de cada posición: fondos → snapshots manuales,
    cuentas remuneradas → motor determinista, resto → histórico guardado
    (precio×cantidad) o el market_value actual. Cada serie se rellena hacia
    delante sobre el eje común de meses y se suman. Solo datos en BD, sin red."""
    from app.modules.investments.reference_rate_service import ensure_deposit_facility_history
    from app.modules.investments.savings_service import compute_schedule, estimate_start_balance

    ensure_deposit_facility_history(db)
    per_holding: dict[str, dict[str, Decimal]] = {}
    for h in db.query(Holding).all():
        asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == h.asset_id).first()
        if asset is None:
            continue
        monthly: dict[str, Decimal] = {}
        if asset.asset_type == "fund":
            for s in (
                db.query(FundValuationSnapshot)
                .filter(FundValuationSnapshot.holding_id == h.id)
                .order_by(FundValuationSnapshot.date.asc())
            ):
                monthly[f"{s.date.year:04d}-{s.date.month:02d}"] = s.market_value
        elif asset.asset_type == "savings_account":
            account = db.query(Account).filter(Account.id == h.account_id).first()
            config = (
                db.query(SavingsAccountConfig)
                .filter(SavingsAccountConfig.account_id == h.account_id)
                .first()
            )
            if account and config:
                current_balance = _savings_current_balance(db, account)
                base = _savings_inputs(account, config, current_balance)
                base.start_balance = estimate_start_balance(db, base, current_balance, None)
                for p in compute_schedule(db, base).points:
                    monthly[p.month] = p.balance_end
        else:
            rows = (
                db.query(HoldingValueHistory)
                .filter(HoldingValueHistory.holding_id == h.id)
                .order_by(HoldingValueHistory.recorded_at.asc())
                .all()
            )
            for r in rows:
                monthly[f"{r.recorded_at.year:04d}-{r.recorded_at.month:02d}"] = (
                    h.quantity * r.price
                ).quantize(Decimal("0.01"))
            if not rows and h.market_value is not None:
                d = h.current_price_updated_at or h.updated_at or h.created_at
                monthly[f"{d.year:04d}-{d.month:02d}"] = h.market_value
        if monthly:
            per_holding[h.id] = monthly

    all_months = sorted({m for mm in per_holding.values() for m in mm})
    if not all_months:
        return {"series": [], "currency": "EUR"}

    series: list[dict] = []
    last_val: dict[str, Decimal] = {}
    for month in all_months:
        total = Decimal("0")
        for hid, mm in per_holding.items():
            if month in mm:
                last_val[hid] = mm[month]
            if hid in last_val:
                total += last_val[hid]
        series.append({"month": month, "value": round(float(total), 2)})

    return {"series": series, "currency": "EUR"}


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
