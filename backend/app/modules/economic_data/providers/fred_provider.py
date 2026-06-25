"""FRED (Federal Reserve Bank of St. Louis) data provider.

Fetches macroeconomic indicators for Spain, Eurozone and the USA
using the free FRED REST API. Requires FRED_API_KEY environment variable.

API docs: https://fred.stlouisfed.org/docs/api/fred/
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# ── Series catalogue ─────────────────────────────────────────────────────────
# Each entry: (series_id, region, indicator, name, unit)
SERIES_CATALOGUE: list[tuple[str, str, str, str, str]] = [
    # Spain
    ("ESPCPIALLMINMEI",        "ES", "inflation",      "Inflación España",              "%"),
    ("ESPCORECPIALLMINMEI",    "ES", "core_inflation",  "Inflación subyacente España",   "%"),
    ("LRHUTTTTESM156S",        "ES", "unemployment",   "Tasa de paro España",           "%"),
    ("CLVMNACSCAB1GQES",       "ES", "gdp",            "PIB España (vol. encad.)",      "M€"),
    # Eurozone
    ("CP0000EZ19M086NEST",     "EA", "inflation",      "Inflación Eurozona",            "%"),
    ("CPGRLE01EZM659N",        "EA", "core_inflation",  "Inflación subyacente Eurozona", "%"),
    ("LRHUTTTTEZM156S",        "EA", "unemployment",   "Tasa de paro Eurozona",         "%"),
    ("CLVMNACSCAB1GQEA19",     "EA", "gdp",            "PIB Eurozona (vol. encad.)",    "M€"),
    ("ECBDFR",                 "EA", "policy_rate",    "Tipo depósito BCE",             "%"),
    # USA
    ("CPIAUCSL",               "US", "inflation",      "Inflación EEUU (CPI)",          "%"),
    ("CPILFESL",               "US", "core_inflation",  "Core CPI EEUU",                "%"),
    ("UNRATE",                 "US", "unemployment",   "Tasa de paro EEUU",             "%"),
    ("GDPC1",                  "US", "gdp",            "PIB EEUU (real)",               "BUSD"),
    ("FEDFUNDS",               "US", "policy_rate",    "Fed Funds Rate",                "%"),
]

# YoY calculation is needed for index series (CPI is level, not rate for some)
_YOY_SERIES = {"CPIAUCSL", "CPILFESL", "ESPCPIALLMINMEI", "ESPCORECPIALLMINMEI",
               "CP0000EZ19M086NEST", "CPGRLE01EZM659N"}


def _format_period(date_str: str) -> str:
    """Convert FRED date string '2026-05-01' → 'mayo 2026'."""
    months_es = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{months_es[d.month]} {d.year}"
    except ValueError:
        return date_str


class FredProvider:
    def __init__(self, api_key: str | None = None) -> None:
        # None means "read from settings"; explicit "" means "no key"
        self._api_key = settings.FRED_API_KEY if api_key is None else api_key
        self._available = bool(self._api_key)

    @property
    def available(self) -> bool:
        return self._available

    def fetch_series(self, series_id: str) -> Optional[dict]:
        """Fetch the two most recent observations for a series.

        Returns a dict with keys: value, prev_value, observation_date, period
        or None on failure.
        """
        if not self._available:
            logger.warning("FRED_API_KEY not set — skipping %s", series_id)
            return None

        try:
            resp = requests.get(
                _BASE_URL,
                params={
                    "series_id": series_id,
                    "api_key": self._api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 13 if series_id in _YOY_SERIES else 2,
                    "observation_start": "2000-01-01",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            observations = [
                o for o in data.get("observations", [])
                if o.get("value") != "."
            ]
            if not observations:
                return None

            latest = observations[0]
            raw_value = float(latest["value"])

            if series_id in _YOY_SERIES and len(observations) >= 13:
                # Compute YoY %
                prev_year = observations[12]
                if prev_year.get("value") != ".":
                    prev_raw = float(prev_year["value"])
                    value = round((raw_value - prev_raw) / prev_raw * 100, 2)
                    prev_value = None
                    if len(observations) >= 14:
                        pp = observations[13]
                        if pp.get("value") != ".":
                            prev_raw2 = float(pp["value"])
                            prev_value = round(
                                (float(observations[1]["value"]) - prev_raw2) / prev_raw2 * 100, 2
                            )
                else:
                    value = raw_value
                    prev_value = None
            else:
                value = raw_value
                prev_value = float(observations[1]["value"]) if len(observations) >= 2 and observations[1].get("value") != "." else None

            return {
                "value": value,
                "prev_value": prev_value,
                "observation_date": latest["date"],
                "period": _format_period(latest["date"]),
            }

        except Exception as exc:
            logger.error("FRED fetch failed for %s: %s", series_id, exc)
            return None

    def fetch_all(self) -> list[dict]:
        """Fetch all configured series. Returns list of indicator dicts."""
        results = []
        for series_id, region, indicator, name, unit in SERIES_CATALOGUE:
            obs = self.fetch_series(series_id)
            if obs is None:
                continue
            results.append({
                "series_id": series_id,
                "region": region,
                "indicator": indicator,
                "name": name,
                "unit": unit,
                "source": "FRED",
                **obs,
            })
        return results
