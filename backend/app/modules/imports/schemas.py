from datetime import datetime

from pydantic import BaseModel


class ColumnMapping(BaseModel):
    date: str
    amount: str
    account: str | None = None
    category: str | None = None
    currency: str | None = None
    description: str | None = None
    converted_amount: str | None = None
    converted_currency: str | None = None


class ConfirmImport(BaseModel):
    mapping: ColumnMapping | None = None
    # Fuerza la divisa de todos los movimientos importados (p. ej. CSV de Monefy
    # etiquetado en USD cuando los importes reales son EUR).
    currency_override: str | None = None
    # Asigna todos los movimientos a esta cuenta en lugar de la columna del archivo.
    account_id: str | None = None


class ImportBatchOut(BaseModel):
    id: str
    source_name: str
    source_type: str
    file_name: str
    status: str
    rows_total: int
    rows_imported: int
    rows_failed: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
