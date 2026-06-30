"""Orchestrates asset resolution + equity quote fetching to classify price coverage.

Conceptual model (three separate concerns):
  1. Price coverage  – can we get a current valid price for the asset?
  2. FX conversion   – can we convert the original price to EUR?
  3. EUR valuation   – can we compute the final EUR value?

Statuses:
  OK         – price available AND valued in EUR (no FX needed, or FX converted)
  FX_PENDING – price available but FX rate could not be fetched
  AMBIGUOUS  – multiple tickers found; user confirmation required
  UNAVAILABLE– no price found from any provider
  MANUAL     – asset has no ticker / marked manual
  ERROR      – technical error during provider query
"""
from __future__ import annotations

import yfinance as yf

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.market_intelligence.ingestion.equity_quote_service import get_equity_quote

FRESHNESS_OK_HOURS = 24
FRESHNESS_WARN_HOURS = 72

# EUR/XXX tickers on yfinance — rate = units of XXX per 1 EUR
FX_TICKER_MAP: dict[str, str] = {
    "USD": "EURUSD=X",
    "AUD": "EURAUD=X",
    "GBP": "EURGBP=X",
    "CHF": "EURCHF=X",
}

DEFAULT_ASSETS: list[str] = [
    "Banco Bilbao Vizcaya Argentaria",
    "Apple",
    "Iberdrola",
    "ASML",
    "Caterpillar",
    "Alphabet",
    "Waste Management",
    "TSMC",
    "Johnson & Johnson",
    "Lockheed Martin",
    "NVIDIA",
    "SpaceX",
    "Amazon",
    "Rocket Lab",
    "RTX Corporation",
    "Berkshire Hathaway",
    "Visa",
    "Microsoft",
    "DroneShield",
]


@dataclass
class CoverageAssetResult:
    asset_name: str
    selected_ticker: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    provider: Optional[str]
    price: Optional[float]
    price_currency: Optional[str]
    requires_fx_conversion: bool
    last_update: Optional[datetime]
    freshness_hours: Optional[float]
    from_cache: bool
    status: str  # OK | FX_PENDING | AMBIGUOUS | UNAVAILABLE | MANUAL | ERROR
    confidence: float
    notes: list[str] = field(default_factory=list)
    # FX / EUR valuation
    fx_rate: Optional[float] = None          # units of original currency per 1 EUR
    fx_currency_pair: Optional[str] = None   # e.g. "EURUSD=X"
    eur_price: Optional[float] = None        # price converted to EUR
    fx_updated_at: Optional[datetime] = None


@dataclass
class AuditSummary:
    total: int = 0
    with_price: int = 0     # has a valid price (OK + FX_PENDING)
    eur_valued: int = 0     # fully valued in EUR (OK)
    fx_pending: int = 0     # price ok but FX unavailable
    ambiguous: int = 0
    manual: int = 0
    unavailable: int = 0
    error: int = 0


@dataclass
class AuditReport:
    generated_at: datetime
    summary: AuditSummary
    assets: list[CoverageAssetResult]


def fetch_fx_rate(currency: str) -> tuple[Optional[float], Optional[str], Optional[datetime]]:
    """Return (rate, fx_ticker, retrieved_at) for EUR→currency conversion.

    rate is units of `currency` per 1 EUR (e.g. EURUSD=X gives ~1.08).
    Returns (None, ticker, None) when the rate cannot be fetched.
    EUR itself returns (1.0, None, now).
    """
    if currency == "EUR":
        return 1.0, None, datetime.now(timezone.utc)

    fx_ticker = FX_TICKER_MAP.get(currency)
    if not fx_ticker:
        return None, None, None

    try:
        raw = yf.Ticker(fx_ticker).fast_info.last_price
        if raw is None:
            return None, fx_ticker, None
        return float(raw), fx_ticker, datetime.now(timezone.utc)
    except Exception:
        return None, fx_ticker, None


def _classify(
    resolution_status: str,
    quote_success: bool,
    freshness_hours: Optional[float],
    requires_fx: bool,
    fx_available: bool,
) -> tuple[str, list[str]]:
    """Return (status, notes) given the audit inputs."""
    notes: list[str] = []

    if resolution_status == "ambiguous":
        return "AMBIGUOUS", ["Múltiples tickers posibles. Requiere confirmación."]
    if resolution_status == "unavailable":
        return "UNAVAILABLE", ["No se encontró ticker para este activo."]
    if not quote_success:
        return "UNAVAILABLE", ["Ningún proveedor devolvió precio."]

    if freshness_hours is not None and freshness_hours > FRESHNESS_WARN_HOURS:
        notes.append(f"Precio con más de {freshness_hours:.0f}h de antigüedad.")

    if requires_fx:
        if fx_available:
            notes.append("Precio obtenido correctamente. Convertido a EUR.")
            return "OK", notes
        else:
            notes.append("Precio obtenido correctamente. Falta conversión a EUR.")
            return "FX_PENDING", notes

    notes.append("Activo valorado correctamente en EUR.")
    return "OK", notes


def audit_asset(asset_name: str) -> CoverageAssetResult:
    resolution = resolve_asset(asset_name)

    if resolution.status == "ambiguous":
        # Use the confirmation_note from the candidate if available
        first = resolution.candidates[0] if resolution.candidates else None
        note = (
            first.confirmation_note
            if first and first.confirmation_note
            else "Múltiples tickers posibles. Requiere confirmación."
        )
        return CoverageAssetResult(
            asset_name=asset_name,
            selected_ticker=first.ticker if first else None,
            exchange=first.exchange if first else None,
            currency=first.currency if first else None,
            provider=None,
            price=None,
            price_currency=None,
            requires_fx_conversion=False,
            last_update=None,
            freshness_hours=None,
            from_cache=False,
            status="AMBIGUOUS",
            confidence=first.confidence if first else 0.5,
            notes=[note],
        )

    if resolution.status == "unavailable" or resolution.selected is None:
        return CoverageAssetResult(
            asset_name=asset_name,
            selected_ticker=None,
            exchange=None,
            currency=None,
            provider=None,
            price=None,
            price_currency=None,
            requires_fx_conversion=False,
            last_update=None,
            freshness_hours=None,
            from_cache=False,
            status="UNAVAILABLE",
            confidence=0.0,
            notes=["No se encontró ticker para este activo."],
        )

    selected = resolution.selected

    try:
        quote = get_equity_quote(
            ticker=selected.ticker,
            yfinance_symbol=selected.yfinance_symbol,
            expected_currency=selected.currency,
        )
    except Exception:
        return CoverageAssetResult(
            asset_name=asset_name,
            selected_ticker=selected.ticker,
            exchange=selected.exchange,
            currency=selected.currency,
            provider=None,
            price=None,
            price_currency=None,
            requires_fx_conversion=False,
            last_update=None,
            freshness_hours=None,
            from_cache=False,
            status="ERROR",
            confidence=selected.confidence,
            notes=["Error técnico al consultar proveedor."],
        )

    now = datetime.now(timezone.utc)
    freshness_hours: Optional[float] = None
    if quote.retrieved_at:
        diff = now - quote.retrieved_at
        freshness_hours = diff.total_seconds() / 3600

    requires_fx = quote.success and quote.currency not in ("EUR", "")

    # Attempt FX conversion when needed
    fx_rate: Optional[float] = None
    fx_currency_pair: Optional[str] = None
    eur_price: Optional[float] = None
    fx_updated_at: Optional[datetime] = None
    fx_available = False

    if requires_fx and quote.success and quote.price:
        fx_rate, fx_currency_pair, fx_updated_at = fetch_fx_rate(quote.currency)
        if fx_rate is not None and fx_rate > 0:
            fx_available = True
            eur_price = round(quote.price / fx_rate, 4)
    elif not requires_fx and quote.success and quote.price:
        # Already in EUR
        eur_price = quote.price

    status, notes = _classify(
        resolution_status=resolution.status,
        quote_success=quote.success,
        freshness_hours=freshness_hours,
        requires_fx=requires_fx,
        fx_available=fx_available,
    )

    return CoverageAssetResult(
        asset_name=asset_name,
        selected_ticker=selected.ticker,
        exchange=selected.exchange,
        currency=selected.currency,
        provider=quote.provider if quote.success else None,
        price=quote.price if quote.success else None,
        price_currency=quote.currency if quote.success else None,
        requires_fx_conversion=requires_fx,
        last_update=quote.retrieved_at if quote.success else None,
        freshness_hours=freshness_hours,
        from_cache=quote.from_cache,
        status=status,
        confidence=selected.confidence,
        notes=notes,
        fx_rate=fx_rate,
        fx_currency_pair=fx_currency_pair,
        eur_price=eur_price,
        fx_updated_at=fx_updated_at,
    )


def run_audit(assets: list[str]) -> AuditReport:
    results: list[CoverageAssetResult] = []
    summary = AuditSummary(total=len(assets))

    for name in assets:
        result = audit_asset(name)
        results.append(result)
        s = result.status
        if s == "OK":
            summary.with_price += 1
            summary.eur_valued += 1
        elif s == "FX_PENDING":
            summary.with_price += 1
            summary.fx_pending += 1
        elif s == "AMBIGUOUS":
            summary.ambiguous += 1
        elif s == "MANUAL":
            summary.manual += 1
        elif s == "UNAVAILABLE":
            summary.unavailable += 1
        elif s == "ERROR":
            summary.error += 1

    return AuditReport(
        generated_at=datetime.now(timezone.utc),
        summary=summary,
        assets=results,
    )
