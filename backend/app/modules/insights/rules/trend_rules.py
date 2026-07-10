"""INS-6 (Lote 2): tendencias y patrimonio.

Reglas deterministas sobre series de meses completos previos (nunca el mes en curso, que
está parcial). Reutilizan los helpers de agregación mensual de spending_rules y la liquidez
de planning_rules; no duplican esos cálculos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.goal import Goal
from app.modules.insights.constants import (
    CATEGORY_TREND_GROWTH_PCT,
    CATEGORY_TREND_MIN_EUR,
    CATEGORY_TREND_MONTHS,
    EMERGENCY_FUND_EXPENSE_LOOKBACK,
    EMERGENCY_FUND_MONTHS_THRESHOLD,
    SAVINGS_RATE_TREND_DELTA_PP,
    SAVINGS_RATE_TREND_MIN_MONTHS,
    SAVINGS_RATE_TREND_MONTHS,
)
from app.modules.insights.formatting import savings_rate_dec
from app.modules.insights.rules.planning_rules import _liquidity_eur
from app.modules.insights.rules.spending_rules import (
    _month_expenses_by_category,
    _month_totals,
    _prev_months,
)
from app.modules.insights.schemas import (
    DataStatus,
    InsightActionOut,
    InsightMetricOut,
    InsightOut,
    InsightSeverity,
    InsightSourceOut,
    InsightType,
)
from app.modules.insights.scoring import compute_confidence, compute_priority


def savings_rate_trend_insight(db: Session, period: str) -> list[InsightOut]:
    """Mejora o deterioro sostenido de la tasa de ahorro en los últimos meses completos."""
    months = list(reversed(_prev_months(period, SAVINGS_RATE_TREND_MONTHS)))  # antiguo→reciente
    series: list[Decimal] = []
    for m in months:
        income, expense = _month_totals(db, m)
        if income <= 0:
            continue
        series.append(savings_rate_dec(income, expense))
    if len(series) < SAVINGS_RATE_TREND_MIN_MONTHS:
        return []

    half = len(series) // 2
    first = sum(series[:half], Decimal("0")) / Decimal(half)
    second = sum(series[half:], Decimal("0")) / Decimal(len(series) - half)
    delta = second - first  # puntos porcentuales
    if abs(delta) < SAVINGS_RATE_TREND_DELTA_PP:
        return []

    improving = delta > 0
    severity = InsightSeverity.positive if improving else InsightSeverity.warning
    now_iso = datetime.now(timezone.utc).isoformat()
    return [InsightOut(
        id=f"insight_{period}_savings_rate_trend",
        type=InsightType.savings_rate_trend,
        severity=severity,
        title="Tu tasa de ahorro mejora de forma sostenida" if improving
              else "Tu tasa de ahorro se deteriora de forma sostenida",
        summary=(
            f"En los últimos {len(series)} meses tu tasa de ahorro media pasó del "
            f"{float(first):.0f}% al {float(second):.0f}% "
            f"({'+' if improving else ''}{float(delta):.0f} pp)."
        ),
        period=period,
        impact_area="spending",
        dedupe_key=f"savings_rate_trend:{period}",
        confidence=compute_confidence("complete"),
        priority=compute_priority(severity.value, "complete", 60.0 if improving else 68.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Variación", value=float(delta), unit="pp", precision=1),
        secondary_metrics=[
            InsightMetricOut(label="Tasa reciente", value=float(second), unit="%", precision=0),
            InsightMetricOut(label="Tasa previa", value=float(first), unit="%", precision=0),
        ],
        sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver gastos", target="/spending", params={})],
        created_at=now_iso,
    )]


def category_trend_insights(db: Session, period: str) -> list[InsightOut]:
    """Categoría con gasto creciente N meses consecutivos (distinto de la anomalía puntual)."""
    months = list(reversed(_prev_months(period, CATEGORY_TREND_MONTHS)))  # antiguo→reciente
    if len(months) < CATEGORY_TREND_MONTHS:
        return []
    per_month = [_month_expenses_by_category(db, m) for m in months]
    # Solo categorías presentes en todos los meses de la ventana: sin hueco no hay tendencia real.
    common = set(per_month[0])
    for d in per_month[1:]:
        common &= set(d)
    if not common:
        return []

    names = {c.id: c.name for c in db.query(Category).all()}
    now_iso = datetime.now(timezone.utc).isoformat()
    out: list[InsightOut] = []
    for cat_id in common:
        seq = [per_month[i][cat_id] for i in range(len(months))]
        if not all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)):
            continue
        if seq[-1] < CATEGORY_TREND_MIN_EUR or seq[0] <= 0:
            continue
        growth_pct = (seq[-1] - seq[0]) / seq[0] * Decimal("100")
        if growth_pct < CATEGORY_TREND_GROWTH_PCT:
            continue
        cat_name = names.get(cat_id or "", "Sin categoría")
        out.append(InsightOut(
            id=f"insight_{period}_category_trend_{cat_id or 'unknown'}",
            type=InsightType.category_trend,
            severity=InsightSeverity.warning,
            title=f"Gasto en {cat_name} al alza {len(months)} meses seguidos",
            summary=(
                f"Tu gasto en {cat_name} ha crecido cada mes durante {len(months)} meses: "
                f"de {float(seq[0]):.0f} € a {float(seq[-1]):.0f} € (+{float(growth_pct):.0f}%)."
            ),
            period=period,
            impact_area="spending",
            dedupe_key=f"category_trend:{cat_id or 'unknown'}",
            confidence=compute_confidence("complete"),
            priority=compute_priority("warning", "complete", 66.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Crecimiento", value=float(growth_pct), unit="%", precision=0),
            secondary_metrics=[
                InsightMetricOut(label="Último mes", value=float(seq[-1]), unit="EUR"),
                InsightMetricOut(label="Primer mes", value=float(seq[0]), unit="EUR"),
            ],
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label=f"Ver gastos de {cat_name}", target="/spending",
                                      params={"category": cat_name})],
            created_at=now_iso,
        ))
    return out


def emergency_fund_coverage_insight(db: Session, period: str) -> list[InsightOut]:
    """Meses de colchón = liquidez / gasto medio mensual (3m). Señal si por debajo del umbral.

    Cruza con el objetivo `emergency_fund` si el usuario lo tiene definido."""
    months = _prev_months(period, EMERGENCY_FUND_EXPENSE_LOOKBACK)
    expenses = [e for e in (_month_totals(db, m)[1] for m in months) if e > 0]
    if not expenses:
        return []
    avg_expense = sum(expenses, Decimal("0")) / Decimal(len(expenses))
    if avg_expense <= 0:
        return []

    liquidity = _liquidity_eur(db)
    coverage = liquidity / avg_expense  # meses
    goal = (
        db.query(Goal)
        .filter(Goal.type == "emergency_fund", Goal.status == "active")
        .first()
    )
    if coverage >= EMERGENCY_FUND_MONTHS_THRESHOLD:
        return []  # colchón sano: sin señal (el progreso del objetivo ya lo cubre goal_progress)

    severity = InsightSeverity.critical if coverage < 1 else InsightSeverity.warning
    now_iso = datetime.now(timezone.utc).isoformat()
    summary = (
        f"Tu liquidez cubre {float(coverage):.1f} meses de gasto "
        f"({float(avg_expense):.0f} €/mes de media), por debajo de los "
        f"{float(EMERGENCY_FUND_MONTHS_THRESHOLD):.0f} meses recomendados."
    )
    secondary = [
        InsightMetricOut(label="Liquidez", value=float(liquidity), unit="EUR"),
        InsightMetricOut(label="Gasto medio", value=float(avg_expense), unit="EUR"),
    ]
    actions = [InsightActionOut(label="Ver cuentas", target="/accounts", params={})]
    if goal is not None and goal.target_amount and goal.target_amount > 0:
        goal_pct = liquidity / Decimal(str(goal.target_amount)) * Decimal("100")
        summary += f" Llevas el {float(goal_pct):.0f}% de tu objetivo '{goal.name}'."
        secondary.append(InsightMetricOut(label="Objetivo", value=float(goal.target_amount), unit="EUR"))
        actions = [InsightActionOut(label="Ver objetivos", target="/goals", params={})]

    return [InsightOut(
        id=f"insight_{period}_emergency_fund_coverage",
        type=InsightType.emergency_fund_coverage,
        severity=severity,
        title="Colchón de emergencia por debajo de lo recomendado",
        summary=summary,
        period=period,
        impact_area="patrimonio",
        dedupe_key=f"emergency_fund_coverage:{period}",
        confidence=compute_confidence("complete"),
        priority=compute_priority(severity.value, "complete", 80.0 if coverage < 1 else 70.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Meses de colchón", value=float(coverage), unit="meses", precision=1),
        secondary_metrics=secondary,
        sources=[InsightSourceOut(type="accounts", label="Cuentas y movimientos", period=period, updated_at=now_iso)],
        actions=actions,
        created_at=now_iso,
    )]


def _latest_ipc() -> float | None:
    """IPC interanual de España desde el almacén de mercado (mi_*, solo lectura)."""
    try:
        from app.modules.market_intelligence.storage.repository import get_latest_macro_all
        data = get_latest_macro_all()
    except Exception:
        return None
    by_id = {item.get("catalog_item_id"): item.get("value") for item in data}
    for cid in ("esp_cpi_yoy", "esp_cpi"):
        v = by_id.get(cid)
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                continue
    return None


def real_return_insight(db: Session, period: str) -> list[InsightOut]:
    """Rentabilidad real de las cuentas remuneradas = tipo nominal vigente − IPC interanual."""
    from app.models.investment import SavingsAccountConfig
    from app.modules.investments.savings_service import current_annual_rate

    configs = db.query(SavingsAccountConfig).all()
    if not configs:
        return []
    # Mismo tipo de referencia que 'Letras vs tu ahorro' (MI): el mejor vigente.
    nominal = max((current_annual_rate(db, c) for c in configs), default=None)
    if nominal is None:
        return []
    ipc = _latest_ipc()
    if ipc is None:
        return []

    real = float(nominal) - ipc
    negative = real < 0
    severity = InsightSeverity.warning if negative else InsightSeverity.positive
    now_iso = datetime.now(timezone.utc).isoformat()
    return [InsightOut(
        id=f"insight_{period}_real_return",
        type=InsightType.real_return,
        severity=severity,
        title="Tu ahorro pierde poder adquisitivo frente a la inflación" if negative
              else "Tu ahorro gana poder adquisitivo frente a la inflación",
        summary=(
            f"Tus cuentas remuneradas rinden un {float(nominal):.2f}% anual y el IPC está en "
            f"{ipc:.1f}%: rentabilidad real del {real:+.2f}%."
        ),
        period=period,
        impact_area="macro",
        dedupe_key=f"real_return:{period}",
        confidence=compute_confidence("complete"),
        priority=compute_priority(severity.value, "complete", 55.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Rentabilidad real", value=round(real, 2), unit="%", precision=2),
        secondary_metrics=[
            InsightMetricOut(label="Tipo nominal", value=float(nominal), unit="%", precision=2),
            InsightMetricOut(label="IPC", value=round(ipc, 1), unit="%", precision=1),
        ],
        sources=[
            InsightSourceOut(type="savings", label="Cuentas remuneradas", period=period, updated_at=now_iso),
            InsightSourceOut(type="macro", label="IPC", source="market_intelligence", updated_at=now_iso),
        ],
        actions=[InsightActionOut(label="Ver economía", target="/economy", params={})],
        created_at=now_iso,
    )]
