"""Perfiles de formato bancario para el centro de importación.

Cada perfil declara la firma de cabeceras que lo identifica y el mapeo de
columnas al modelo normalizado. La detección es por subconjunto: si todas las
cabeceras requeridas están presentes, el perfil aplica. Si ninguno encaja se
usa el mapeo genérico (primeras columnas fecha/importe), como hasta ahora.
"""

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FormatProfile:
    name: str
    source_type: str
    required_columns: frozenset[str]
    mapping: dict[str, str | None]
    date_formats: tuple[str, ...] = ("%d/%m/%Y",)
    # Columna de estado y valores que se importan; el resto de filas se omiten.
    status_column: str | None = None
    status_allowed: frozenset[str] = field(default_factory=frozenset)
    # Columna de comisión que se resta del importe (Revolut).
    fee_column: str | None = None
    # Descripciones que son traspasos internos (recargas, vaults), no ingreso/gasto.
    transfer_patterns: tuple[str, ...] = ()
    # Divisa real de la fuente cuando el fichero miente (Monefy exporta 'USD' siendo EUR).
    force_currency: str | None = None

    def is_transfer(self, description: str) -> bool:
        return any(re.search(p, description, re.IGNORECASE) for p in self.transfer_patterns)


PROFILES: list[FormatProfile] = [
    FormatProfile(
        name="Monefy",
        source_type="monefy",
        required_columns=frozenset({"date", "account", "category", "amount"}),
        mapping={
            "date": "date",
            "account": "account",
            "category": "category",
            "amount": "amount",
            "currency": "currency",
            "converted_amount": "converted amount",
            "converted_currency": "currency.1",
            "description": "description",
        },
        date_formats=("%d/%m/%Y",),
        force_currency="EUR",
    ),
    FormatProfile(
        name="Revolut",
        source_type="revolut",
        required_columns=frozenset({"Tipo", "Producto", "Fecha de inicio", "Importe", "Divisa"}),
        mapping={
            "date": "Fecha de inicio",
            "amount": "Importe",
            "currency": "Divisa",
            "description": "Descripción",
        },
        date_formats=("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"),
        status_column="State",
        status_allowed=frozenset({"COMPLETED", "COMPLETADO"}),
        fee_column="Comisión",
        transfer_patterns=(
            r"^(una )?recarga",
            r"savings vault",
            r"^to ",
            r"^from ",
        ),
    ),
    FormatProfile(
        name="BBVA",
        source_type="bbva",
        required_columns=frozenset({"F.Valor", "Concepto", "Importe"}),
        mapping={
            "date": "F.Valor",
            "amount": "Importe",
            "currency": "Divisa",
            "description": "Concepto",
        },
        date_formats=("%d/%m/%Y",),
        transfer_patterns=(
            r"^revolut\*\*",
            r"^traspaso",
        ),
    ),
]


def detect_profile(columns: list[str]) -> FormatProfile | None:
    available = {c.strip() for c in columns}
    for profile in PROFILES:
        if profile.required_columns.issubset(available):
            return profile
    return None


def header_row_matches(cells: list[str]) -> bool:
    """True si una fila de celdas parece la cabecera de un perfil conocido."""
    return detect_profile(cells) is not None
