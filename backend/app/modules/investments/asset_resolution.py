"""Maps asset names to canonical tickers for the 19 known portfolio assets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TickerCandidate:
    ticker: str
    yfinance_symbol: str
    name: str
    exchange: str
    currency: str
    asset_type: str = "equity"
    confidence: float = 1.0


@dataclass
class AssetResolution:
    asset_name: str
    candidates: list[TickerCandidate]
    selected: Optional[TickerCandidate]
    status: str  # resolved | ambiguous | manual | unavailable


# Known asset registry — tickers hardcoded for resolution only, never prices
_KNOWN: dict[str, TickerCandidate] = {
    "banco bilbao vizcaya argentaria": TickerCandidate(
        ticker="BBVA", yfinance_symbol="BBVA.MC",
        name="Banco Bilbao Vizcaya Argentaria SA",
        exchange="BME", currency="EUR",
    ),
    "bbva": TickerCandidate(
        ticker="BBVA", yfinance_symbol="BBVA.MC",
        name="Banco Bilbao Vizcaya Argentaria SA",
        exchange="BME", currency="EUR",
    ),
    "apple": TickerCandidate(
        ticker="AAPL", yfinance_symbol="AAPL",
        name="Apple Inc.", exchange="NASDAQ", currency="USD",
    ),
    "iberdrola": TickerCandidate(
        ticker="IBE.MC", yfinance_symbol="IBE.MC",
        name="Iberdrola SA", exchange="BME", currency="EUR",
    ),
    "asml": TickerCandidate(
        ticker="ASML", yfinance_symbol="ASML.AS",
        name="ASML Holding NV", exchange="AMS", currency="EUR",
    ),
    "caterpillar": TickerCandidate(
        ticker="CAT", yfinance_symbol="CAT",
        name="Caterpillar Inc.", exchange="NYSE", currency="USD",
    ),
    "alphabet": TickerCandidate(
        ticker="GOOGL", yfinance_symbol="GOOGL",
        name="Alphabet Inc. (A)", exchange="NASDAQ", currency="USD",
    ),
    "waste management": TickerCandidate(
        ticker="WM", yfinance_symbol="WM",
        name="Waste Management Inc.", exchange="NYSE", currency="USD",
    ),
    "tsmc": TickerCandidate(
        ticker="TSM", yfinance_symbol="TSM",
        name="Taiwan Semiconductor Mfg Co. (ADR)",
        exchange="NYSE", currency="USD",
    ),
    "johnson & johnson": TickerCandidate(
        ticker="JNJ", yfinance_symbol="JNJ",
        name="Johnson & Johnson", exchange="NYSE", currency="USD",
    ),
    "johnson and johnson": TickerCandidate(
        ticker="JNJ", yfinance_symbol="JNJ",
        name="Johnson & Johnson", exchange="NYSE", currency="USD",
    ),
    "lockheed martin": TickerCandidate(
        ticker="LMT", yfinance_symbol="LMT",
        name="Lockheed Martin Corp.", exchange="NYSE", currency="USD",
    ),
    "nvidia": TickerCandidate(
        ticker="NVDA", yfinance_symbol="NVDA",
        name="NVIDIA Corp.", exchange="NASDAQ", currency="USD",
    ),
    "spacex": TickerCandidate(
        ticker="SPCX", yfinance_symbol="SPCX",
        name="SpaceX", exchange="NASDAQ", currency="USD",
    ),
    "amazon": TickerCandidate(
        ticker="AMZN", yfinance_symbol="AMZN",
        name="Amazon.com Inc.", exchange="NASDAQ", currency="USD",
    ),
    "amazon.com": TickerCandidate(
        ticker="AMZN", yfinance_symbol="AMZN",
        name="Amazon.com Inc.", exchange="NASDAQ", currency="USD",
    ),
    "rocket lab": TickerCandidate(
        ticker="RKLB", yfinance_symbol="RKLB",
        name="Rocket Lab USA Inc.", exchange="NASDAQ", currency="USD",
    ),
    "rtx": TickerCandidate(
        ticker="RTX", yfinance_symbol="RTX",
        name="RTX Corporation", exchange="NYSE", currency="USD",
    ),
    "rtx corporation": TickerCandidate(
        ticker="RTX", yfinance_symbol="RTX",
        name="RTX Corporation", exchange="NYSE", currency="USD",
    ),
    "berkshire hathaway": TickerCandidate(
        ticker="BRK-B", yfinance_symbol="BRK-B",
        name="Berkshire Hathaway Inc. (B)", exchange="NYSE", currency="USD",
    ),
    "visa": TickerCandidate(
        ticker="V", yfinance_symbol="V",
        name="Visa Inc.", exchange="NYSE", currency="USD",
    ),
    "microsoft": TickerCandidate(
        ticker="MSFT", yfinance_symbol="MSFT",
        name="Microsoft Corp.", exchange="NASDAQ", currency="USD",
    ),
    "droneshield": TickerCandidate(
        ticker="DRO.AX", yfinance_symbol="DRO.AX",
        name="DroneShield Ltd.", exchange="ASX", currency="AUD",
    ),
}


def _normalize(name: str) -> str:
    return name.lower().strip()


def resolve_asset(asset_name: str) -> AssetResolution:
    """Resolve an asset name to a ticker candidate."""
    key = _normalize(asset_name)

    # Exact match
    if key in _KNOWN:
        candidate = _KNOWN[key]
        return AssetResolution(
            asset_name=asset_name,
            candidates=[candidate],
            selected=candidate,
            status="resolved",
        )

    # Substring match: key appears inside a known key
    seen: set[str] = set()
    matches: list[TickerCandidate] = []
    for k, c in _KNOWN.items():
        if key in k and c.ticker not in seen:
            seen.add(c.ticker)
            matches.append(c)

    if len(matches) == 1:
        return AssetResolution(
            asset_name=asset_name,
            candidates=matches,
            selected=matches[0],
            status="resolved",
        )
    if len(matches) > 1:
        return AssetResolution(
            asset_name=asset_name,
            candidates=matches,
            selected=None,
            status="ambiguous",
        )

    return AssetResolution(
        asset_name=asset_name,
        candidates=[],
        selected=None,
        status="unavailable",
    )
