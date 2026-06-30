"""Tests for Portfolio Price Coverage Audit.

All external providers (Finnhub, Alpha Vantage, yfinance) are mocked.
No internet access required.

Conceptual model tested here:
  OK         – price available AND valued in EUR
  FX_PENDING – price available but FX rate could not be fetched
  AMBIGUOUS  – multiple tickers, user must confirm
  UNAVAILABLE– no price from any provider
  ERROR      – technical error during quote fetch
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
FX_PATH = "app.modules.investments.price_coverage_audit.fetch_fx_rate"


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


def _fx_ok(rate: float = 1.08) -> tuple:
    """Simulates a successful FX rate fetch: 1 EUR = rate USD."""
    return (rate, "EURUSD=X", datetime.now(timezone.utc))


def _fx_fail() -> tuple:
    return (None, "EURUSD=X", None)


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
    # ticker must match the BME exchange-qualified symbol, not the NYSE ADR
    assert r.selected.ticker == "BBVA.MC"
    assert r.selected.yfinance_symbol == "BBVA.MC"
    assert r.selected.exchange == "BME"
    assert r.selected.currency == "EUR"


def test_resolve_asml():
    r = resolve_asset("ASML")
    assert r.status == "resolved"
    # ticker must match the Euronext Amsterdam listing (EUR), not the NASDAQ listing (USD)
    assert r.selected.ticker == "ASML.AS"
    assert r.selected.yfinance_symbol == "ASML.AS"
    assert r.selected.exchange == "AMS"
    assert r.selected.currency == "EUR"


def test_resolve_spacex():
    # SpaceX is private; SPCX is an unrelated ETF → must require confirmation
    r = resolve_asset("SpaceX")
    assert r.status == "ambiguous"
    assert r.selected is None
    assert len(r.candidates) == 1
    assert r.candidates[0].ticker == "SPCX"
    assert r.candidates[0].requires_confirmation is True
    assert "privada" in r.candidates[0].confirmation_note.lower()


def test_resolve_spacex_audit_returns_ambiguous():
    """audit_asset must propagate the confirmation note and expose the candidate ticker."""
    result = audit_asset("SpaceX")
    assert result.status == "AMBIGUOUS"
    assert result.selected_ticker == "SPCX"  # candidate visible for display
    assert "SpaceX" in result.notes[0] or "privada" in result.notes[0].lower()


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


# ── Price Coverage: EUR assets ────────────────────────────────────────────────

def test_audit_ok_eur_asset_with_eur_price():
    """EUR asset → no FX needed → OK immediately."""
    with patch(QUOTE_PATH, return_value=_ok_quote(10.5, "EUR", "finnhub")):
        result = audit_asset("Iberdrola")
    assert result.status == "OK"
    assert result.selected_ticker == "IBE.MC"
    assert result.price == 10.5
    assert result.requires_fx_conversion is False
    assert result.eur_price == 10.5
    assert result.fx_rate is None


# ── Price Coverage: USD assets with FX ───────────────────────────────────────

def test_audit_ok_when_usd_price_and_fx_available():
    """USD price + FX rate available → OK with eur_price computed."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_ok(1.08)),
    ):
        result = audit_asset("Apple")
    assert result.status == "OK"
    assert result.requires_fx_conversion is True
    assert result.fx_rate == 1.08
    assert result.eur_price == pytest.approx(150.0 / 1.08, rel=1e-3)
    assert result.price == 150.0
    assert result.price_currency == "USD"


def test_audit_fx_pending_when_usd_price_but_fx_unavailable():
    """USD price available but FX fetch fails → FX_PENDING (not PARTIAL, not error)."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_fail()),
    ):
        result = audit_asset("Apple")
    assert result.status == "FX_PENDING"
    assert result.requires_fx_conversion is True
    assert result.price == 150.0
    assert result.eur_price is None
    assert "Falta conversión a EUR" in result.notes[0]


def test_audit_ok_when_aud_price_and_fx_available():
    """AUD price + FX available → OK."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(1.2, "AUD", "finnhub")),
        patch(FX_PATH, return_value=(1.65, "EURAUD=X", datetime.now(timezone.utc))),
    ):
        result = audit_asset("DroneShield")
    assert result.status == "OK"
    assert result.requires_fx_conversion is True
    assert result.eur_price == pytest.approx(1.2 / 1.65, rel=1e-3)


def test_audit_fx_pending_when_aud_price_and_fx_unavailable():
    """AUD price but FX fails → FX_PENDING."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(1.2, "AUD", "finnhub")),
        patch(FX_PATH, return_value=(None, "EURAUD=X", None)),
    ):
        result = audit_asset("DroneShield")
    assert result.status == "FX_PENDING"
    assert result.eur_price is None


# ── yfinance as provider does NOT degrade status ──────────────────────────────

def test_audit_ok_when_yfinance_used_with_fx():
    """yfinance as provider is NOT a degradation. Status depends only on FX."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "yfinance")),
        patch(FX_PATH, return_value=_fx_ok(1.08)),
    ):
        result = audit_asset("Apple")
    assert result.status == "OK"
    assert result.provider == "yfinance"


def test_audit_fx_pending_when_yfinance_used_and_fx_fails():
    """yfinance + FX failure → FX_PENDING (not PARTIAL)."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "yfinance")),
        patch(FX_PATH, return_value=_fx_fail()),
    ):
        result = audit_asset("Apple")
    assert result.status == "FX_PENDING"


# ── Failure cases ─────────────────────────────────────────────────────────────

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


# ── AuditSummary ──────────────────────────────────────────────────────────────

def test_run_audit_summary_all_ok():
    """All assets with EUR price → with_price == eur_valued == total."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(10.0, "EUR", "finnhub")),
    ):
        report = run_audit(["Iberdrola", "BBVA"])  # both EUR
    assert report.summary.total == 2
    assert report.summary.with_price == 2
    assert report.summary.eur_valued == 2
    assert report.summary.fx_pending == 0


def test_run_audit_summary_fx_pending():
    """USD assets with no FX → all FX_PENDING."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_fail()),
    ):
        report = run_audit(["Apple", "Microsoft"])
    assert report.summary.total == 2
    assert report.summary.with_price == 2
    assert report.summary.eur_valued == 0
    assert report.summary.fx_pending == 2


def test_run_audit_summary_mixed():
    quotes = iter([_ok_quote(10.0, "EUR", "finnhub"), _fail_quote()])

    def side_effect(*args, **kwargs):
        return next(quotes)

    with patch(QUOTE_PATH, side_effect=side_effect):
        report = run_audit(["Iberdrola", "Apple"])

    statuses = {r.status for r in report.assets}
    assert "UNAVAILABLE" in statuses
    assert report.summary.total == 2
    assert report.summary.with_price == 1  # only Iberdrola
    assert report.summary.unavailable == 1


def test_run_audit_does_not_raise_on_provider_failure():
    with patch(QUOTE_PATH, side_effect=RuntimeError("timeout")):
        report = run_audit(["Apple", "Microsoft"])
    assert all(r.status == "ERROR" for r in report.assets)
    assert report.summary.error == 2
    assert report.summary.with_price == 0


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
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(200.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_ok(1.08)),
    ):
        r = client.post(
            "/api/investments/price-coverage/audit",
            json={"assets": [{"name": "Apple"}, {"name": "Microsoft"}], "force_refresh": False},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 2
    assert data["summary"]["with_price"] == 2
    assert data["summary"]["eur_valued"] == 2
    assert "generated_at" in data
    assert len(data["assets"]) == 2
    # EUR price must be computed
    for asset in data["assets"]:
        assert asset["eur_price"] is not None
        assert asset["fx_rate"] == pytest.approx(1.08)


def test_audit_endpoint_fx_pending(client):
    """Endpoint returns FX_PENDING status when FX is unavailable."""
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(200.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_fail()),
    ):
        r = client.post(
            "/api/investments/price-coverage/audit",
            json={"assets": [{"name": "Apple"}]},
        )
    assert r.status_code == 200
    data = r.json()
    asset = data["assets"][0]
    assert asset["status"] == "FX_PENDING"
    assert asset["eur_price"] is None
    assert data["summary"]["fx_pending"] == 1
    assert data["summary"]["eur_valued"] == 0


def test_audit_endpoint_empty_body_uses_defaults(client):
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(100.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_ok(1.08)),
    ):
        r = client.post("/api/investments/price-coverage/audit", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 19
