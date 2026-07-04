from __future__ import annotations

import calendar
import uuid
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.modules.recurring.schemas import (
    CalendarEvent, RecurringCandidate, RecurringCreate, RecurringOut, RecurringUpdate,
)

router = APIRouter()


def _next_occurrences(rt: RecurringTransaction, from_date: date, until: date) -> list[date]:
    """Generate all occurrence dates for a recurring transaction in [from_date, until]."""
    dates: list[date] = []
    cursor = rt.next_date
    # Guard: advance cursor to from_date
    while cursor < from_date:
        cursor = _advance(cursor, rt.frequency, rt.day_of_month)
    while cursor <= until:
        dates.append(cursor)
        cursor = _advance(cursor, rt.frequency, rt.day_of_month)
    return dates


def _advance(current: date, frequency: str, day_of_month: int | None = None) -> date:
    if frequency == "weekly":
        return current + timedelta(weeks=1)
    elif frequency == "monthly":
        target_day = day_of_month or current.day
        m = current.month + 1
        y = current.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        max_day = calendar.monthrange(y, m)[1]
        return date(y, m, min(target_day, max_day))
    elif frequency == "yearly":
        return date(current.year + 1, current.month, current.day)
    return current + timedelta(days=30)


def _parse_tx_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def _normalize_description(value: str) -> str:
    text = re.sub(r"\d+", "", value.lower())
    text = re.sub(r"[^a-záéíóúüñ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _frequency_from_intervals(intervals: list[int]) -> tuple[str, float] | None:
    if not intervals:
        return None
    avg = sum(intervals) / len(intervals)
    if 24 <= avg <= 38:
        return "monthly", avg
    if 5 <= avg <= 9:
        return "weekly", avg
    if 330 <= avg <= 400:
        return "yearly", avg
    return None


@router.get("", response_model=list[RecurringOut])
def list_recurring(db: Session = Depends(get_db)) -> list[RecurringOut]:
    return db.query(RecurringTransaction).order_by(RecurringTransaction.next_date).all()


@router.get("/candidates", response_model=list[RecurringCandidate])
def list_recurring_candidates(
    min_occurrences: int = Query(default=2, ge=2, le=12),
    db: Session = Depends(get_db),
) -> list[RecurringCandidate]:
    transactions = (
        db.query(Transaction)
        .filter(Transaction.type.in_(["income", "expense"]))
        .order_by(Transaction.date.asc())
        .all()
    )
    grouped: dict[tuple[str, str], list[Transaction]] = defaultdict(list)
    for tx in transactions:
        normalized = _normalize_description(tx.description)
        if len(normalized) < 3:
            continue
        grouped[(normalized, tx.type)].append(tx)

    candidates: list[RecurringCandidate] = []
    for (normalized, tx_type), items in grouped.items():
        dated = [(tx, _parse_tx_date(tx.date)) for tx in items]
        dated = [(tx, tx_date) for tx, tx_date in dated if tx_date is not None]
        if len(dated) < min_occurrences:
            continue
        dated.sort(key=lambda item: item[1])
        dates = [tx_date for _, tx_date in dated]
        intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        frequency = _frequency_from_intervals(intervals)
        if not frequency:
            continue
        frequency_name, avg_interval = frequency
        amounts = [abs(Decimal(str(tx.amount))) for tx, _ in dated]
        avg_amount = sum(amounts) / Decimal(len(amounts))
        max_deviation = max((abs(amount - avg_amount) / avg_amount for amount in amounts), default=Decimal("0")) if avg_amount else Decimal("1")
        if max_deviation > Decimal("0.25"):
            continue
        last_tx, last_date = dated[-1]
        common_day = round(sum(d.day for d in dates) / len(dates)) if frequency_name == "monthly" else None
        confidence = min(0.95, 0.45 + (len(dated) * 0.12) + max(0, 0.25 - float(max_deviation)))
        candidates.append(RecurringCandidate(
            id=f"{normalized}:{tx_type}",
            name=last_tx.description[:80],
            description=f"Detectado por {len(dated)} movimientos similares cada {avg_interval:.0f} dias.",
            amount=avg_amount.quantize(Decimal("0.01")),
            amount_min=min(amounts).quantize(Decimal("0.01")),
            amount_max=max(amounts).quantize(Decimal("0.01")),
            currency=last_tx.currency,
            type=tx_type,
            frequency=frequency_name,
            next_date=_advance(last_date, frequency_name, common_day),
            confidence=round(confidence, 2),
            transaction_count=len(dated),
            transaction_ids=[tx.id for tx, _ in dated],
            category_id=last_tx.category_id,
            account_id=last_tx.account_id,
            evidence=[f"{tx.date} · {tx.description} · {tx.amount} {tx.currency}" for tx, _ in dated[-5:]],
        ))
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


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
