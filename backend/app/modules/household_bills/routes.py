from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.household_bill import HouseholdBill
from app.modules.household_bills.schemas import (
    HouseholdBillCreate,
    HouseholdBillOut,
    HouseholdBillSummary,
    HouseholdBillSummaryItem,
    HouseholdBillUpdate,
)

router = APIRouter()


@router.get("", response_model=list[HouseholdBillOut])
def list_household_bills(
    service_type: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[HouseholdBill]:
    query = db.query(HouseholdBill)
    if service_type:
        query = query.filter(HouseholdBill.service_type == service_type)
    if provider:
        query = query.filter(HouseholdBill.provider == provider)
    return query.order_by(HouseholdBill.period_end.desc()).all()


@router.post("", response_model=HouseholdBillOut, status_code=201)
def create_household_bill(body: HouseholdBillCreate, db: Session = Depends(get_db)) -> HouseholdBill:
    bill = HouseholdBill(id=str(uuid.uuid4()), **body.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.put("/{bill_id}", response_model=HouseholdBillOut)
def update_household_bill(bill_id: str, body: HouseholdBillUpdate, db: Session = Depends(get_db)) -> HouseholdBill:
    bill = db.get(HouseholdBill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Household bill not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(bill, field, value)
    bill.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(bill)
    return bill


@router.delete("/{bill_id}", status_code=204)
def delete_household_bill(bill_id: str, db: Session = Depends(get_db)) -> None:
    bill = db.get(HouseholdBill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Household bill not found")
    db.delete(bill)
    db.commit()


@router.get("/summary", response_model=HouseholdBillSummary)
def household_bill_summary(db: Session = Depends(get_db)) -> HouseholdBillSummary:
    bills = db.query(HouseholdBill).order_by(HouseholdBill.period_end.asc()).all()
    grouped: dict[tuple[str, str], list[HouseholdBill]] = defaultdict(list)
    for bill in bills:
        grouped[(bill.service_type, bill.provider)].append(bill)

    items: list[HouseholdBillSummaryItem] = []
    for (service_type, provider), entries in grouped.items():
        amounts = [float(entry.amount) for entry in entries]
        last = entries[-1]
        previous = entries[-2] if len(entries) > 1 else None
        previous_amount = float(previous.amount) if previous else None
        change_pct = round((float(last.amount) - previous_amount) / previous_amount * 100, 1) if previous_amount else None
        average = round(sum(amounts) / len(amounts), 2)
        anomaly = bool(change_pct is not None and change_pct >= 20)
        next_estimate = round(float(last.amount if anomaly else average), 2)
        items.append(HouseholdBillSummaryItem(
            service_type=service_type,
            provider=provider,
            bills_count=len(entries),
            last_amount=float(last.amount),
            previous_amount=previous_amount,
            change_pct=change_pct,
            average_amount=average,
            next_estimate=next_estimate,
            anomaly=anomaly,
            latest_period=f"{last.period_start.isoformat()} - {last.period_end.isoformat()}",
        ))

    return HouseholdBillSummary(
        generated_at=datetime.now(timezone.utc),
        total_monthly_estimate=round(sum(item.next_estimate for item in items), 2),
        items=sorted(items, key=lambda item: item.next_estimate, reverse=True),
    )
