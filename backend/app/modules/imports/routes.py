import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.import_batch import ImportBatch, ImportRow
from app.models.transaction import Transaction
from app.modules.imports.schemas import ConfirmImport, ImportBatchOut
from app.modules.imports.service import (
    DEFAULT_MONEFY_MAPPING,
    MONEFY_COLUMNS,
    dumps,
    normalize_row,
    read_csv,
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
    source_type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict:
    if source_type not in {"monefy", "generic_csv"}:
        raise fail(400, "UNSUPPORTED_SOURCE", "Fuente de importación no soportada")
    content = await file.read()
    try:
        columns, rows = read_csv(content)
    except ValueError as exc:
        raise fail(422, "INVALID_CSV", str(exc)) from exc
    if source_type == "monefy" and not {"date", "amount"}.issubset(set(columns)):
        raise fail(422, "INVALID_COLUMNS", "El CSV de Monefy requiere date y amount")
    mapping = (
        DEFAULT_MONEFY_MAPPING
        if source_type == "monefy"
        else {"date": columns[0], "amount": columns[1] if len(columns) > 1 else ""}
    )
    batch = ImportBatch(
        source_name="Monefy" if source_type == "monefy" else "CSV genérico",
        source_type=source_type,
        file_name=file.filename or "import.csv",
        file_hash=hashlib.sha256(content).hexdigest(),
        rows_total=len(rows),
        mapping_json=dumps(mapping),
    )
    db.add(batch)
    db.flush()
    result_rows, warning_count, invalid_count = [], 0, 0
    for number, raw in enumerate(rows, 2):
        normalized, errors, warnings = normalize_row(raw, mapping)
        duplicate = (
            db.query(Transaction)
            .filter(Transaction.external_id == normalized["duplicate_hash"])
            .first()
            is not None
        )
        status = "invalid" if errors else "duplicate" if duplicate else "valid"
        invalid_count += bool(errors)
        warning_count += len(warnings) + int(duplicate)
        row = ImportRow(
            import_batch_id=batch.id,
            row_number=number,
            raw_payload_json=dumps(raw),
            normalized_payload_json=dumps(normalized),
            status=status,
            error_message="; ".join(errors) or None,
        )
        db.add(row)
        if len(result_rows) < 100:
            result_rows.append(
                {
                    "row_number": number,
                    **normalized,
                    "status": status,
                    "errors": errors,
                    "warnings": warnings + (["Posible duplicado"] if duplicate else []),
                }
            )
    batch.status = "validated"
    batch.rows_failed = invalid_count
    db.commit()
    return {
        "import_batch_id": batch.id,
        "source_type": source_type,
        "columns": columns,
        "detected_monefy": MONEFY_COLUMNS.issubset(set(columns)),
        "rows_total": len(rows),
        "rows_valid": len(rows) - invalid_count,
        "rows_invalid": invalid_count,
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
    rows = db.query(ImportRow).filter(ImportRow.import_batch_id == batch_id).all()
    imported = 0
    for row in rows:
        raw = json.loads(row.raw_payload_json)
        normalized, errors, _ = normalize_row(raw, mapping)
        if errors or row.status == "duplicate":
            continue
        if currency_override:
            normalized["currency"] = currency_override
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
        category = None
        if normalized["category"]:
            category = db.query(Category).filter(Category.name == normalized["category"]).first()
            if not category:
                category = Category(
                    name=normalized["category"], type=normalized["type"], is_system=False
                )
                db.add(category)
                db.flush()
        db.add(
            Transaction(
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
            )
        )
        row.status = "imported"
        row.normalized_payload_json = dumps(normalized)
        imported += 1
    batch.status = "imported"
    batch.rows_imported = imported
    batch.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "import_batch_id": batch.id,
        "status": batch.status,
        "rows_imported": imported,
        "rows_skipped": batch.rows_total - imported,
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
