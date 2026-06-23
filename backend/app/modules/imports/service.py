import csv
import hashlib
import io
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

MONEFY_COLUMNS = {
    "date",
    "account",
    "category",
    "amount",
    "currency",
    "converted amount",
    "currency.1",
    "description",
}
DEFAULT_MONEFY_MAPPING = {
    "date": "date",
    "account": "account",
    "category": "category",
    "amount": "amount",
    "currency": "currency",
    "converted_amount": "converted amount",
    "converted_currency": "currency.1",
    "description": "description",
}


def decode_csv(content: bytes) -> str:
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("El archivo supera el límite de 10 MB")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar codificado en UTF-8") from exc


def read_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = decode_csv(content)
    rows_reader = csv.reader(io.StringIO(text))
    raw_columns = next(rows_reader, [])
    seen: dict[str, int] = {}
    columns: list[str] = []
    for raw_column in raw_columns:
        column = raw_column.strip()
        occurrence = seen.get(column, 0)
        columns.append(column if occurrence == 0 else f"{column}.{occurrence}")
        seen[column] = occurrence + 1
    if not columns:
        raise ValueError("El CSV no contiene cabeceras")
    rows = [
        {
            column: (values[index] if index < len(values) else "").strip()
            for index, column in enumerate(columns)
        }
        for values in rows_reader
        if any(value.strip() for value in values)
    ]
    if not rows:
        raise ValueError("El CSV no contiene movimientos")
    return columns, rows


def normalize_row(
    raw: dict[str, str], mapping: dict[str, str | None]
) -> tuple[dict, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    def value(key: str) -> str:
        return raw.get(mapping.get(key) or "", "").strip()

    date_raw, amount_raw = value("date"), value("amount")
    try:
        date = datetime.strptime(date_raw, "%d/%m/%Y").date().isoformat()
    except ValueError:
        errors.append("Fecha no válida; usa D/M/YYYY")
        date = date_raw
    try:
        amount = Decimal(amount_raw.replace(" ", "").replace(",", "."))
        if amount == 0:
            errors.append("El importe no puede ser cero")
    except InvalidOperation:
        errors.append("Importe no numérico")
        amount = Decimal("0")
    currency = (value("currency") or "EUR").upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        errors.append("Moneda no válida")
    description, category = value("description"), value("category")
    if not description:
        warnings.append("Descripción vacía")
    if not category:
        warnings.append("Categoría vacía")
    normalized = {
        "date": date,
        "amount": str(amount),
        "account": value("account") or "Importado",
        "category": category,
        "currency": currency,
        "description": description or "Movimiento importado",
        "converted_amount": value("converted_amount") or None,
        "converted_currency": value("converted_currency").upper() or None,
        "type": "income" if amount > 0 else "expense",
    }
    duplicate_key = "|".join(
        [date, str(amount), description.casefold().strip(), category.casefold().strip()]
    )
    normalized["duplicate_hash"] = hashlib.sha256(duplicate_key.encode()).hexdigest()
    return normalized, errors, warnings


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
