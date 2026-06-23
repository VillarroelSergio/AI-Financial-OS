from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.modules.transactions.schemas import TransactionCreate, TransactionOut, TransactionUpdate

router = APIRouter()


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
    return q.order_by(Transaction.date.desc()).all()


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> Transaction:
    tx = Transaction(**payload.model_dump(), source="manual")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


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
    return tx


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
