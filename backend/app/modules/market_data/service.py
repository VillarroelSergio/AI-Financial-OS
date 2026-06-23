import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf

from app.modules.market_data.schemas import QuoteOut


@dataclass
class AssetConfig:
    symbol: str
    name: str
    category: str
    currency: str


ASSET_CATALOG: list[AssetConfig] = [
    # Europa
    AssetConfig("^IBEX", "IBEX 35", "indices_eu", "EUR"),
    AssetConfig("^STOXX50E", "Euro Stoxx 50", "indices_eu", "EUR"),
    AssetConfig("^STOXX", "STOXX Europe 600", "indices_eu", "EUR"),
    AssetConfig("^GDAXI", "DAX", "indices_eu", "EUR"),
    AssetConfig("^FCHI", "CAC 40", "indices_eu", "EUR"),
    AssetConfig("^FTSE", "FTSE 100", "indices_eu", "GBP"),
    # EEUU
    AssetConfig("^GSPC", "S&P 500", "indices_us", "USD"),
    AssetConfig("^NDX", "Nasdaq 100", "indices_us", "USD"),
    AssetConfig("^DJI", "Dow Jones", "indices_us", "USD"),
    AssetConfig("^RUT", "Russell 2000", "indices_us", "USD"),
    # Asia
    AssetConfig("^N225", "Nikkei 225", "indices_asia", "JPY"),
    AssetConfig("^HSI", "Hang Seng", "indices_asia", "HKD"),
    AssetConfig("000001.SS", "Shanghai Composite", "indices_asia", "CNY"),
    AssetConfig("^NSEI", "Nifty 50", "indices_asia", "INR"),
    # Cripto
    AssetConfig("BTC-USD", "Bitcoin", "crypto", "USD"),
    AssetConfig("ETH-USD", "Ethereum", "crypto", "USD"),
    AssetConfig("BNB-USD", "BNB", "crypto", "USD"),
    AssetConfig("SOL-USD", "Solana", "crypto", "USD"),
    # Divisas
    AssetConfig("EURUSD=X", "EUR/USD", "fx", "USD"),
    AssetConfig("EURGBP=X", "EUR/GBP", "fx", "GBP"),
    AssetConfig("EURJPY=X", "EUR/JPY", "fx", "JPY"),
    AssetConfig("GBPUSD=X", "GBP/USD", "fx", "USD"),
    AssetConfig("JPY=X", "USD/JPY", "fx", "JPY"),
    AssetConfig("CHF=X", "USD/CHF", "fx", "CHF"),
    # Bonos 10Y (tickers pueden fallar — precio null es aceptable, ver TD-07)
    AssetConfig("^TNX", "Treasury EEUU 10Y", "bonds", "USD"),
    AssetConfig("^TMBMKDE-10Y", "Bund Alemania 10Y", "bonds", "EUR"),
    AssetConfig("^TMBMKES-10Y", "Bono España 10Y", "bonds", "EUR"),
    AssetConfig("^TMBMKGB-10Y", "Gilt UK 10Y", "bonds", "GBP"),
    AssetConfig("^TMBMKIT-10Y", "BTP Italia 10Y", "bonds", "EUR"),
    # Materias primas
    AssetConfig("GC=F", "Oro", "commodities", "USD"),
    AssetConfig("SI=F", "Plata", "commodities", "USD"),
    AssetConfig("BZ=F", "Petróleo Brent", "commodities", "USD"),
    AssetConfig("CL=F", "Petróleo WTI", "commodities", "USD"),
    AssetConfig("NG=F", "Gas Natural", "commodities", "USD"),
    AssetConfig("HG=F", "Cobre", "commodities", "USD"),
    # Volatilidad
    AssetConfig("^VIX", "VIX", "volatility", "USD"),
]

_cache: dict = {"quotes": [], "updated_at": None, "refreshing": False}
CACHE_TTL = 15.0


def _fetch_quote(asset: AssetConfig) -> QuoteOut:
    try:
        ticker = yf.Ticker(asset.symbol)
        fast = ticker.fast_info
        price = fast.last_price
        prev_close = fast.previous_close
        change_pct = (
            float((price - prev_close) / prev_close * 100)
            if price is not None and prev_close and prev_close != 0
            else None
        )
        try:
            hist = ticker.history(period="1d", interval="5m")
            sparkline = [float(v) for v in hist["Close"].dropna().tolist()] if not hist.empty else []
        except Exception:
            sparkline = []
        try:
            market_state = getattr(fast, "market_state", None)
            market_open = market_state == "REGULAR" if market_state else True
        except Exception:
            market_open = True
        return QuoteOut(
            symbol=asset.symbol,
            name=asset.name,
            category=asset.category,
            price=float(price) if price is not None else None,
            change_pct=change_pct,
            currency=asset.currency,
            sparkline=sparkline,
            last_updated=datetime.now(timezone.utc).isoformat(),
            market_open=market_open,
        )
    except Exception:
        return QuoteOut(
            symbol=asset.symbol,
            name=asset.name,
            category=asset.category,
            price=None,
            change_pct=None,
            currency=asset.currency,
            sparkline=[],
            last_updated=datetime.now(timezone.utc).isoformat(),
            market_open=False,
        )


def _refresh_cache() -> None:
    if _cache["refreshing"]:
        return
    _cache["refreshing"] = True
    try:
        quotes = [_fetch_quote(asset) for asset in ASSET_CATALOG]
        _cache["quotes"] = [q.model_dump() for q in quotes]
        _cache["updated_at"] = time.time()
    finally:
        _cache["refreshing"] = False


def get_quotes(category: str | None = None) -> list[dict]:
    now = time.time()
    is_stale = _cache["updated_at"] is None or (now - _cache["updated_at"]) > CACHE_TTL

    if is_stale and not _cache["refreshing"]:
        if _cache["quotes"]:
            threading.Thread(target=_refresh_cache, daemon=True).start()
        else:
            _refresh_cache()

    quotes = _cache["quotes"]
    if category:
        quotes = [q for q in quotes if q["category"] == category]
    return quotes
