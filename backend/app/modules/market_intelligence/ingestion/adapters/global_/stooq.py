"""Stooq adapter - daily close quotes for major indices from CSV."""
import csv
import io
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    HistoricalPrice,
    MarketQuote,
)

_SOURCES = {
    "sp500": {"symbol": "^SPX", "name": "S&P 500", "currency": "USD", "country": "US", "stooq": "%5Espx", "yahoo": "%5EGSPC"},
    "nasdaq": {"symbol": "^NDQ", "name": "Nasdaq Composite", "currency": "USD", "country": "US", "stooq": "%5Endq", "yahoo": "%5EIXIC"},
    "dow_jones": {"symbol": "^DJI", "name": "Dow Jones Industrial", "currency": "USD", "country": "US", "stooq": "%5Edji", "yahoo": "%5EDJI"},
    "russell_2000": {"symbol": "^RUT", "name": "Russell 2000", "currency": "USD", "country": "US", "stooq": "%5Erut", "yahoo": "%5ERUT"},
    "ibex35": {"symbol": "^IBEX", "name": "IBEX 35", "currency": "EUR", "country": "ES", "stooq": "%5Eibex", "yahoo": "%5EIBEX"},
    "eurostoxx50": {"symbol": "^STOXX50E", "name": "EuroStoxx 50", "currency": "EUR", "country": "EA", "stooq": "%5Estoxx50", "yahoo": "%5ESTOXX50E"},
    "dax": {"symbol": "^DAX", "name": "DAX", "currency": "EUR", "country": "DE", "stooq": "%5Edax", "yahoo": "%5EGDAXI"},
    "cac40": {"symbol": "^CAC", "name": "CAC 40", "currency": "EUR", "country": "FR", "stooq": "%5Ecac", "yahoo": "%5EFCHI"},
    "ftse100": {"symbol": "^FTSE", "name": "FTSE 100", "currency": "GBP", "country": "GB", "stooq": "%5Eukx", "yahoo": "%5EFTSE"},
    "nikkei225": {"symbol": "^NKX", "name": "Nikkei 225", "currency": "JPY", "country": "JP", "stooq": "%5Enkx", "yahoo": "%5EN225"},
    # Futuros de commodities — mismos endpoints CSV públicos de stooq, sin API key.
    "gold": {"symbol": "GC.F", "name": "Oro", "currency": "USD", "country": "GLOBAL", "stooq": "gc.f", "yahoo": "GC%3DF", "asset_type": "commodity"},
    "silver": {"symbol": "SI.F", "name": "Plata", "currency": "USD", "country": "GLOBAL", "stooq": "si.f", "yahoo": "SI%3DF", "asset_type": "commodity"},
    "brent": {"symbol": "CB.F", "name": "Brent Crude Oil", "currency": "USD", "country": "GLOBAL", "stooq": "cb.f", "yahoo": "BZ%3DF", "asset_type": "commodity"},
    "wti": {"symbol": "CL.F", "name": "WTI Crude Oil", "currency": "USD", "country": "US", "stooq": "cl.f", "yahoo": "CL%3DF", "asset_type": "commodity"},
    "natural_gas": {"symbol": "NG.F", "name": "Gas Natural", "currency": "USD", "country": "GLOBAL", "stooq": "ng.f", "yahoo": "NG%3DF", "asset_type": "commodity"},
    "copper": {"symbol": "HG.F", "name": "Cobre", "currency": "USD", "country": "GLOBAL", "stooq": "hg.f", "yahoo": "HG%3DF", "asset_type": "commodity"},
}

_HEADERS = {"User-Agent": "MarketDataPOC/0.1"}
_FALLBACK_HEADERS = {"User-Agent": "Mozilla/5.0"}


class StooqAdapter(BaseAdapter):
    name = "Stooq"
    category = "markets"
    region = "Global"
    requires_api_key = False
    supported_indicators = {key: value for key, value in _SOURCES.items()}

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = self._make_metadata(
            base_url="https://stooq.com",
            method="csv",
            license="Stooq Public",
            notes="Stooq CSV with Yahoo Chart fallback when CSV is blocked",
        )
        t0 = time.time()
        records: list[MarketQuote] = []
        errors: list[str] = []
        fallback_used: list[str] = []
        retrieved_at = datetime.now(timezone.utc)

        sources = {indicator_id: _SOURCES[indicator_id]} if indicator_id in _SOURCES else _SOURCES
        for catalog_id, source in sources.items():
            try:
                records.append(_fetch_stooq_csv(catalog_id, source, retrieved_at))
            except Exception as exc:
                errors.append(f"{source['symbol']}: {exc}")
                try:
                    fallback_record = _fetch_yahoo_fallback(catalog_id, source, retrieved_at)
                except Exception as fallback_exc:
                    errors.append(f"{source['symbol']} (yahoo): {fallback_exc}")
                    fallback_record = None
                if fallback_record:
                    records.append(fallback_record)
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
                "symbols": [s["symbol"] for s in sources.values()],
                "rows_fetched": len(records),
                "fallback_used": fallback_used,
            },
            metadata=metadata,
        )


def fetch_stooq_history(catalog_id: str, years: int | None = None) -> list[HistoricalPrice]:
    """MKT-6: serie EOD completa para backfill manual bajo demanda, no en arranque.

    Stooq bloquea su CSV diario con un reto JS, así que tomamos el histórico de la
    Yahoo Chart API (el mismo fallback que `fetch` ya usa para el precio en vivo).

    ponytail: solo índices/commodities. Cripto (CoinGecko) y forex (BCE SDMX)
    quedan fuera hasta que sus adapters expongan histórico — otro lift, otro provider.
    """
    source = _SOURCES[catalog_id]
    yrange = f"{years}y" if years else "max"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{source['yahoo']}?range={yrange}&interval=1d"
    r = requests.get(url, headers=_FALLBACK_HEADERS, timeout=20)
    r.raise_for_status()
    result = (r.json().get("chart", {}).get("result") or [None])[0]
    if not result:
        raise ValueError("Yahoo Chart returned no result")
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    currency = result.get("meta", {}).get("currency") or source["currency"]
    closes, opens = quote.get("close", []), quote.get("open", [])
    highs, lows, volumes = quote.get("high", []), quote.get("low", []), quote.get("volume", [])
    now = datetime.now(timezone.utc)
    out: list[HistoricalPrice] = []
    for i, ts in enumerate(timestamps):
        c = closes[i] if i < len(closes) else None
        if c is None:
            continue
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        rec = HistoricalPrice(
            provider="Yahoo", source=url, retrieved_at=now,
            country=source["country"], region="Global",
            symbol=source["symbol"], date=d,
            open=float(opens[i] or 0) if i < len(opens) and opens[i] is not None else 0.0,
            high=float(highs[i] or 0) if i < len(highs) and highs[i] is not None else 0.0,
            low=float(lows[i] or 0) if i < len(lows) and lows[i] is not None else 0.0,
            close=float(c),
            volume=float(volumes[i] or 0) if i < len(volumes) and volumes[i] is not None else 0.0,
        )
        rec.currency = currency  # HistoricalPrice no tiene el campo; persist lee getattr
        out.append(rec)
    if not out:
        raise ValueError("Yahoo Chart has no usable rows")
    return out


def _fetch_stooq_csv(catalog_id: str, source: dict, retrieved_at: datetime) -> MarketQuote:
    url = f"https://stooq.com/q/d/l/?s={source['stooq']}&i=d"
    r = requests.get(url, headers=_HEADERS, timeout=10)
    r.raise_for_status()
    text = r.text
    if "Date," not in text[:100]:
        raise ValueError("Stooq response is not CSV")

    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader if row.get("Close")]
    if not rows:
        raise ValueError("Stooq CSV has no close rows")
    last = rows[-1]
    prev = rows[-2] if len(rows) > 1 else last
    close = float(last.get("Close") or 0)
    prev_close = float(prev.get("Close") or close)
    change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0.0
    return _quote(catalog_id, source, url, retrieved_at, close, change_pct, 1.0)


def _fetch_yahoo_fallback(catalog_id: str, source: dict, retrieved_at: datetime) -> MarketQuote | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{source['yahoo']}?range=5d&interval=1d"
    r = requests.get(url, headers=_FALLBACK_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    result = data.get("chart", {}).get("result") or []
    if not result:
        return []

    item = result[0]
    item.get("timestamp") or []
    quote = (item.get("indicators", {}).get("quote") or [{}])[0]
    closes = [value for value in quote.get("close", []) if value is not None]
    if not closes:
        return None
    close = float(closes[-1])
    prev_close = float(closes[-2]) if len(closes) > 1 else close
    change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0.0
    return _quote(catalog_id, source, url, retrieved_at, close, change_pct, 0.75)


def _quote(
    catalog_id: str,
    source: dict,
    url: str,
    retrieved_at: datetime,
    price: float,
    change_pct: float,
    confidence: float,
) -> MarketQuote:
    return MarketQuote(
        provider="Stooq",
        source=url,
        retrieved_at=retrieved_at,
        country=source["country"],
        region="Global",
        confidence_score=confidence,
        symbol=source["symbol"],
        name=source["name"],
        asset_type=source.get("asset_type", "index"),
        price=price,
        change_pct=change_pct,
        currency=source["currency"],
        market_status="closed",
    )
