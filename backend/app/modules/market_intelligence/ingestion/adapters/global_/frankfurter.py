"""Frankfurter adapter - free ECB-backed FX rates."""
import time
from datetime import date, datetime, timedelta, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    CurrencyRate,
    HistoricalPrice,
)

_BASE_URL = "https://api.frankfurter.app"
_PAIRS = ("USD", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY")
_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}


def fetch_forex_history(catalog_id: str, years: int | None = None) -> list[HistoricalPrice]:
    """MKT-6: serie diaria de un par FX desde Frankfurter (tipos de referencia del BCE).
    El par sale del propio catalog_id (`eur_usd` → EUR→USD). Solo días hábiles, sin OHLC."""
    base, quote = catalog_id.upper().split("_")
    start = (date.today() - timedelta(days=365 * (years or 5))).isoformat()
    end = date.today().isoformat()
    url = f"{_BASE_URL}/{start}..{end}?from={base}&to={quote}"
    r = requests.get(url, headers=_HEADERS, timeout=20)
    r.raise_for_status()
    rates = r.json().get("rates") or {}
    now = datetime.now(timezone.utc)
    out: list[HistoricalPrice] = []
    for dstr in sorted(rates):
        val = rates[dstr].get(quote)
        if val is None:
            continue
        rec = HistoricalPrice(
            provider="Frankfurter", source=url, retrieved_at=now,
            country="GLOBAL", region="Global", symbol=catalog_id.upper(),
            date=date.fromisoformat(dstr),
            open=0.0, high=0.0, low=0.0, close=float(val), volume=0.0,
        )
        rec.currency = quote  # HistoricalPrice no tiene el campo; persist lee getattr
        out.append(rec)
    if not out:
        raise ValueError("Frankfurter returned no rates")
    return out


class FrankfurterAdapter(BaseAdapter):
    name = "Frankfurter"
    category = "markets"
    region = "Global"
    requires_api_key = False
    capabilities = ("currency", "forex", "historical")
    priority = "primary"

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(
            id="frankfurter",
            base_url=_BASE_URL,
            method="api",
            license="open",
            declared_update_frequency="daily",
            declared_historical_depth_years=25,
            notes="Free exchange-rate API based on ECB reference rates.",
        )
        t0 = time.perf_counter()
        url = f"{_BASE_URL}/latest"
        params = {"from": "EUR", "to": ",".join(_PAIRS)}
        try:
            response = requests.get(url, params=params, headers=_HEADERS, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            obs_date = datetime.fromisoformat(data["date"]).date()
            records = [
                CurrencyRate(
                    provider=self.name,
                    source=response.url,
                    retrieved_at=datetime.now(timezone.utc),
                    country="GLOBAL",
                    region=self.region,
                    confidence_score=0.95,
                    base_currency=data.get("base", "EUR"),
                    quote_currency=quote,
                    rate=float(rate),
                    date=obs_date,
                    frequency="daily",
                )
                for quote, rate in (data.get("rates") or {}).items()
            ]
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "Frankfurter response contained no rates",
                latency_ms=latency_ms,
                raw_sample={"date": data.get("date"), "rates": list((data.get("rates") or {}).keys())},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None,
                metadata=metadata,
            )


Adapter = FrankfurterAdapter
