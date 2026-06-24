"""Economic data service — orchestrates providers, cache, and personal impact."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.economic_data import repository as repo
from app.modules.economic_data.providers.fred_provider import FredProvider
from app.modules.economic_data.providers.stooq_macro_provider import StooqMacroProvider
from app.modules.economic_data.schemas import (
    ImpactItem,
    IndicatorOut,
    MacroSnapshotOut,
    PersonalImpactOut,
    RegionSnapshotOut,
)

logger = logging.getLogger(__name__)

_refresh_lock = threading.Lock()

# ── Indicator catalogue metadata (for ordering within regions) ────────────────
_REGION_ORDER = {
    "ES": ["inflation", "core_inflation", "unemployment", "gdp", "bond_10y", "index", "euribor"],
    "EA": ["inflation", "core_inflation", "unemployment", "gdp", "policy_rate", "bond_10y", "index", "euribor"],
    "US": ["inflation", "core_inflation", "unemployment", "gdp", "policy_rate", "bond_10y", "index"],
}


def _row_to_indicator(row: dict) -> IndicatorOut:
    value = row.get("value")
    prev_value = row.get("prev_value")
    change = round(value - prev_value, 4) if value is not None and prev_value is not None else None
    return IndicatorOut(
        series_id=row["series_id"],
        region=row["region"],
        indicator=row["indicator"],
        name=row["name"],
        value=value,
        prev_value=prev_value,
        change=change,
        period=row.get("period", ""),
        unit=row.get("unit", "%"),
        source=row.get("source", ""),
        observation_date=str(row.get("observation_date", "")),
        is_stale=repo.is_stale(row["series_id"], row["indicator"]),
    )


def _build_snapshot(all_rows: list[dict]) -> MacroSnapshotOut:
    by_region: dict[str, list[IndicatorOut]] = {"ES": [], "EA": [], "US": []}
    for row in all_rows:
        region = row.get("region", "")
        if region in by_region:
            by_region[region].append(_row_to_indicator(row))

    def sort_key(ind: IndicatorOut, region: str) -> int:
        order = _REGION_ORDER.get(region, [])
        try:
            return order.index(ind.indicator)
        except ValueError:
            return 99

    now = datetime.now(timezone.utc).isoformat()
    return MacroSnapshotOut(
        spain=RegionSnapshotOut(
            region="ES",
            indicators=sorted(by_region["ES"], key=lambda x: sort_key(x, "ES")),
        ),
        eurozone=RegionSnapshotOut(
            region="EA",
            indicators=sorted(by_region["EA"], key=lambda x: sort_key(x, "EA")),
        ),
        us=RegionSnapshotOut(
            region="US",
            indicators=sorted(by_region["US"], key=lambda x: sort_key(x, "US")),
        ),
        last_refreshed=now,
    )


def get_snapshot() -> MacroSnapshotOut:
    rows = repo.get_all_latest()
    if not rows:
        rows = _do_refresh()
    return _build_snapshot(rows)


def refresh_snapshot() -> Optional[MacroSnapshotOut]:
    if not _refresh_lock.acquire(blocking=False):
        return None
    try:
        rows = _do_refresh()
        return _build_snapshot(rows)
    finally:
        _refresh_lock.release()


def _do_refresh() -> list[dict]:
    fred = FredProvider()
    stooq = StooqMacroProvider()

    fetched: list[dict] = []
    fetched.extend(fred.fetch_all())
    fetched.extend(stooq.fetch_all())

    for item in fetched:
        try:
            repo.upsert_indicator(
                series_id=item["series_id"],
                region=item["region"],
                indicator=item["indicator"],
                name=item["name"],
                value=item.get("value"),
                prev_value=item.get("prev_value"),
                period=item.get("period", ""),
                unit=item.get("unit", "%"),
                source=item["source"],
                observation_date=item["observation_date"],
            )
        except Exception as exc:
            logger.error("Failed to cache indicator %s: %s", item.get("series_id"), exc)

    return repo.get_all_latest()


def get_indicators(region: Optional[str] = None, indicator: Optional[str] = None) -> list[IndicatorOut]:
    rows = repo.get_all_latest()
    if region:
        rows = [r for r in rows if r["region"] == region]
    if indicator:
        rows = [r for r in rows if r["indicator"] == indicator]
    return [_row_to_indicator(r) for r in rows]


# ── Personal Impact ───────────────────────────────────────────────────────────

def get_personal_impact(db: Session) -> PersonalImpactOut:
    return PersonalImpactOut(
        inflation_vs_savings=_calc_inflation_vs_savings(db),
        rates_vs_liquidity=_calc_rates_vs_liquidity(db),
        market_vs_portfolio=_calc_market_vs_portfolio(db),
        purchasing_power=_calc_purchasing_power(db),
    )


def _calc_inflation_vs_savings(db: Session) -> ImpactItem:
    from app.models.transaction import Transaction
    from decimal import Decimal

    inflation_row = repo.get_latest("ESPCPIALLMINMEI")
    macro_value = inflation_row["value"] if inflation_row else None

    # Last complete month with transactions
    now = datetime.now(timezone.utc)
    if now.month == 1:
        month_prefix = f"{now.year - 1}-12"
    else:
        month_prefix = f"{now.year}-{now.month - 1:02d}"

    txs = db.query(Transaction).filter(Transaction.date.like(f"{month_prefix}%")).all()
    income = sum((t.amount for t in txs if t.type == "income"), Decimal("0"))
    expense = abs(sum((t.amount for t in txs if t.type == "expense"), Decimal("0")))

    if income > 0:
        personal_value = round(float((income - expense) / income * 100), 2)
    else:
        personal_value = None

    if macro_value is None or personal_value is None:
        return ImpactItem(
            title="Inflación vs tu tasa de ahorro",
            macro_value=macro_value,
            personal_value=personal_value,
            delta=None,
            interpretation="no_data",
            description="No hay suficientes datos para calcular esta comparativa.",
        )

    delta = round(personal_value - macro_value, 2)
    interpretation = "favorable" if delta > 0 else ("neutral" if delta == 0 else "adverse")
    if interpretation == "favorable":
        desc = f"Tu tasa de ahorro ({personal_value:.1f}%) supera la inflación ({macro_value:.1f}%). Estás preservando poder adquisitivo."
    else:
        desc = f"Tu tasa de ahorro ({personal_value:.1f}%) está por debajo de la inflación ({macro_value:.1f}%). Tu poder adquisitivo se reduce."

    return ImpactItem(
        title="Inflación vs tu tasa de ahorro",
        macro_value=macro_value,
        personal_value=personal_value,
        delta=delta,
        interpretation=interpretation,
        description=desc,
    )


def _calc_rates_vs_liquidity(db: Session) -> ImpactItem:
    from app.models.account import Account

    bce_row = repo.get_latest("ECBDFR")
    macro_value = bce_row["value"] if bce_row else None

    # Average rate of savings/remunerada accounts
    accounts = db.query(Account).filter(
        Account.type == "savings",
        Account.is_active == True,  # noqa: E712
    ).all()

    if accounts:
        rates = [float(getattr(a, "interest_rate", 0) or 0) for a in accounts]
        personal_value = round(sum(rates) / len(rates), 2) if rates else None
    else:
        personal_value = None

    if macro_value is None or personal_value is None:
        return ImpactItem(
            title="Tipo BCE vs rentabilidad de tu liquidez",
            macro_value=macro_value,
            personal_value=personal_value,
            delta=None,
            interpretation="no_data",
            description="No tienes cuentas de ahorro registradas o no hay datos del tipo BCE.",
        )

    delta = round(personal_value - macro_value, 2)
    interpretation = "favorable" if delta >= 0 else "adverse"
    if interpretation == "favorable":
        desc = f"Tus cuentas de ahorro rinden al {personal_value:.2f}%, en línea o por encima del tipo BCE ({macro_value:.2f}%)."
    else:
        desc = f"Tus cuentas de ahorro rinden al {personal_value:.2f}%, por debajo del tipo BCE ({macro_value:.2f}%)."

    return ImpactItem(
        title="Tipo BCE vs rentabilidad de tu liquidez",
        macro_value=macro_value,
        personal_value=personal_value,
        delta=delta,
        interpretation=interpretation,
        description=desc,
    )


def _calc_market_vs_portfolio(db: Session) -> ImpactItem:
    from app.models.investment import Holding, InvestmentOperation

    eurostoxx_row = repo.get_latest("EUROSTOXX50")
    macro_value = None
    if eurostoxx_row and eurostoxx_row.get("value") and eurostoxx_row.get("prev_value"):
        v = eurostoxx_row["value"]
        pv = eurostoxx_row["prev_value"]
        if pv and pv != 0:
            macro_value = round((v - pv) / abs(pv) * 100, 2)

    # Portfolio return: (current_value - cost_basis) / cost_basis * 100
    holdings = db.query(Holding).filter(Holding.quantity > 0).all()
    if holdings:
        total_current = sum(float(h.quantity) * float(h.current_price or 0) for h in holdings)
        total_cost = sum(float(h.quantity) * float(h.average_price or 0) for h in holdings)
        if total_cost > 0:
            personal_value = round((total_current - total_cost) / total_cost * 100, 2)
        else:
            personal_value = None
    else:
        personal_value = None

    if macro_value is None or personal_value is None:
        return ImpactItem(
            title="Mercado vs rentabilidad de tu cartera",
            macro_value=macro_value,
            personal_value=personal_value,
            delta=None,
            interpretation="no_data",
            description="No hay datos suficientes para comparar tu cartera con el mercado.",
        )

    delta = round(personal_value - macro_value, 2)
    interpretation = "favorable" if delta >= 0 else "adverse"
    if interpretation == "favorable":
        desc = f"Tu cartera rinde un {personal_value:.1f}% frente al {macro_value:.1f}% del Euro Stoxx 50."
    else:
        desc = f"Tu cartera ({personal_value:.1f}%) queda por debajo del Euro Stoxx 50 ({macro_value:.1f}%)."

    return ImpactItem(
        title="Mercado vs rentabilidad de tu cartera",
        macro_value=macro_value,
        personal_value=personal_value,
        delta=delta,
        interpretation=interpretation,
        description=desc,
    )


def _calc_purchasing_power(db: Session) -> ImpactItem:
    from app.models.transaction import Transaction
    from decimal import Decimal
    from datetime import datetime, timezone, timedelta

    inflation_row = repo.get_latest("ESPCPIALLMINMEI")
    macro_value = inflation_row["value"] if inflation_row else None

    # Compare income: last 3 months vs same period 1 year ago
    now = datetime.now(timezone.utc)
    recent_months = [(now - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(1, 4)]
    prior_months = [(now - timedelta(days=30 * (i + 12))).strftime("%Y-%m") for i in range(1, 4)]

    def sum_income(months: list[str]) -> Decimal:
        total = Decimal("0")
        for m in months:
            txs = db.query(Transaction).filter(
                Transaction.date.like(f"{m}%"),
                Transaction.type == "income",
            ).all()
            total += sum((t.amount for t in txs), Decimal("0"))
        return total

    recent_income = sum_income(recent_months)
    prior_income = sum_income(prior_months)

    if prior_income > 0 and recent_income > 0:
        personal_value = round(float((recent_income - prior_income) / prior_income * 100), 2)
    else:
        personal_value = None

    if macro_value is None or personal_value is None:
        return ImpactItem(
            title="Poder adquisitivo",
            macro_value=macro_value,
            personal_value=personal_value,
            delta=None,
            interpretation="no_data",
            description="No hay suficientes datos de ingresos para calcular la evolución del poder adquisitivo.",
        )

    delta = round(personal_value - macro_value, 2)
    interpretation = "favorable" if delta > 0 else ("neutral" if delta == 0 else "adverse")
    if interpretation == "favorable":
        desc = f"Tus ingresos crecieron un {personal_value:.1f}% frente a una inflación del {macro_value:.1f}%. Estás ganando poder adquisitivo."
    else:
        desc = f"Tus ingresos crecieron un {personal_value:.1f}% pero la inflación es del {macro_value:.1f}%. Estás perdiendo poder adquisitivo."

    return ImpactItem(
        title="Poder adquisitivo",
        macro_value=macro_value,
        personal_value=personal_value,
        delta=delta,
        interpretation=interpretation,
        description=desc,
    )
