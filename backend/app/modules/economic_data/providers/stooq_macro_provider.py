"""Stooq-backed provider for market-derived macro indicators.

Bridges the existing market_data ProviderRouter (Fase 4.6) to the
economic_data domain. Handles euríbor, bonds, indices and forex symbols
that are already configured in market_data_config.yaml.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.modules.investments.market_data.router import get_quotes

logger = logging.getLogger(__name__)

# Maps (internal_symbol, region, indicator, name, unit)
MACRO_MARKET_SYMBOLS: list[tuple[str, str, str, str, str]] = [
    # Euríbor
    ("EUR3M",   "EA", "euribor",   "Euríbor 3M",          "%"),
    # Bonds
    ("ES10Y",   "ES", "bond_10y",  "Bono España 10Y",      "%"),
    ("DE10Y",   "EA", "bond_10y",  "Bund Alemania 10Y",    "%"),
    ("US10Y",   "US", "bond_10y",  "Treasury EEUU 10Y",    "%"),
    # Indices
    ("IBEX35",        "ES", "index", "IBEX 35",            "pts"),
    ("EUROSTOXX50",   "EA", "index", "Euro Stoxx 50",      "pts"),
    ("SP500",         "US", "index", "S&P 500",            "pts"),
    ("NASDAQ100",     "US", "index", "Nasdaq 100",         "pts"),
    ("DOWJONES",      "US", "index", "Dow Jones",          "pts"),
    # Forex
    ("EURUSD",  "GLOBAL", "forex", "EUR/USD",              "USD"),
]

_MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_period(ts_str: str) -> str:
    try:
        d = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return f"{_MONTHS_ES[d.month]} {d.year}"
    except Exception:
        return ts_str


class StooqMacroProvider:
    def fetch_all(self) -> list[dict]:
        symbol_map = {sym: (sym, region, indicator, name, unit)
                      for sym, region, indicator, name, unit in MACRO_MARKET_SYMBOLS}

        try:
            quotes = {q.symbol: q for q in get_quotes()}
        except Exception as exc:
            logger.error("StooqMacroProvider: failed to get quotes: %s", exc)
            return []

        results = []
        for sym, (_, region, indicator, name, unit) in symbol_map.items():
            q = quotes.get(sym)
            if q is None or q.price is None:
                continue
            results.append({
                "series_id": sym,
                "region": region,
                "indicator": indicator,
                "name": name,
                "unit": unit,
                "source": "STOOQ",
                "value": q.price,
                "prev_value": (q.price - q.change_absolute) if q.change_absolute is not None else None,
                "observation_date": q.last_updated[:10] if q.last_updated else datetime.now(timezone.utc).date().isoformat(),
                "period": _format_period(q.last_updated) if q.last_updated else "",
            })
        return results
