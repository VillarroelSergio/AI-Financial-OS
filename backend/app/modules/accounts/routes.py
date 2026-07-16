from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.investment import Holding
from app.models.transaction import Transaction
from app.modules.accounts.schemas import AccountCreate, AccountOut, AccountUpdate
from app.modules.accounts.valuation_service import CurrentValuation, build_current_valuation

router = APIRouter()


@router.post("/purge-inactive")
def purge_inactive_accounts(preview: bool = True, db: Session = Depends(get_db)) -> dict:
    """Elimina cuentas soft-deleted sin transacciones ni posiciones (duplicados de imports)."""
    referenced = {r[0] for r in db.query(Transaction.account_id).distinct()}
    referenced |= {r[0] for r in db.query(Holding.account_id).distinct()}
    purgeable = (
        db.query(Account)
        .filter(Account.is_active == False)  # noqa: E712
        .filter(Account.id.notin_(referenced))
        .all()
    )
    names = [a.name for a in purgeable]
    if not preview:
        for account in purgeable:
            db.delete(account)
        db.commit()
    return {"affected": len(names), "names": names, "applied": not preview}


def _account_out(account: Account, valuation: CurrentValuation) -> AccountOut:
    return AccountOut.model_validate(account).model_copy(update={
        "cash_balance_eur": valuation.cash_by_account.get(account.id, Decimal("0")),
        "portfolio_value_eur": valuation.portfolio_by_account.get(account.id, Decimal("0")),
        "total_value_eur": valuation.total_by_account.get(account.id, Decimal("0")),
        "position_count": valuation.position_count_by_account.get(account.id, 0),
    })


@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    valuation = build_current_valuation(db)
    return [_account_out(account, valuation) for account in valuation.accounts]


@router.post("", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountOut:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _account_out(account, build_current_valuation(db))


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: str, payload: AccountUpdate, db: Session = Depends(get_db)) -> AccountOut:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Cuenta no encontrada", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return _account_out(account, build_current_valuation(db))


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: str, db: Session = Depends(get_db)) -> None:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Cuenta no encontrada", "details": {}}},
        )
    account.is_active = False
    db.commit()
