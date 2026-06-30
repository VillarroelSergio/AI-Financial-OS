"""Tests for Portfolio Import Assistant.

All external providers (Finnhub, Alpha Vantage, yfinance) are mocked.
No internet access required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.modules.investments.portfolio_import_service import (
    _parse_number,
    estimate_cost,
    parse_text_positions,
    validate_position,
)

QUOTE_PATH = "app.modules.investments.price_coverage_audit.get_equity_quote"
FX_PATH = "app.modules.investments.price_coverage_audit.fetch_fx_rate"


# ── Helpers (shared with price-coverage tests) ────────────────────────────────

from app.modules.market_intelligence.ingestion.equity_quote_service import EquityQuoteResult


def _ok_quote(price=150.0, currency="USD", provider="finnhub"):
    return EquityQuoteResult(
        ticker="TEST", price=price, currency=currency, provider=provider,
        retrieved_at=datetime.now(timezone.utc), success=True,
    )


def _fail_quote():
    return EquityQuoteResult(
        ticker="TEST", price=0.0, currency="", provider="none",
        retrieved_at=datetime.now(timezone.utc), success=False,
        error="All providers failed",
    )


def _fx_ok(rate=1.08):
    return (rate, "EURUSD=X", datetime.now(timezone.utc))


def _fx_fail():
    return (None, "EURUSD=X", None)


# ── Number parser ─────────────────────────────────────────────────────────────

def test_parse_number_dot_decimal():
    assert _parse_number("140.15") == pytest.approx(140.15)


def test_parse_number_comma_decimal():
    assert _parse_number("140,15") == pytest.approx(140.15)


def test_parse_number_spanish_thousands():
    assert _parse_number("1.234,56") == pytest.approx(1234.56)


def test_parse_number_fractional():
    assert _parse_number("0,564555") == pytest.approx(0.564555)


def test_parse_number_invalid():
    assert _parse_number("n/a") is None


# ── Cost estimation ───────────────────────────────────────────────────────────

def test_estimate_cost_positive_return():
    # 140.15 / 1.3876 ≈ 100.99
    cost = estimate_cost(140.15, 38.76)
    assert cost == pytest.approx(100.99, rel=1e-2)


def test_estimate_cost_negative_return():
    # 280.50 / 0.9477 ≈ 296.0
    cost = estimate_cost(280.50, -5.23)
    assert cost == pytest.approx(280.50 / (1 - 5.23 / 100), rel=1e-3)


def test_estimate_cost_zero_return():
    assert estimate_cost(100.0, 0.0) == pytest.approx(100.0)


# ── Text parser ───────────────────────────────────────────────────────────────

_SAMPLE_TEXT = """Apple
x 0,564555
140,15 €
+38,76 %

Microsoft
x 1,234
280,50 €
-5,23 %"""


def test_parse_text_block_count():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert len(positions) == 2


def test_parse_text_apple_name():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert positions[0].raw_name == "Apple"


def test_parse_text_apple_quantity():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert positions[0].quantity == pytest.approx(0.564555)


def test_parse_text_apple_value():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert positions[0].current_value == pytest.approx(140.15)
    assert positions[0].current_value_currency == "EUR"


def test_parse_text_apple_return():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert positions[0].return_pct == pytest.approx(38.76)


def test_parse_text_microsoft_negative_return():
    positions = parse_text_positions(_SAMPLE_TEXT)
    assert positions[1].return_pct == pytest.approx(-5.23)


def test_parse_text_empty():
    assert parse_text_positions("") == []


def test_parse_text_single_line_asset():
    positions = parse_text_positions("Iberdrola\n1,5\n12,30 €\n+2,10 %")
    assert len(positions) == 1
    assert positions[0].raw_name == "Iberdrola"
    assert positions[0].quantity == pytest.approx(1.5)


def test_parse_text_no_return():
    # Some brokers don't show return percentage
    positions = parse_text_positions("Apple\nx 1,5\n150,00 €")
    assert len(positions) == 1
    assert positions[0].return_pct is None
    assert positions[0].quantity == pytest.approx(1.5)


def test_parse_text_usd_value():
    positions = parse_text_positions("NVIDIA\n2\n$900.50\n+120.5%")
    assert len(positions) == 1
    assert positions[0].current_value_currency == "USD"


# ── Validate position ─────────────────────────────────────────────────────────

def test_validate_apple_resolved():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_ok(1.08)),
    ):
        pos = validate_position("Apple", quantity=0.5, current_value=140.15, current_value_currency="EUR", return_pct=38.76)

    assert pos.resolution_status == "resolved"
    assert pos.selected_ticker == "AAPL"
    assert pos.import_status == "READY"
    assert pos.estimated_cost == pytest.approx(estimate_cost(140.15, 38.76), rel=1e-3)
    assert pos.is_cost_estimated is True


def test_validate_estimated_cost_computed():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(10.0, "EUR", "finnhub")),
    ):
        pos = validate_position("Iberdrola", quantity=5, current_value=50.0, return_pct=10.0)

    assert pos.estimated_cost == pytest.approx(estimate_cost(50.0, 10.0), rel=1e-3)


def test_validate_no_cost_without_return():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(10.0, "EUR", "finnhub")),
    ):
        pos = validate_position("Iberdrola", quantity=5)

    assert pos.estimated_cost is None
    assert pos.is_cost_estimated is False


def test_validate_unavailable_asset():
    pos = validate_position("Empresa Inventada XYZ")
    assert pos.resolution_status == "unavailable"
    assert pos.import_status == "REVIEW"


def test_validate_spacex_requires_confirmation():
    pos = validate_position("SpaceX")
    assert pos.resolution_status == "ambiguous"
    assert pos.requires_confirmation is True
    assert pos.import_status == "REQUIRES_CONFIRMATION"


def test_validate_bbva_resolved():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(8.0, "EUR", "yfinance")),
    ):
        pos = validate_position("BBVA")

    assert pos.resolution_status == "resolved"
    assert pos.selected_ticker == "BBVA.MC"
    assert pos.currency == "EUR"


def test_validate_droneshield_aud():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(1.2, "AUD", "yfinance")),
        patch(FX_PATH, return_value=(1.65, "EURAUD=X", datetime.now(timezone.utc))),
    ):
        pos = validate_position("DroneShield", quantity=100, current_value=120.0, current_value_currency="AUD", return_pct=5.0)

    assert pos.selected_ticker == "DRO.AX"
    assert pos.import_status == "READY"
    assert pos.eur_price is not None


def test_validate_fx_pending_status():
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(150.0, "USD", "finnhub")),
        patch(FX_PATH, return_value=_fx_fail()),
    ):
        pos = validate_position("Apple", quantity=1, current_value=150.0, return_pct=10.0)

    # FX_PENDING still means we can import (price is known, just EUR value pending)
    assert pos.coverage_status == "FX_PENDING"
    assert pos.import_status == "READY"


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_parse_text_endpoint(client):
    r = client.post(
        "/api/investments/import/parse-text",
        json={"text": _SAMPLE_TEXT},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["raw_name"] == "Apple"
    assert data[0]["quantity"] == pytest.approx(0.564555)
    assert data[0]["current_value"] == pytest.approx(140.15)
    assert data[0]["return_pct"] == pytest.approx(38.76)


def test_parse_text_endpoint_empty(client):
    r = client.post("/api/investments/import/parse-text", json={"text": ""})
    assert r.status_code == 422


def test_validate_batch_endpoint(client):
    with (
        patch(QUOTE_PATH, return_value=_ok_quote(10.0, "EUR", "finnhub")),
    ):
        r = client.post(
            "/api/investments/import/validate",
            json={
                "positions": [
                    {
                        "raw_name": "Iberdrola",
                        "quantity": 5.0,
                        "current_value": 50.0,
                        "current_value_currency": "EUR",
                        "return_pct": 10.0,
                        "raw_text": "",
                    }
                ]
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["selected_ticker"] == "IBE.MC"
    assert data[0]["resolution_status"] == "resolved"
    assert data[0]["import_status"] == "READY"
    assert data[0]["estimated_cost"] == pytest.approx(estimate_cost(50.0, 10.0), rel=1e-3)


def test_validate_batch_empty(client):
    r = client.post("/api/investments/import/validate", json={"positions": []})
    assert r.status_code == 200
    assert r.json() == []


def test_validate_spacex_endpoint(client):
    r = client.post(
        "/api/investments/import/validate",
        json={
            "positions": [
                {"raw_name": "SpaceX", "raw_text": ""}
            ]
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data[0]["import_status"] == "REQUIRES_CONFIRMATION"
    assert data[0]["requires_confirmation"] is True


# ── Screenshot / Opción B ─────────────────────────────────────────────────────

def test_screenshot_endpoint_not_creates_holdings_without_review():
    """La captura NO debe crear holdings directamente — solo debe devolver datos para revisión.

    Opción B: no existe ruta de screenshot en el router. Las imágenes no se procesan
    ni se envían a servicios externos. Los holdings solo se crean tras confirmación
    explícita del usuario a través de /confirm.
    """
    from app.modules.investments.portfolio_import_routes import router

    screenshot_routes = [r for r in router.routes if "screenshot" in str(r.path)]
    # Opción B implementada: no debe existir ninguna ruta de screenshot
    assert len(screenshot_routes) == 0, (
        f"Se encontraron rutas de screenshot inesperadas: {[r.path for r in screenshot_routes]}. "
        "La extracción automática desde captura no está disponible en esta fase (Opción B)."
    )
