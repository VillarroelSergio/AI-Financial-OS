import csv
import hashlib
import io
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.modules.imports.format_profiles import FormatProfile

MAX_FILE_BYTES = 10 * 1024 * 1024

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
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("El archivo supera el límite de 10 MB")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar codificado en UTF-8") from exc


def _cell_to_str(value: object) -> str:
    """Normaliza celdas de Excel al mismo formato de texto que produce un CSV."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_xlsx(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("El archivo supera el límite de 10 MB")
    import openpyxl

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError("No se pudo leer el archivo XLSX") from exc
    from app.modules.imports.format_profiles import header_row_matches

    sheet = workbook.worksheets[0]
    all_rows = list(sheet.iter_rows(values_only=True))
    # Los extractos de banco (p. ej. BBVA) traen filas de preámbulo antes de la
    # cabecera: buscamos la primera fila que case con un perfil conocido y, si
    # ninguna casa, la primera fila con al menos dos celdas de texto.
    header_index = None
    fallback_index = None
    for index, values in enumerate(all_rows[:20]):
        cells = [_cell_to_str(v) for v in (values or [])]
        if header_row_matches([c for c in cells if c]):
            header_index = index
            break
        if fallback_index is None and sum(1 for c in cells if c) >= 2:
            fallback_index = index
    if header_index is None:
        header_index = fallback_index if fallback_index is not None else 0
    raw_columns = all_rows[header_index] if len(all_rows) > header_index else []
    rows_iter = iter(all_rows[header_index + 1 :])
    seen: dict[str, int] = {}
    columns: list[str] = []
    for raw_column in raw_columns:
        column = _cell_to_str(raw_column)
        occurrence = seen.get(column, 0)
        columns.append(column if occurrence == 0 else f"{column}.{occurrence}")
        seen[column] = occurrence + 1
    if not any(columns):
        raise ValueError("El XLSX no contiene cabeceras")
    rows = [
        {
            column: _cell_to_str(values[index] if index < len(values) else None)
            for index, column in enumerate(columns)
        }
        for values in rows_iter
        if values and any(_cell_to_str(v) for v in values)
    ]
    if not rows:
        raise ValueError("El XLSX no contiene movimientos")
    return columns, rows


def read_table(filename: str | None, content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Lee CSV o XLSX y devuelve columnas + filas normalizadas a texto."""
    if (filename or "").lower().endswith(".xlsx"):
        return read_xlsx(content)
    return read_csv(content)


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


def parse_date(raw: str, date_formats: tuple[str, ...]) -> str | None:
    """Devuelve la fecha en ISO probando los formatos del perfil."""
    for fmt in date_formats:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw).date().isoformat()
    except ValueError:
        return None


def parse_amount(raw: str) -> Decimal:
    """Acepta '1.234,56', '1,234.56', '-20.5' y símbolos de divisa sueltos."""
    s = raw.replace("\xa0", "").replace(" ", "").replace("€", "").replace("$", "").replace("£", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return Decimal(s)


def normalize_row(
    raw: dict[str, str],
    mapping: dict[str, str | None],
    profile: FormatProfile | None = None,
    occurrence: int = 0,
) -> tuple[dict, list[str], list[str]]:
    date_formats = profile.date_formats if profile else ("%d/%m/%Y",)
    fee_column = profile.fee_column if profile else None
    errors: list[str] = []
    warnings: list[str] = []

    def value(key: str) -> str:
        return raw.get(mapping.get(key) or "", "").strip()

    date_raw, amount_raw = value("date"), value("amount")
    date = parse_date(date_raw, date_formats)
    if date is None:
        errors.append("Fecha no válida")
        date = date_raw
    try:
        amount = parse_amount(amount_raw)
        if fee_column:
            fee_raw = raw.get(fee_column, "").strip()
            if fee_raw:
                try:
                    amount -= parse_amount(fee_raw)
                except InvalidOperation:
                    warnings.append("Comisión no numérica; se ignora")
        if amount == 0:
            errors.append("El importe no puede ser cero")
    except InvalidOperation:
        errors.append("Importe no numérico")
        amount = Decimal("0")
    currency = (value("currency") or "EUR").upper()
    if profile and profile.force_currency:
        currency = profile.force_currency
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
    # Recargas, vaults y traspasos entre cuentas propias no son ingreso ni gasto.
    if profile and profile.is_transfer(normalized["description"]):
        normalized["type"] = "transfer"
    duplicate_key = "|".join(
        [date, str(amount), description.casefold().strip(), category.casefold().strip()]
    )
    # Ocurrencia n>0 dentro del mismo archivo: sufijo para no colisionar con la
    # primera. La ocurrencia 0 conserva el hash histórico (retrocompatible).
    if occurrence:
        duplicate_key += f"|{occurrence}"
    normalized["duplicate_hash"] = hashlib.sha256(duplicate_key.encode()).hexdigest()
    return normalized, errors, warnings


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
