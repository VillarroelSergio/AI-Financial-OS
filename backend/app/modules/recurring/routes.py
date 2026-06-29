from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.models.recurring_transaction import RecurringTransaction
from app.modules.recurring.schemas import (
    CalendarEvent, RecurringCreate, RecurringOut, RecurringUpdate,
)

router = APIRouter()


def _next_occurrences(rt: RecurringTransaction, from_date: date, until: date) -> list[date]:
    """Generate all occurrence dates for a recurring transaction in [from_date, until]."""
    dates: list[date] = []
    cursor = rt.next_date
    # Guard: advance cursor to from_date
    while cursor < from_date:
        cursor = _advance(rt, cursor)
    while cursor <= until:
        dates.append(cursor)
        cursor = _advance(rt, cursor)
    return dates


def _advance(rt: RecurringTransaction, current: date) -> date:
    if rt.frequency == "weekly":
        return current + timedelta(weeks=1)
    elif rt.frequency == "monthly":
        m = current.month + 1
        y = current.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        d = min(rt.day_of_month or current.day, 28)
        return date(y, m, d)
    elif rt.frequency == "yearly":
        return date(current.year + 1, current.month, current.day)
    return current + timedelta(days=30)


@router.get("", response_model=list[RecurringOut])
def list_recurring(db: Session = Depends(get_db)) -> list[RecurringOut]:
    return db.query(RecurringTransaction).order_by(RecurringTransaction.next_date).all()


@router.post("", response_model=RecurringOut, status_code=201)
def create_recurring(body: RecurringCreate, db: Session = Depends(get_db)) -> RecurringOut:
    rt = RecurringTransaction(id=str(uuid.uuid4()), **body.model_dump())
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


@router.put("/{rt_id}", response_model=RecurringOut)
def update_recurring(rt_id: str, body: RecurringUpdate, db: Session = Depends(get_db)) -> RecurringOut:
    rt = db.get(RecurringTransaction, rt_id)
    if not rt:
        raise HTTPException(status_code=404, detail="RecurringTransaction not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rt, field, value)
    rt.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rt)
    return rt


@router.delete("/{rt_id}", status_code=204)
def delete_recurring(rt_id: str, db: Session = Depends(get_db)) -> None:
    rt = db.get(RecurringTransaction, rt_id)
    if not rt:
        raise HTTPException(status_code=404, detail="RecurringTransaction not found")
    db.delete(rt)
    db.commit()


@router.get("/calendar", response_model=list[CalendarEvent])
def get_calendar(
    days: int = Query(default=60, ge=1, le=365),
    db: Session = Depends(get_db),
) -> list[CalendarEvent]:
    from_date = date.today()
    until = from_date + timedelta(days=days)

    rts = db.query(RecurringTransaction).filter(RecurringTransaction.active == True).all()
    events: list[CalendarEvent] = []

    for rt in rts:
        cat = db.get(Category, rt.category_id) if rt.category_id else None
        for occ in _next_occurrences(rt, from_date, until):
            events.append(CalendarEvent(
                recurring_id=rt.id,
                name=rt.name,
                amount=float(rt.amount),
                type=rt.type,
                date=occ,
                category_name=cat.name if cat else None,
            ))

    return sorted(events, key=lambda e: e.date)
