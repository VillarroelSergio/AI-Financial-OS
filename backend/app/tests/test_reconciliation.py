from __future__ import annotations
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from app.modules.investments.reconciliation_service import (
    compute_reconciliation,
    QualityState,
)
from app.modules.investments.schemas import HoldingOut, InvestmentAssetOut


def _make_asset(currency: str = "EUR", sector: str = "Tecnologia",
                region: str = "US", asset_type: str = "equity") -> InvestmentAssetOut:
    return InvestmentAssetOut(
        id="asset-1", name="Apple", ticker="AAPL", isin=None,
        asset_type=asset_type, currency=currency, region=region,
        sector=sector, price_source="market",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_holding(
    market_value: str = "5000",
    current_price: str = "175",
    currency: str = "USD",
    price_updated_at: datetime | None = None,
    is_mock: bool = False,
    average_price: str = "140",
    quantity: str = "30",
) -> HoldingOut:
    if price_updated_at is None:
        price_updated_at = datetime.now(timezone.utc) - timedelta(hours=1)
    return HoldingOut(
        id="h-1", account_id="acc-1", asset_id="asset-1",
        quantity=Decimal(quantity), average_price=Decimal(average_price),
        current_price=Decimal(current_price),
        current_price_currency=currency,
        current_price_updated_at=price_updated_at,
        market_value=Decimal(market_value),
        interest_rate=None, inception_date=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        asset=_make_asset(currency=currency),
        cost_basis=Decimal(average_price) * Decimal(quantity),
        return_absolute=Decimal("800"), return_percent=19.0,
        accrued_interest=None,
        display_name="Apple", symbol="AAPL",
        asset_type="equity", broker="acc-1",
        invested_amount=Decimal(average_price) * Decimal(quantity),
        unrealized_pnl=Decimal("800"), unrealized_pnl_pct=19.0,
        currency=currency, is_mock=is_mock, quality_score=1.0, warnings=[],
    )


def test_confirmed_when_fresh_price_eur():
    holding = _make_holding(currency="EUR", price_updated_at=datetime.now(timezone.utc) - timedelta(hours=1))
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.CONFIRMED


def test_fx_pending_when_price_not_eur():
    holding = _make_holding(currency="USD")
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.FX_PENDING
    assert report.holdings[0].requires_fx is True


def test_no_price_when_market_value_none():
    h = _make_holding()
    h = h.model_copy(update={"market_value": None, "current_price": None, "current_price_updated_at": None})
    report = compute_reconciliation([h])
    assert report.holdings[0].quality_state == QualityState.NO_PRICE


def test_manual_when_mock():
    holding = _make_holding(is_mock=True, currency="EUR")
    report = compute_reconciliation([holding])
    assert report.holdings[0].quality_state == QualityState.MANUAL


def test_weights_sum_to_100():
    h1 = _make_holding(market_value="6000", currency="USD")
    h2 = _make_holding(market_value="4000", currency="EUR")
    h2 = h2.model_copy(update={"id": "h-2"})
    report = compute_reconciliation([h1, h2])
    total = sum(w.weight_pct for w in report.weights_by["currency"])
    assert abs(total - 100.0) < 0.2


def test_concentration_alert_when_over_threshold():
    h = _make_holding(market_value="9000", currency="EUR")
    report = compute_reconciliation([h])
    assert any(a.type == "asset" for a in report.concentration_alerts)


def test_empty_holdings_returns_valid_report():
    report = compute_reconciliation([])
    assert report.portfolio_value_eur == 0.0
    assert report.completeness.confirmed_pct == 0.0
    assert report.holdings == []
