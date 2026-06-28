"""Orchestrates asset resolution + equity quote fetching to classify price coverage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.modules.investments.asset_resolution import resolve_asset
from app.modules.market_intelligence.ingestion.equity_quote_service import get_equity_quote

FRESHNESS_OK_HOURS = 24
FRESHNESS_PARTIAL_HOURS = 72

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
    status: str  # OK | PARTIAL | AMBIGUOUS | UNAVAILABLE | MANUAL | ERROR
    confidence: float
    notes: list[str] = field(default_factory=list)


@dataclass
class AuditSummary:
    total: int = 0
    ok: int = 0
    partial: int = 0
    ambiguous: int = 0
    manual: int = 0
    unavailable: int = 0
    error: int = 0


@dataclass
class AuditReport:
    generated_at: datetime
    summary: AuditSummary
    assets: list[CoverageAssetResult]


def _classify(
    resolution_status: str,
    quote_success: bool,
    freshness_hours: Optional[float],
    requires_fx: bool,
    provider: Optional[str],
) -> tuple[str, list[str]]:
    notes: list[str] = []

    if resolution_status == "ambiguous":
        return "AMBIGUOUS", ["Multiples tickers posibles. Requiere confirmacion."]
    if resolution_status == "unavailable":
        return "UNAVAILABLE", ["No se encontro ticker para este activo."]
    if not quote_success:
        return "UNAVAILABLE", ["Ningun proveedor devolvio precio."]

    is_partial = False
    if freshness_hours is not None and freshness_hours > FRESHNESS_OK_HOURS:
        is_partial = True
        notes.append(f"Precio retrasado ({freshness_hours:.0f}h).")
    if requires_fx:
        is_partial = True
        notes.append("Precio en divisa extranjera (conversion FX no implementada).")
    if provider == "yfinance":
        is_partial = True
        notes.append("Precio obtenido via yfinance (proveedor secundario).")

    return ("PARTIAL" if is_partial else "OK"), notes


def audit_asset(asset_name: str) -> CoverageAssetResult:
    resolution = resolve_asset(asset_name)

    # Handle unresolvable or ambiguous cases before querying providers
    if resolution.status == "ambiguous":
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
            status="AMBIGUOUS",
            confidence=0.5,
            notes=["Multiples tickers posibles. Requiere confirmacion."],
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
            notes=["No se encontro ticker para este activo."],
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
            notes=["Error tecnico al consultar proveedor."],
        )

    now = datetime.now(timezone.utc)
    freshness_hours: Optional[float] = None
    if quote.retrieved_at:
        diff = now - quote.retrieved_at
        freshness_hours = diff.total_seconds() / 3600

    # FX required if price currency is not EUR (portfolio base currency)
    requires_fx = quote.success and quote.currency not in ("EUR", "")

    status, notes = _classify(
        resolution_status=resolution.status,
        quote_success=quote.success,
        freshness_hours=freshness_hours,
        requires_fx=requires_fx,
        provider=quote.provider if quote.success else None,
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
    )


def run_audit(assets: list[str]) -> AuditReport:
    results: list[CoverageAssetResult] = []
    summary = AuditSummary(total=len(assets))

    for name in assets:
        result = audit_asset(name)
        results.append(result)
        s = result.status.lower()
        if s == "ok":
            summary.ok += 1
        elif s == "partial":
            summary.partial += 1
        elif s == "ambiguous":
            summary.ambiguous += 1
        elif s == "manual":
            summary.manual += 1
        elif s == "unavailable":
            summary.unavailable += 1
        elif s == "error":
            summary.error += 1

    return AuditReport(
        generated_at=datetime.now(timezone.utc),
        summary=summary,
        assets=results,
    )
