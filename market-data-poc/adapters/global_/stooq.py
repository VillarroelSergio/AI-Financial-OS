"""Stooq adapter - IBEX35 and S&P500 historical prices from CSV."""
import csv
import io
import time
import requests
from datetime import datetime, timezone, date

from models.base import AdapterResult
from models.market import HistoricalPrice
from adapters.base import BaseAdapter

_SOURCES = [
    {
        "symbol": "^IBEX",
        "url": "https://stooq.com/q/d/l/?s=%5Eibex&i=d",
        "fallback_url": "https://query1.finance.yahoo.com/v8/finance/chart/%5EIBEX?range=5d&interval=1d",
    },
    {
        "symbol": "^SPX",
        "url": "https://stooq.com/q/d/l/?s=%5Espx&i=d",
        "fallback_url": "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=5d&interval=1d",
    },
]

_HEADERS = {"User-Agent": "MarketDataPOC/0.1"}
_FALLBACK_HEADERS = {"User-Agent": "Mozilla/5.0"}


class StooqAdapter(BaseAdapter):
    name = "Stooq"
    category = "markets"
    region = "Global"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(
            base_url="https://stooq.com",
            method="csv",
            license="Stooq Public",
            notes="Stooq CSV with Yahoo Chart fallback when CSV is blocked",
        )
        t0 = time.time()
        records: list[HistoricalPrice] = []
        errors: list[str] = []
        fallback_used: list[str] = []
        retrieved_at = datetime.now(timezone.utc)

        for source in _SOURCES:
            try:
                source_records = _fetch_stooq_csv(source, retrieved_at)
                records.extend(source_records)
            except Exception as exc:
                errors.append(f"{source['symbol']}: {exc}")
                fallback_records = _fetch_yahoo_fallback(source, retrieved_at)
                if fallback_records:
                    records.extend(fallback_records)
                    fallback_used.append(source["symbol"])

        latency_ms = (time.time() - t0) * 1000

        if not records:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error="; ".join(errors) if errors else "No data",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error="; ".join(errors) if errors else None,
            latency_ms=latency_ms,
            raw_sample={
                "symbols": [s["symbol"] for s in _SOURCES],
                "rows_fetched": len(records),
                "fallback_used": fallback_used,
            },
            metadata=metadata,
        )


def _fetch_stooq_csv(source: dict, retrieved_at: datetime) -> list[HistoricalPrice]:
    r = requests.get(source["url"], headers=_HEADERS, timeout=10)
    r.raise_for_status()
    text = r.text
    if "Date," not in text[:100]:
        raise ValueError("Stooq response is not CSV")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    records: list[HistoricalPrice] = []
    for row in rows[-5:]:
        records.append(
            HistoricalPrice(
                provider="Stooq",
                source=source["url"],
                retrieved_at=retrieved_at,
                country="GLOBAL",
                region="Global",
                confidence_score=1.0,
                symbol=source["symbol"],
                date=date.fromisoformat(row["Date"]),
                open=float(row.get("Open") or 0),
                high=float(row.get("High") or 0),
                low=float(row.get("Low") or 0),
                close=float(row.get("Close") or 0),
                volume=float(row.get("Volume") or 0),
            )
        )
    return records


def _fetch_yahoo_fallback(source: dict, retrieved_at: datetime) -> list[HistoricalPrice]:
    r = requests.get(source["fallback_url"], headers=_FALLBACK_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    result = data.get("chart", {}).get("result") or []
    if not result:
        return []

    item = result[0]
    timestamps = item.get("timestamp") or []
    quote = (item.get("indicators", {}).get("quote") or [{}])[0]
    records: list[HistoricalPrice] = []
    start = max(0, len(timestamps) - 5)

    for offset in range(start, len(timestamps)):
        try:
            close = quote.get("close", [])[offset]
            if close is None:
                continue
            records.append(
                HistoricalPrice(
                    provider="Stooq",
                    source=source["fallback_url"],
                    retrieved_at=retrieved_at,
                    country="GLOBAL",
                    region="Global",
                    confidence_score=0.75,
                    symbol=source["symbol"],
                    date=datetime.fromtimestamp(timestamps[offset], tz=timezone.utc).date(),
                    open=float((quote.get("open", [None])[offset]) or 0),
                    high=float((quote.get("high", [None])[offset]) or 0),
                    low=float((quote.get("low", [None])[offset]) or 0),
                    close=float(close),
                    volume=float((quote.get("volume", [0])[offset]) or 0),
                )
            )
        except Exception:
            continue
    return records
