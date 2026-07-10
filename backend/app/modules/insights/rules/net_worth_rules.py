from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.investment import Holding, InvestmentAsset
from app.modules.insights.constants import HIGH_CONCENTRATION_THRESHOLD
from app.modules.insights.formatting import fmt_pct, round_dec
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


def net_worth_change_insight(db: Session, period: str) -> list[InsightOut]:
    """INS-4: variación REAL de patrimonio entre los dos últimos snapshots mensuales.

    El insight estático desaparece: sin al menos dos snapshots no hay señal que dar
    (el recordatorio de cierre de mes vive en Resumen, no aquí)."""
    from app.models.net_worth_snapshot import NetWorthSnapshot

    now_iso = datetime.now(timezone.utc).isoformat()
    snaps = (
        db.query(NetWorthSnapshot)
        .order_by(NetWorthSnapshot.month.desc())
        .limit(2)
        .all()
    )
    if len(snaps) < 2:
        return []

    current, previous = snaps[0], snaps[1]
    change = current.net_worth - previous.net_worth
    pct = round_dec(change / abs(previous.net_worth) * 100, 1) if previous.net_worth else Decimal("0")
    severity = InsightSeverity.positive if change >= 0 else InsightSeverity.warning
    signo = "+" if change >= 0 else ""

    return [InsightOut(
        id=f"insight_{period}_net_worth",
        dedupe_key=f"net_worth_change_{current.month}",
        type=InsightType.net_worth_change,
        severity=severity,
        title="Variación de patrimonio",
        summary=(
            f"Tu patrimonio neto {'creció' if change >= 0 else 'bajó'} "
            f"{signo}{change:.0f} € ({signo}{pct}%) respecto a {previous.month}."
        ),
        detail=f"Patrimonio neto en {current.month}: {current.net_worth:.0f} €.",
        period=period,
        impact_area="patrimonio",
        confidence=compute_confidence("complete"),
        priority=compute_priority(severity.value, "complete", 55.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Variación", value=float(change), unit="EUR"),
        secondary_metrics=[
            InsightMetricOut(label="Patrimonio neto", value=float(current.net_worth), unit="EUR"),
            InsightMetricOut(label="Variación", value=float(pct), unit="%", precision=1),
        ],
        sources=[InsightSourceOut(type="net_worth", label="Snapshots de patrimonio", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver balance", target="/", params={})],
        created_at=now_iso,
    )]


def _holding_value(h: Holding) -> Decimal:
    return h.market_value or (h.quantity * (h.current_price or h.average_price)) or Decimal("0")


def wealth_concentration_insight(db: Session, period: str) -> list[InsightOut]:
    """Concentración sobre patrimonio TOTAL (D1/INS-B4). Copy honesto: 'de tu patrimonio'.

    Universo: cuentas activas + posiciones de inversión, no solo la cartera de mercado."""
    now_iso = datetime.now(timezone.utc).isoformat()
    items: list[tuple[str, Decimal]] = []
    for a in db.query(Account).filter(Account.is_active == True).all():  # noqa: E712
        if a.current_balance and a.current_balance > 0:
            items.append((a.name, Decimal(str(a.current_balance))))
    assets = {a.id: a for a in db.query(InvestmentAsset).all()}
    for h in db.query(Holding).all():
        mv = _holding_value(h)
        if mv > 0:
            asset = assets.get(h.asset_id)
            items.append((asset.name if asset else "Activo desconocido", mv))

    total = sum((v for _, v in items), Decimal("0"))
    if total <= 0 or not items:
        return []

    name, val = max(items, key=lambda t: t[1])
    pct = round_dec(val / total * 100, 1)
    if pct <= HIGH_CONCENTRATION_THRESHOLD:
        return []

    return [InsightOut(
        id=f"insight_{period}_wealth_concentration",
        dedupe_key=f"wealth_concentration_{period}",
        type=InsightType.wealth_concentration,
        severity=InsightSeverity.info,
        title="Concentración de patrimonio",
        summary=f"El {fmt_pct(pct)} de tu patrimonio está en {name}. Diversificar reduce el riesgo de una única fuente.",
        period=period,
        impact_area="patrimonio",
        confidence=compute_confidence("complete"),
        priority=compute_priority("info", "complete", 45.0),
        data_status=DataStatus.complete,
        primary_metric=InsightMetricOut(label="Concentración", value=float(pct), unit="%", precision=1),
        sources=[InsightSourceOut(type="accounts", label="Cuentas e inversiones", period=period, updated_at=now_iso)],
        actions=[InsightActionOut(label="Ver cuentas", target="/accounts", params={})],
        created_at=now_iso,
    )]
