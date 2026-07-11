"""Motor determinista de intereses de cuentas remuneradas (INV-4). Spec §2.3.

Sin IA, sin red (salvo el histórico del tipo ya cacheado por reference_rate_service).
Interés compuesto mensual; el tipo anual de cada mes es el vigente el último día del mes
(fijo, manual o BCE + spread_bps). Las aportaciones/retiradas salen de Transaction
(type=transfer) sobre la Account (spec §2.2) y se aplican al cierre del mes.

Todo en Decimal; nunca float en el cálculo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.modules.investments.reference_rate_service import ECB_DFR, get_rate_on

_CENTS = Decimal("0.01")
_HUNDRED = Decimal("100")
_TWELVE = Decimal("12")


@dataclass
class SavingsInputs:
    opened_at: date
    start_balance: Decimal
    rate_source: str            # ecb_deposit_facility | fixed | manual
    fixed_rate: Decimal | None  # % anual (fixed | manual)
    spread_bps: int             # puntos básicos sobre la referencia
    account_id: str | None = None


@dataclass
class MonthPoint:
    month: str                # "YYYY-MM"
    balance_start: Decimal
    annual_rate: Decimal      # % vigente ese mes
    interest: Decimal
    contributions: Decimal
    balance_end: Decimal


@dataclass
class SavingsSchedule:
    points: list[MonthPoint]
    total_interest: Decimal
    total_contributions: Decimal
    current_balance: Decimal
    current_rate: Decimal | None


def _add_month(d: date) -> date:
    return date(d.year + (d.month // 12), (d.month % 12) + 1, 1)


def _annual_rate_for(db: Session | None, inputs: SavingsInputs, on_day: date) -> Decimal:
    if inputs.rate_source == "ecb_deposit_facility":
        base = get_rate_on(db, on_day, ECB_DFR) if db is not None else None
        base = base if base is not None else Decimal("0")
        return base + Decimal(inputs.spread_bps) / _HUNDRED
    # fixed | manual: tipo introducido por el usuario
    return inputs.fixed_rate if inputs.fixed_rate is not None else Decimal("0")


def current_annual_rate(db: Session | None, config, on_day: date | None = None) -> Decimal:
    """Tipo anual vigente hoy de una SavingsAccountConfig (seam para consumidores externos,
    p.ej. la comparativa 'Letras vs tu ahorro' de Market Intelligence)."""
    on_day = on_day or date.today()
    inputs = SavingsInputs(
        opened_at=config.opened_at or on_day, start_balance=Decimal("0"),
        rate_source=config.rate_source, fixed_rate=config.fixed_rate,
        spread_bps=config.spread_bps, account_id=config.account_id,
    )
    return _annual_rate_for(db, inputs, on_day)


def _contributions_by_month(db: Session | None, inputs: SavingsInputs) -> dict[str, Decimal]:
    """Suma neta de transfers por mes 'YYYY-MM' sobre la Account (spec §2.2).
    El signo del importe marca aportación (+) o retirada (−)."""
    out: dict[str, Decimal] = {}
    if db is None or inputs.account_id is None:
        return out
    txs = (
        db.query(Transaction)
        .filter(Transaction.account_id == inputs.account_id, Transaction.type == "transfer")
        .all()
    )
    for tx in txs:
        try:
            key = tx.date[:7]  # 'YYYY-MM' de la fecha ISO string
        except (TypeError, IndexError):
            continue
        out[key] = out.get(key, Decimal("0")) + tx.amount
    return out


def compute_schedule(db: Session | None, inputs: SavingsInputs, as_of: date | None = None) -> SavingsSchedule:
    """Calendario mensual de intereses desde opened_at hasta as_of (hoy por defecto)."""
    as_of = as_of or date.today()
    contributions = _contributions_by_month(db, inputs)

    balance = inputs.start_balance
    total_interest = Decimal("0")
    total_contrib = Decimal("0")
    points: list[MonthPoint] = []
    last_rate: Decimal | None = None

    month = date(inputs.opened_at.year, inputs.opened_at.month, 1)
    while month <= as_of:
        # Spec §2.3: tipo vigente el último día del mes.
        month_end = min(_add_month(month) - timedelta(days=1), as_of)
        annual = _annual_rate_for(db, inputs, month_end)
        last_rate = annual
        monthly_factor = (annual / _HUNDRED) / _TWELVE
        interest = (balance * monthly_factor).quantize(_CENTS)
        contrib = contributions.get(f"{month.year:04d}-{month.month:02d}", Decimal("0"))
        balance_end = (balance + interest + contrib).quantize(_CENTS)
        points.append(MonthPoint(
            month=f"{month.year:04d}-{month.month:02d}",
            balance_start=balance.quantize(_CENTS),
            annual_rate=annual,
            interest=interest,
            contributions=contrib,
            balance_end=balance_end,
        ))
        total_interest += interest
        total_contrib += contrib
        balance = balance_end
        month = _add_month(month)

    return SavingsSchedule(
        points=points,
        total_interest=total_interest.quantize(_CENTS),
        total_contributions=total_contrib.quantize(_CENTS),
        current_balance=balance.quantize(_CENTS),
        current_rate=last_rate,
    )


def estimate_start_balance(
    db: Session | None,
    inputs: SavingsInputs,
    current_balance: Decimal,
    as_of: date | None = None,
) -> Decimal:
    """Modo inverso (spec §2.3): dado el saldo actual y opened_at, retro-calcula el
    saldo inicial asumiendo sin movimientos. Se marca como estimado en la capa API."""
    # El motor es lineal en start_balance sin aportaciones; usamos un probe grande para
    # que el redondeo a céntimos sea despreciable frente al factor de crecimiento.
    probe_start = Decimal("1000000")
    probe = SavingsInputs(
        opened_at=inputs.opened_at, start_balance=probe_start,
        rate_source=inputs.rate_source, fixed_rate=inputs.fixed_rate,
        spread_bps=inputs.spread_bps, account_id=None,  # sin movimientos
    )
    factor = compute_schedule(db, probe, as_of).current_balance / probe_start
    if factor <= 0:
        return current_balance
    return (current_balance / factor).quantize(_CENTS)
