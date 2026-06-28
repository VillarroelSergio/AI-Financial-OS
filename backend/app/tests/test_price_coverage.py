"""Tests for Portfolio Price Coverage Audit.

All external providers (Finnhub, Alpha Vantage, yfinance) are mocked.
No internet access required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.investments.price_coverage_audit import (
    DEFAULT_ASSETS,
    audit_asset,
    run_audit,
)
from app.modules.market_intelligence.ingestion.equity_quote_service import EquityQuoteResult

QUOTE_PATH = "app.modules.investments.price_coverage_audit.get_equity_quote"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ok_quote(price: float = 150.0, currency: str = "USD", provider: str = "finnhub") -> EquityQuoteResult:
    return EquityQuoteResult(
        ticker="TEST", price=price, currency=currency, provider=provider,
        retrieved_at=datetime.now(timezone.utc), success=True,
    )


def _fail_quote() -> EquityQuoteResult:
    return EquityQuoteResult(
        ticker="TEST", price=0.0, currency="", provider="none",
        retrieved_at=datetime.now(timezone.utc), success=False,
        error="All providers failed",
    )


# ── Asset Resolution ──────────────────────────────────────────────────────────

def test_resolve_apple():
    r = resolve_asset("Apple")
    assert r.status == "resolved"
    assert r.selected.ticker == "AAPL"
    assert r.selected.exchange == "NASDAQ"
    assert r.selected.currency == "USD"


def test_resolve_iberdrola():
    r = resolve_asset("Iberdrola")
    assert r.status == "resolved"
    assert r.selected.ticker == "IBE.MC"
    assert r.selected.exchange == "BME"
    assert r.selected.currency == "EUR"


def test_resolve_bbva():
    r = resolve_asset("Banco Bilbao Vizcaya Argentaria")
    assert r.status == "resolved"
    assert r.selected.ticker == "BBVA"
    assert r.selected.yfinance_symbol == "BBVA.MC"
    assert r.selected.currency == "EUR"


def test_resolve_asml():
    r = resolve_asset("ASML")
    assert r.status == "resolved"
    assert r.selected.ticker == "ASML"
    assert r.selected.yfinance_symbol == "ASML.AS"
    assert r.selected.exchange == "AMS"


def test_resolve_spacex():
    r = resolve_asset("SpaceX")
    assert r.status == "resolved"
    assert r.selected.ticker == "SPCX"
    assert r.selected.exchange == "NASDAQ"


def test_resolve_droneshield():
    r = resolve_asset("DroneShield")
    assert r.status == "resolved"
    assert r.selected.ticker == "DRO.AX"
    assert r.selected.exchange == "ASX"
    assert r.selected.currency == "AUD"


def test_resolve_unknown():
    r = resolve_asset("Empresa Inventada XYZ")
    assert r.status == "unavailable"
    assert r.selected is None


# ── Coverage Audit ────────────────────────────────────────────────────────────

def test_audit_ok_when_finnhub_returns_eur_price():
    # EUR asset with EUR price from finnhub → OK (no FX, no secondary provider)
    with patch(QUOTE_PATH, return_value=_ok_quote(10.5, "EUR", "finnhub")):
        result = audit_asset("Iberdrola")
    assert result.status == "OK"
    assert result.selected_ticker == "IBE.MC"
    assert result.price == 10.5
    assert result.provider == "finnhub"
    assert result.requires_fx_conversion is False


def test_audit_partial_when_usd_price_in_eur_portfolio():
    # USD asset in EUR portfolio → PARTIAL because requires_fx_conversion
    with patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")):
        result = audit_asset("Apple")
    assert result.status == "PARTIAL"
    assert result.selected_ticker == "AAPL"
    assert result.price == 150.0
    assert result.provider == "finnhub"
    assert result.requires_fx_conversion is True


def test_audit_partial_when_yfinance_used():
    with patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "yfinance")):
        result = audit_asset("Apple")
    assert result.status == "PARTIAL"
    assert any("yfinance" in n for n in result.notes)


def test_audit_partial_when_fx_required():
    with patch(QUOTE_PATH, return_value=_ok_quote(1.2, "AUD", "finnhub")):
        result = audit_asset("DroneShield")
    assert result.status == "PARTIAL"
    assert result.requires_fx_conversion is True


def test_audit_eur_asset_no_fx_required():
    with patch(QUOTE_PATH, return_value=_ok_quote(10.0, "EUR", "finnhub")):
        result = audit_asset("Iberdrola")
    # EUR asset with EUR price — no FX required
    assert result.requires_fx_conversion is False


def test_audit_unavailable_when_all_providers_fail():
    with patch(QUOTE_PATH, return_value=_fail_quote()):
        result = audit_asset("Apple")
    assert result.status == "UNAVAILABLE"
    assert result.price is None
    assert result.provider is None


def test_audit_error_when_provider_raises():
    with patch(QUOTE_PATH, side_effect=RuntimeError("connection timeout")):
        result = audit_asset("Apple")
    assert result.status == "ERROR"
    assert result.price is None


def test_audit_unavailable_when_asset_not_known():
    result = audit_asset("Empresa Inventada XYZ")
    assert result.status == "UNAVAILABLE"


def test_run_audit_summary_totals():
    results = iter([_ok_quote(), _fail_quote()])

    def side_effect(*args, **kwargs):
        return next(results)

    with patch(QUOTE_PATH, side_effect=side_effect):
        report = run_audit(["Apple", "Microsoft"])

    assert report.summary.total == 2
    assert len(report.assets) == 2
    # One OK/PARTIAL and one UNAVAILABLE
    statuses = {r.status for r in report.assets}
    assert "UNAVAILABLE" in statuses


def test_run_audit_does_not_raise_on_provider_failure():
    with patch(QUOTE_PATH, side_effect=RuntimeError("timeout")):
        report = run_audit(["Apple", "Microsoft"])
    assert all(r.status == "ERROR" for r in report.assets)


def test_default_assets_count():
    assert len(DEFAULT_ASSETS) == 19


# ── API Endpoints ─────────────────────────────────────────────────────────────

def test_get_default_assets(client):
    r = client.get("/api/investments/price-coverage/default-assets")
    assert r.status_code == 200
    assets = r.json()
    assert len(assets) == 19
    assert "Apple" in assets


def test_resolve_endpoint(client):
    r = client.post(
        "/api/investments/price-coverage/resolve",
        json={"asset_name": "Apple"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["selected"]["ticker"] == "AAPL"


def test_resolve_endpoint_unknown(client):
    r = client.post(
        "/api/investments/price-coverage/resolve",
        json={"asset_name": "Empresa Fantasma"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "unavailable"
    assert data["selected"] is None


def test_audit_endpoint_summary(client):
    with patch(QUOTE_PATH, return_value=_ok_quote(200.0, "USD", "finnhub")):
        r = client.post(
            "/api/investments/price-coverage/audit",
            json={"assets": [{"name": "Apple"}, {"name": "Microsoft"}], "force_refresh": False},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 2
    assert "generated_at" in data
    assert len(data["assets"]) == 2


def test_audit_endpoint_empty_body_uses_defaults(client):
    with patch(QUOTE_PATH, return_value=_ok_quote(100.0, "USD", "finnhub")):
        r = client.post("/api/investments/price-coverage/audit", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 19
