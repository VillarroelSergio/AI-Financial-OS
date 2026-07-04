from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction
from app.modules.insights.constants import (
    BASELINE_MONTHS,
    EXPENSE_DELTA_PERCENTAGE_THRESHOLD,
    MIN_BASELINE_MONTHS,
    SAVINGS_DELTA_ABSOLUTE_THRESHOLD_EUR,
    SPENDING_ANOMALY_MIN_ABSOLUTE_EUR,
    SPENDING_ANOMALY_MIN_CURRENT_EUR,
    SPENDING_ANOMALY_MULTIPLIER,
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


def _month_expenses_by_category(db: Session, period: str) -> dict[str | None, Decimal]:
    txs = db.query(Transaction).filter(
        Transaction.date.like(f"{period}%"),
        Transaction.type == "expense",
    ).all()
    by_cat: dict[str | None, Decimal] = {}
    for t in txs:
        by_cat[t.category_id] = by_cat.get(t.category_id, Decimal("0")) + abs(t.amount)
    return by_cat


def _prev_months(period: str, n: int) -> list[str]:
    year, month = int(period[:4]), int(period[5:7])
    months = []
    for _ in range(n):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        months.append(f"{year}-{month:02d}")
    return months


def _month_totals(db: Session, period: str) -> tuple[Decimal, Decimal]:
    txs = db.query(Transaction).filter(Transaction.date.like(f"{period}%")).all()
    income = sum((t.amount for t in txs if t.type == "income"), Decimal("0"))
    expense = abs(sum((t.amount for t in txs if t.type == "expense"), Decimal("0")))
    return income, expense


def spending_anomaly_insights(db: Session, period: str) -> list[InsightOut]:
    categories = {c.id: c.name for c in db.query(Category).all()}
    current_by_cat = _month_expenses_by_category(db, period)

    if not current_by_cat:
        return []

    prev_months = _prev_months(period, BASELINE_MONTHS)
    baseline_by_cat: dict[str | None, list[Decimal]] = {}
    valid_baseline_months = 0
    for m in prev_months:
        month_cat = _month_expenses_by_category(db, m)
        if month_cat:
            valid_baseline_months += 1
            for cat_id, amt in month_cat.items():
                baseline_by_cat.setdefault(cat_id, []).append(amt)

    insights: list[InsightOut] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for cat_id, current_amt in current_by_cat.items():
        if current_amt < SPENDING_ANOMALY_MIN_CURRENT_EUR:
            continue

        if valid_baseline_months < MIN_BASELINE_MONTHS or cat_id not in baseline_by_cat:
            data_status = DataStatus.insufficient
            confidence = compute_confidence("insufficient")
            priority = compute_priority("info", "insufficient", 40.0)
            cat_name = categories.get(cat_id or "", "Sin categoría")
            insights.append(InsightOut(
                id=f"insight_{period}_spending_anomaly_{cat_id or 'unknown'}_insufficient",
                type=InsightType.spending_anomaly,
                severity=InsightSeverity.info,
                title=f"Gasto en {cat_name} sin historial suficiente",
                summary=f"No hay suficientes meses previos para comparar el gasto en {cat_name}.",
                period=period,
                impact_area="spending",
                confidence=confidence,
                priority=priority,
                data_status=data_status,
                primary_metric=InsightMetricOut(label="Gasto actual", value=float(current_amt), unit="EUR"),
                sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
                actions=[InsightActionOut(label=f"Ver gastos de {cat_name}", target="/spending", params={"category": cat_name, "period": period})],
                created_at=now_iso,
            ))
            continue

        baseline_vals = baseline_by_cat[cat_id]
        baseline_avg = sum(baseline_vals) / Decimal(len(baseline_vals))
        diff = current_amt - baseline_avg

        if diff < SPENDING_ANOMALY_MIN_ABSOLUTE_EUR:
            continue
        if current_amt <= baseline_avg * SPENDING_ANOMALY_MULTIPLIER:
            continue

        pct_increase = float(diff / baseline_avg * 100) if baseline_avg > 0 else 0.0
        cat_name = categories.get(cat_id or "", "Sin categoría")

        if pct_increase >= 50:
            severity = InsightSeverity.warning
            impact_score = 70.0
        else:
            severity = InsightSeverity.info
            impact_score = 50.0

        confidence = compute_confidence("complete")
        priority = compute_priority(severity.value, "complete", impact_score)

        insights.append(InsightOut(
            id=f"insight_{period}_spending_anomaly_{cat_id or 'unknown'}",
            type=InsightType.spending_anomaly,
            severity=severity,
            title=f"Gasto en {cat_name} superior a tu media",
            summary=f"Este mes has gastado un {pct_increase:.0f}% más en {cat_name} que tu media reciente.",
            detail=f"La comparación usa los últimos {len(baseline_vals)} meses con datos. El incremento absoluto es de {float(diff):.0f} €.",
            period=period,
            impact_area="spending",
            confidence=confidence,
            priority=priority,
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Incremento", value=round(pct_increase, 1), unit="%"),
            secondary_metrics=[
                InsightMetricOut(label="Gasto actual", value=float(current_amt), unit="EUR"),
                InsightMetricOut(label="Media reciente", value=float(baseline_avg), unit="EUR"),
            ],
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label=f"Ver gastos de {cat_name}", target="/spending", params={"category": cat_name, "period": period})],
            created_at=now_iso,
        ))

    return insights


def monthly_comparison_insights(db: Session, period: str) -> list[InsightOut]:
    prev_months = _prev_months(period, 1)
    prev_period = prev_months[0] if prev_months else None
    if not prev_period:
        return []

    income_curr, expense_curr = _month_totals(db, period)
    income_prev, expense_prev = _month_totals(db, prev_period)

    if income_curr == 0 and expense_curr == 0:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    insights: list[InsightOut] = []

    expense_delta = expense_curr - expense_prev
    expense_delta_pct = float(expense_delta / expense_prev * 100) if expense_prev > 0 else 0.0

    savings_curr = income_curr - expense_curr
    savings_prev = income_prev - expense_prev
    savings_delta = savings_curr - savings_prev

    if abs(expense_delta_pct) >= float(EXPENSE_DELTA_PERCENTAGE_THRESHOLD):
        severity = InsightSeverity.warning if expense_delta > 0 else InsightSeverity.positive
        insights.append(InsightOut(
            id=f"insight_{period}_monthly_comparison_expense",
            type=InsightType.monthly_comparison,
            severity=severity,
            title="Gasto mensual distinto al mes anterior",
            summary=f"Has gastado {abs(float(expense_delta)):.0f} € {'más' if expense_delta > 0 else 'menos'} que el mes anterior ({expense_delta_pct:+.0f}%).",
            period=period,
            impact_area="spending",
            confidence=compute_confidence("complete"),
            priority=compute_priority(severity.value, "complete", 65.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Variación gasto", value=round(expense_delta_pct, 1), unit="%"),
            secondary_metrics=[
                InsightMetricOut(label="Gasto actual", value=float(expense_curr), unit="EUR"),
                InsightMetricOut(label="Gasto anterior", value=float(expense_prev), unit="EUR"),
            ],
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver gastos", target="/spending", params={"period": period})],
            created_at=now_iso,
        ))

    if abs(savings_delta) >= float(SAVINGS_DELTA_ABSOLUTE_THRESHOLD_EUR):
        severity = InsightSeverity.warning if savings_delta < 0 else InsightSeverity.positive
        insights.append(InsightOut(
            id=f"insight_{period}_monthly_comparison_savings",
            type=InsightType.monthly_comparison,
            severity=severity,
            title="Cambio en ahorro mensual",
            summary=f"Tu ahorro {'ha bajado' if savings_delta < 0 else 'ha subido'} {abs(float(savings_delta)):.0f} € respecto al mes anterior.",
            period=period,
            impact_area="spending",
            confidence=compute_confidence("complete"),
            priority=compute_priority(severity.value, "complete", 60.0),
            data_status=DataStatus.complete,
            primary_metric=InsightMetricOut(label="Variación ahorro", value=float(savings_delta), unit="EUR"),
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Ver gastos", target="/spending", params={"period": period})],
            created_at=now_iso,
        ))

    return insights


def savings_rate_insight(db: Session, period: str) -> list[InsightOut]:
    income, expense = _month_totals(db, period)
    now_iso = datetime.now(timezone.utc).isoformat()

    if income == 0 and expense == 0:
        return []

    if income == 0:
        return [InsightOut(
            id=f"insight_{period}_savings_rate_no_income",
            type=InsightType.savings_rate,
            severity=InsightSeverity.warning,
            title="Sin ingresos registrados este mes",
            summary="No hay ingresos registrados para calcular la tasa de ahorro.",
            period=period,
            impact_area="spending",
            confidence=compute_confidence("insufficient"),
            priority=compute_priority("warning", "insufficient", 55.0),
            data_status=DataStatus.insufficient,
            sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
            actions=[InsightActionOut(label="Importar datos", target="/imports", params={})],
            created_at=now_iso,
        )]

    savings = income - expense
    rate = float(savings / income * 100)

    if rate >= 30:
        severity, impact = InsightSeverity.positive, 60.0
        summary = f"Has ahorrado el {rate:.1f}% de tus ingresos. Excelente tasa de ahorro."
    elif rate >= 15:
        severity, impact = InsightSeverity.info, 50.0
        summary = f"Tu tasa de ahorro este mes es del {rate:.1f}%. Es positiva."
    elif rate >= 0:
        severity, impact = InsightSeverity.warning, 65.0
        summary = f"Tu tasa de ahorro es del {rate:.1f}%. Puedes revisar si hay margen para mejorarla."
    else:
        severity, impact = InsightSeverity.warning, 75.0
        summary = f"Tus gastos superan tus ingresos ({rate:.1f}%). Puedes revisar si faltan ingresos por importar."

    return [InsightOut(
        id=f"insight_{period}_savings_rate",
        type=InsightType.savings_rate,
        severity=severity,
        title="Tasa de ahorro mensual",
        summary=summary,
        period=period,
        impact_area="spending",
        confidence=compute_confidence("complete"),
        priority=compute_priority(severity.value, "complete", impact),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Tasa de ahorro", value=round(rate, 1), unit="%"),
        secondary_metrics=[
            InsightMetricOut(label="Ingresos", value=float(income), unit="EUR"),
            InsightMetricOut(label="Gastos", value=float(expense), unit="EUR"),
            InsightMetricOut(label="Ahorro", value=float(savings), unit="EUR"),
        ],
        sources=[InsightSourceOut(type="transactions", label="Movimientos", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver gastos", target="/spending", params={"period": period})],
        created_at=now_iso,
    )]
