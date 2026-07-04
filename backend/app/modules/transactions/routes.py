import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.modules.security.service import create_backup
from app.modules.transactions.schemas import (
    CurrencyReassign,
    ScopeUpdate,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)

router = APIRouter()


def _stamp_account_names(db: Session, txs: list[Transaction]) -> list[Transaction]:
    # Incluye cuentas inactivas: las tx pueden apuntar a cuentas soft-deleted.
    names = {a.id: a.name for a in db.query(Account.id, Account.name)}
    for tx in txs:
        tx.account_name = names.get(tx.account_id)
    return txs


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    type: str | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    q = db.query(Transaction)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if from_date:
        q = q.filter(Transaction.date >= from_date)
    if to_date:
        q = q.filter(Transaction.date <= to_date)
    if type:
        q = q.filter(Transaction.type == type)
    if source:
        q = q.filter(Transaction.source == source)
    return _stamp_account_names(db, q.order_by(Transaction.date.desc()).all())


@router.post("/currency-reassign")
def reassign_currency(payload: CurrencyReassign, db: Session = Depends(get_db)) -> dict:
    src = payload.from_currency.strip().upper()
    dst = payload.to_currency.strip().upper()
    if not (re.fullmatch(r"[A-Z]{3}", src) and re.fullmatch(r"[A-Z]{3}", dst)) or src == dst:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_CURRENCY", "message": "Divisas ISO de 3 letras y distintas", "details": {}}},
        )
    q = db.query(Transaction).filter(Transaction.currency == src)
    affected = q.count()
    if payload.preview:
        return {"affected": affected, "applied": False, "from_currency": src, "to_currency": dst}
    backup = create_backup()
    q.update({"currency": dst})
    db.commit()
    return {
        "affected": affected,
        "applied": True,
        "from_currency": src,
        "to_currency": dst,
        "backup_filename": backup["filename"],
    }


@router.post("/reconcile")
def run_reconciliation(db: Session = Depends(get_db)) -> dict:
    """Empareja movimientos bancarios pendientes con sus gastos Monefy."""
    from app.modules.imports.reconciliation import reconcile

    stats = reconcile(db)
    db.commit()
    return stats


@router.get("/reconciliation")
def reconciliation_review(db: Session = Depends(get_db)) -> list[dict]:
    """Movimientos bancarios pendientes de revisar, con su mejor candidato Monefy."""
    from app.modules.imports.reconciliation import find_matches

    matches = {m.bank_tx.id: m for m in find_matches(db)}
    pending = (
        db.query(Transaction)
        .filter(
            Transaction.analytics_scope == "pending",
            Transaction.type.in_(["income", "expense"]),
        )
        .order_by(Transaction.date.desc())
        .all()
    )
    _stamp_account_names(db, pending)
    result = []
    for tx in pending:
        match = matches.get(tx.id)
        result.append(
            {
                "transaction": TransactionOut.model_validate(tx).model_dump(),
                "account_name": tx.account_name,
                "suggestion": {
                    "id": match.monefy_tx.id,
                    "date": match.monefy_tx.date,
                    "description": match.monefy_tx.description,
                    "amount": str(match.monefy_tx.amount),
                    "category_id": match.monefy_tx.category_id,
                    "score": round(match.score, 2),
                }
                if match
                else None,
            }
        )
    return result


@router.patch("/{tx_id}/scope", response_model=TransactionOut)
def resolve_scope(tx_id: str, payload: ScopeUpdate, db: Session = Depends(get_db)) -> Transaction:
    """Resolución manual: contar como personal, excluir o enlazar con un gasto Monefy."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Movimiento no encontrado", "details": {}}},
        )
    if payload.scope not in ("personal", "excluded", "pending"):
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_SCOPE", "message": "Scope debe ser personal, excluded o pending", "details": {}}},
        )
    tx.analytics_scope = payload.scope
    if payload.linked_transaction_id:
        linked = (
            db.query(Transaction).filter(Transaction.id == payload.linked_transaction_id).first()
        )
        if not linked:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "INVALID_LINK", "message": "El movimiento enlazado no existe", "details": {}}},
            )
        tx.linked_transaction_id = linked.id
        tx.analytics_scope = "excluded"
        if linked.category_id and not tx.category_id:
            tx.category_id = linked.category_id
    db.commit()
    db.refresh(tx)
    return _stamp_account_names(db, [tx])[0]


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> Transaction:
    tx = Transaction(**payload.model_dump(), source="manual")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return _stamp_account_names(db, [tx])[0]


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(tx_id: str, payload: TransactionUpdate, db: Session = Depends(get_db)) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Movimiento no encontrado", "details": {}}},
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return _stamp_account_names(db, [tx])[0]


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: str, db: Session = Depends(get_db)) -> None:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Movimiento no encontrado", "details": {}}},
        )
    db.delete(tx)
    db.commit()
