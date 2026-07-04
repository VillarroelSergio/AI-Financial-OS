import hashlib
import json
import re
from datetime import date as date_cls, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.household_bill import HouseholdBill
from app.models.import_batch import ImportBatch, ImportRow
from app.models.transaction import Transaction
from app.modules.imports.auto_categorizer import auto_category
from app.modules.imports.bill_classifier import SERVICE_LABELS, classify_bill
from app.modules.imports.schemas import ConfirmImport, ImportBatchOut
from app.modules.imports.format_profiles import PROFILES, detect_profile
from app.modules.imports.service import (
    MONEFY_COLUMNS,
    dumps,
    normalize_row,
    read_table,
)

router = APIRouter()


def fail(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status, detail={"error": {"code": code, "message": message, "details": {}}}
    )


@router.get("", response_model=list[ImportBatchOut])
def history(db: Session = Depends(get_db)) -> list[ImportBatch]:
    return db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).all()


@router.post("/preview")
async def preview(
    source_type: str = Form("auto"), file: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict:
    content = await file.read()
    try:
        columns, rows = read_table(file.filename, content)
    except ValueError as exc:
        raise fail(422, "INVALID_CSV", str(exc)) from exc
    # Detección automática por cabeceras; sin perfil se usa el mapeo genérico.
    profile = detect_profile(columns)
    if profile:
        mapping = dict(profile.mapping)
    else:
        mapping = {"date": columns[0], "amount": columns[1] if len(columns) > 1 else ""}
    batch = ImportBatch(
        source_name=profile.name if profile else "Genérico",
        source_type=profile.source_type if profile else "generic_csv",
        file_name=file.filename or "import.csv",
        file_hash=hashlib.sha256(content).hexdigest(),
        rows_total=len(rows),
        mapping_json=dumps(mapping),
    )
    db.add(batch)
    db.flush()
    result_rows, warning_count, invalid_count, skipped_count = [], 0, 0, 0
    # Hasta 100 filas por estado, para que los filtros del preview siempre tengan muestra.
    shown_by_status: dict[str, int] = {}
    for number, raw in enumerate(rows, 2):
        skipped_reason = None
        if profile and profile.status_column:
            state = raw.get(profile.status_column, "").strip().upper()
            if state and state not in profile.status_allowed:
                skipped_reason = f"Operación no completada ({state})"
        normalized, errors, warnings = normalize_row(raw, mapping, profile)
        # Archivos sin columna de categoría: se infiere por el comercio.
        if not normalized["category"] and normalized["type"] != "transfer":
            normalized["category"] = auto_category(normalized["description"]) or ""
        if not skipped_reason and not errors and normalized["type"] == "expense":
            bill = classify_bill(normalized["description"])
            if bill:
                warnings.append(f"Factura detectada: {SERVICE_LABELS[bill[0]]} · {bill[1]}")
        duplicate = (
            db.query(Transaction)
            .filter(Transaction.external_id == normalized["duplicate_hash"])
            .first()
            is not None
        )
        if skipped_reason:
            status = "skipped"
            skipped_count += 1
        elif errors:
            status = "invalid"
            invalid_count += 1
        elif duplicate:
            status = "duplicate"
        else:
            status = "valid"
        warning_count += len(warnings) + int(duplicate)
        row = ImportRow(
            import_batch_id=batch.id,
            row_number=number,
            raw_payload_json=dumps(raw),
            normalized_payload_json=dumps(normalized),
            status=status,
            error_message=skipped_reason or "; ".join(errors) or None,
        )
        db.add(row)
        if shown_by_status.get(status, 0) < 100:
            shown_by_status[status] = shown_by_status.get(status, 0) + 1
            result_rows.append(
                {
                    "row_number": number,
                    **normalized,
                    "status": status,
                    "errors": ([skipped_reason] if skipped_reason else errors),
                    "warnings": warnings + (["Posible duplicado"] if duplicate else []),
                }
            )
    batch.status = "validated"
    batch.rows_failed = invalid_count
    db.commit()
    return {
        "import_batch_id": batch.id,
        "source_type": batch.source_type,
        "detected_source": profile.name if profile else None,
        "columns": columns,
        "detected_monefy": MONEFY_COLUMNS.issubset(set(columns)),
        "rows_total": len(rows),
        "rows_valid": len(rows) - invalid_count - skipped_count,
        "rows_invalid": invalid_count,
        "rows_skipped": skipped_count,
        "warnings_count": warning_count,
        "preview_rows": result_rows,
        "mapping": mapping,
    }


@router.post("/{batch_id}/confirm")
def confirm(batch_id: str, payload: ConfirmImport, db: Session = Depends(get_db)) -> dict:
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch or batch.status != "validated":
        raise fail(409, "INVALID_STATE", "La importación no está lista para confirmar")
    mapping = (
        payload.mapping.model_dump() if payload.mapping else json.loads(batch.mapping_json or "{}")
    )
    currency_override = (payload.currency_override or "").strip().upper() or None
    if currency_override and not re.fullmatch(r"[A-Z]{3}", currency_override):
        raise fail(422, "INVALID_CURRENCY", "La divisa debe ser un código ISO de 3 letras")
    target_account = None
    if payload.account_id:
        target_account = db.query(Account).filter(Account.id == payload.account_id).first()
        if not target_account:
            raise fail(422, "INVALID_ACCOUNT", "La cuenta seleccionada no existe")
    profile = next((p for p in PROFILES if p.source_type == batch.source_type), None)
    rows = db.query(ImportRow).filter(ImportRow.import_batch_id == batch_id).all()
    imported = 0
    bills_created = 0
    new_txs: list[Transaction] = []
    for row in rows:
        raw = json.loads(row.raw_payload_json)
        normalized, errors, _ = normalize_row(raw, mapping, profile)
        if errors or row.status != "valid":
            continue
        if currency_override:
            normalized["currency"] = currency_override
        if target_account:
            account = target_account
        else:
            account_name = normalized["account"]
            account = db.query(Account).filter(Account.name == account_name).first()
            if not account:
                account = Account(
                    name=account_name,
                    type="cash" if "efectivo" in account_name.casefold() else "other",
                    currency=normalized["currency"],
                )
                db.add(account)
                db.flush()
        # Adeudos/recibos domésticos: categoría automática + alta en Facturas.
        bill = classify_bill(normalized["description"]) if normalized["type"] == "expense" else None
        if bill and not normalized["category"]:
            normalized["category"] = SERVICE_LABELS[bill[0]]
        # Archivos sin columna de categoría: se infiere por el comercio.
        if not normalized["category"] and normalized["type"] != "transfer":
            normalized["category"] = auto_category(normalized["description"]) or ""
        category = None
        if normalized["category"]:
            category = db.query(Category).filter(Category.name == normalized["category"]).first()
            if not category:
                category = Category(
                    name=normalized["category"], type=normalized["type"], is_system=False
                )
                db.add(category)
                db.flush()
        # Carga única: todo movimiento importado cuenta en la analítica personal,
        # salvo los traspasos entre cuentas propias.
        scope = "excluded" if normalized["type"] == "transfer" else "personal"
        tx = Transaction(
            account_id=account.id,
            category_id=category.id if category else None,
            date=normalized["date"],
            description=normalized["description"],
            amount=Decimal(normalized["amount"]),
            currency=normalized["currency"],
            converted_amount=Decimal(normalized["converted_amount"])
            if normalized["converted_amount"]
            else None,
            converted_currency=normalized["converted_currency"],
            type=normalized["type"],
            source="csv",
            source_name=batch.source_name,
            external_id=normalized["duplicate_hash"],
            import_batch_id=batch.id,
            analytics_scope=scope,
        )
        db.add(tx)
        new_txs.append(tx)
        if bill:
            service_type, provider = bill
            bill_date = date_cls.fromisoformat(normalized["date"])
            amount_abs = abs(Decimal(normalized["amount"]))
            exists = (
                db.query(HouseholdBill)
                .filter(
                    HouseholdBill.provider == provider,
                    HouseholdBill.service_type == service_type,
                    HouseholdBill.period_end == bill_date,
                    HouseholdBill.amount == amount_abs,
                )
                .first()
            )
            if not exists:
                db.add(
                    HouseholdBill(
                        provider=provider,
                        service_type=service_type,
                        period_start=bill_date,
                        period_end=bill_date,
                        amount=amount_abs,
                        currency=normalized["currency"],
                        category_id=category.id if category else None,
                        paid_at=bill_date,
                        notes=f"Detectada en importación: {normalized['description']}",
                    )
                )
                bills_created += 1
        row.status = "imported"
        row.normalized_payload_json = dumps(normalized)
        imported += 1
    db.flush()  # asigna ids a las nuevas transacciones antes de emparejar traspasos
    # Traspasos entre cuentas: un movimiento con contrapartida de importe opuesto
    # en otra cuenta (±3 días) no es ingreso ni gasto; ambos pasan a "transfer".
    # ponytail: emparejado exacto por importe; si hacen falta comisiones intermedias, ampliar aquí.
    transfers = 0
    used_ids: set[str] = set()
    for tx in new_txs:
        if tx.type not in ("income", "expense"):
            continue
        tx_date = date_cls.fromisoformat(tx.date)
        lo = (tx_date - timedelta(days=3)).isoformat()
        hi = (tx_date + timedelta(days=3)).isoformat()
        counterpart = (
            db.query(Transaction)
            .filter(
                Transaction.account_id != tx.account_id,
                Transaction.amount == -tx.amount,
                Transaction.currency == tx.currency,
                Transaction.type.in_(["income", "expense"]),
                Transaction.date >= lo,
                Transaction.date <= hi,
                ~Transaction.id.in_(used_ids),
            )
            .first()
        )
        if counterpart is not None:
            tx.type = "transfer"
            counterpart.type = "transfer"
            tx.analytics_scope = "excluded"
            counterpart.analytics_scope = "excluded"
            used_ids.update({tx.id, counterpart.id})
            transfers += 1
    batch.status = "imported"
    batch.rows_imported = imported
    batch.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "import_batch_id": batch.id,
        "status": batch.status,
        "rows_imported": imported,
        "rows_skipped": batch.rows_total - imported,
        "transfers_detected": transfers,
        "bills_created": bills_created,
    }


@router.post("/{batch_id}/rollback")
def rollback(batch_id: str, db: Session = Depends(get_db)) -> dict:
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch or batch.status != "imported":
        raise fail(409, "INVALID_STATE", "Solo se puede revertir una importación completada")
    deleted = db.query(Transaction).filter(Transaction.import_batch_id == batch_id).delete()
    db.query(ImportRow).filter(ImportRow.import_batch_id == batch_id).update({"status": "valid"})
    batch.status = "rolled_back"
    batch.rows_imported = 0
    batch.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"import_batch_id": batch.id, "status": batch.status, "rows_removed": deleted}
