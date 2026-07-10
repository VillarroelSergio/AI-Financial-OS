"""Redondeo determinista único y formateo es-ES para insights (INS-1).

Todas las reglas y el review consumen estas funciones: una sola cifra por
concepto, redondeo `ROUND_HALF_UP`, y copy en formato es-ES (coma decimal,
punto de millar). Corrige INS-B1/B2/F1 por construcción.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def round_dec(value: Decimal | float | int | str, places: int = 2) -> Decimal:
    """Redondeo half-up a `places` decimales. Punto de redondeo único del módulo."""
    q = Decimal(1).scaleb(-places)  # 10**-places
    return Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)


def savings_rate_dec(income: Decimal, expense: Decimal) -> Decimal:
    """Tasa de ahorro en % con una única definición de redondeo (1 decimal)."""
    if income <= 0:
        return Decimal("0.0")
    return round_dec((income - expense) / income * 100, 1)


def _es(number: Decimal, decimals: int) -> str:
    """Formatea con coma decimal y punto de millar (es-ES), sin depender de locale del SO."""
    q = round_dec(number, decimals)
    sign = "-" if q < 0 else ""
    digits = f"{abs(q):.{decimals}f}"
    int_part, _, frac = digits.partition(".")
    groups = []
    while len(int_part) > 3:
        groups.insert(0, int_part[-3:])
        int_part = int_part[:-3]
    groups.insert(0, int_part)
    int_es = ".".join(groups)
    return f"{sign}{int_es},{frac}" if decimals else f"{sign}{int_es}"


def fmt_eur(value: Decimal | float | int, decimals: int = 2) -> str:
    return f"{_es(Decimal(str(value)), decimals)} €"


def fmt_pct(value: Decimal | float | int, decimals: int = 1) -> str:
    return f"{_es(Decimal(str(value)), decimals)} %"


def fmt_num(value: Decimal | float | int, decimals: int = 0) -> str:
    return _es(Decimal(str(value)), decimals)


if __name__ == "__main__":
    # ponytail: self-check de las cifras exactas de las capturas (regresión INS-B1/F1)
    income, expense = Decimal("3915.00"), Decimal("1501.25")
    assert savings_rate_dec(income, expense) == Decimal("61.7"), savings_rate_dec(income, expense)
    assert fmt_pct(savings_rate_dec(income, expense)) == "61,7 %"
    assert fmt_eur(Decimal("2413.75")) == "2.413,75 €"
    assert fmt_eur(Decimal("42100")) == "42.100,00 €"
    assert round_dec("61.65", 1) == Decimal("61.7")
    print("formatting self-check OK")
