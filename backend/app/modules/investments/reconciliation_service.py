"""Reconciliation service — computes quality states, weights and concentration alerts on-demand."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from app.modules.investments.schemas import HoldingOut

ASSET_CONCENTRATION_THRESHOLD = 20.0
CURRENCY_CONCENTRATION_THRESHOLD = 40.0
PRICE_FRESHNESS_HOURS = 24


class QualityState(str, Enum):
    CONFIRMED = "confirmed"
    ESTIMATED = "estimated"
    MANUAL = "manual"
    NO_PRICE = "no_price"
    FX_PENDING = "fx_pending"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class ReconciliationHolding:
    holding_id: str
    display_name: str
    ticker: str | None
    quality_state: QualityState
    value_eur: float
    weight_pct: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    currency: str
    requires_fx: bool
    broker: str
    sector: str | None
    asset_type: str


@dataclass
class WeightItem:
    key: str
    weight_pct: float


@dataclass
class ConcentrationAlert:
    type: str
    key: str
    weight_pct: float
    threshold_pct: float


@dataclass
class Completeness:
    confirmed_pct: float = 0.0
    estimated_pct: float = 0.0
    manual_pct: float = 0.0
    no_price_pct: float = 0.0


@dataclass
class ReconciliationReport:
    generated_at: datetime
    portfolio_value_eur: float
    completeness: Completeness
    holdings: list[ReconciliationHolding]
    weights_by: dict[str, list[WeightItem]]
    concentration_alerts: list[ConcentrationAlert]


def _compute_quality_state(h: HoldingOut) -> tuple[QualityState, bool]:
    """Returns (quality_state, requires_fx)."""
    if h.is_mock:
        return QualityState.MANUAL, False

    if h.market_value is None or h.current_price is None:
        return QualityState.NO_PRICE, False

    requires_fx = h.currency not in ("EUR", "")
    if requires_fx:
        return QualityState.FX_PENDING, True

    if h.current_price_updated_at is not None:
        now = datetime.now(timezone.utc)
        updated_at = h.current_price_updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age_hours = (now - updated_at).total_seconds() / 3600
        if age_hours > PRICE_FRESHNESS_HOURS:
            return QualityState.ESTIMATED, False

    return QualityState.CONFIRMED, False


def _group_weights(items: list[tuple[str, float]], total: float) -> list[WeightItem]:
    grouped: dict[str, float] = {}
    for key, value in items:
        k = key or "Otro"
        grouped[k] = grouped.get(k, 0.0) + value
    if total == 0:
        return []
    return sorted(
        [WeightItem(key=k, weight_pct=round(v / total * 100, 1)) for k, v in grouped.items()],
        key=lambda x: x.weight_pct,
        reverse=True,
    )


def compute_reconciliation(holdings: list[HoldingOut]) -> ReconciliationReport:
    if not holdings:
        return ReconciliationReport(
            generated_at=datetime.now(timezone.utc),
            portfolio_value_eur=0.0,
            completeness=Completeness(),
            holdings=[],
            weights_by={"currency": [], "sector": [], "broker": [], "asset_type": [], "region": []},
            concentration_alerts=[],
        )

    total_value = sum(
        float(h.market_value or h.invested_amount or Decimal("0"))
        for h in holdings
    )

    reconciled: list[ReconciliationHolding] = []
    state_counts: dict[QualityState, int] = {s: 0 for s in QualityState}

    for h in holdings:
        state, requires_fx = _compute_quality_state(h)
        state_counts[state] += 1
        value = float(h.market_value or h.invested_amount or Decimal("0"))
        weight_pct = round(value / total_value * 100, 1) if total_value > 0 else 0.0
        reconciled.append(ReconciliationHolding(
            holding_id=h.id,
            display_name=h.display_name,
            ticker=h.symbol,
            quality_state=state,
            value_eur=round(value, 2),
            weight_pct=weight_pct,
            unrealized_pnl=float(h.unrealized_pnl),
            unrealized_pnl_pct=h.unrealized_pnl_pct,
            currency=h.currency,
            requires_fx=requires_fx,
            broker=h.broker,
            sector=h.asset.sector,
            asset_type=h.asset_type,
        ))

    n = len(holdings)
    completeness = Completeness(
        confirmed_pct=round(state_counts[QualityState.CONFIRMED] / n * 100, 1),
        estimated_pct=round(state_counts[QualityState.ESTIMATED] / n * 100, 1),
        manual_pct=round((state_counts[QualityState.MANUAL] + state_counts[QualityState.REQUIRES_REVIEW]) / n * 100, 1),
        no_price_pct=round((state_counts[QualityState.NO_PRICE] + state_counts[QualityState.FX_PENDING]) / n * 100, 1),
    )

    values_by: dict[str, list[tuple[str, float]]] = {
        "currency": [], "sector": [], "broker": [], "asset_type": [], "region": [],
    }
    for rh, h in zip(reconciled, holdings):
        v = rh.value_eur
        values_by["currency"].append((rh.currency, v))
        values_by["sector"].append((rh.sector or "Sin sector", v))
        values_by["broker"].append((rh.broker, v))
        values_by["asset_type"].append((rh.asset_type, v))
        values_by["region"].append((h.asset.region or "Sin region", v))

    weights_by = {dim: _group_weights(items, total_value) for dim, items in values_by.items()}

    alerts: list[ConcentrationAlert] = []
    for rh in reconciled:
        if rh.weight_pct > ASSET_CONCENTRATION_THRESHOLD:
            alerts.append(ConcentrationAlert(
                type="asset", key=rh.display_name,
                weight_pct=rh.weight_pct, threshold_pct=ASSET_CONCENTRATION_THRESHOLD,
            ))
    for item in weights_by.get("currency", []):
        if item.weight_pct > CURRENCY_CONCENTRATION_THRESHOLD:
            alerts.append(ConcentrationAlert(
                type="currency", key=item.key,
                weight_pct=item.weight_pct, threshold_pct=CURRENCY_CONCENTRATION_THRESHOLD,
            ))

    return ReconciliationReport(
        generated_at=datetime.now(timezone.utc),
        portfolio_value_eur=round(total_value, 2),
        completeness=completeness,
        holdings=reconciled,
        weights_by=weights_by,
        concentration_alerts=alerts,
    )
