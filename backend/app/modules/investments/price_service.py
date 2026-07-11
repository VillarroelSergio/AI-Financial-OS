import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal

import yfinance as yf

from app.models.investment import Holding, HoldingValueHistory, InvestmentAsset
from app.modules.investments.asset_resolution import resolve_asset

logger = logging.getLogger("investments.prices")


class PriceRefreshResult:
    def __init__(self) -> None:
        self.updated: int = 0
        self.failed: list[str] = []
        self.needs_manual_nav: list[str] = []
        self.updated_items: list[dict] = []
        self.manual_required: list[dict] = []
        self.skipped: list[dict] = []
        self.errors: list[str] = []


class PriceService:
    @staticmethod
    def fetch_ticker_price(ticker: str) -> Decimal | None:
        try:
            price = yf.Ticker(ticker).fast_info.last_price
            return Decimal(str(price)) if price is not None else None
        except Exception as exc:  # noqa: BLE001 — el llamador decide; aquí solo se registra
            logger.warning("fetch de %s falló: %s", ticker, exc)
            return None

    @classmethod
    def get_eur_rate(cls, currency: str, cache: dict[str, Decimal | None]) -> Decimal | None:
        """Unidades de `currency` por 1 EUR; None si el tipo no está disponible."""
        currency = (currency or "EUR").upper()
        if currency == "EUR":
            return Decimal("1.0")
        if currency not in cache:
            cache[currency] = cls.fetch_ticker_price(f"EUR{currency}=X")
        return cache[currency]

    @classmethod
    def refresh_prices(cls, db, holding_ids: list[str] | None = None) -> PriceRefreshResult:
        result = PriceRefreshResult()
        q = db.query(Holding)
        if holding_ids:
            q = q.filter(Holding.id.in_(holding_ids))
        holdings = q.all()

        fx_cache: dict[str, Decimal | None] = {}

        assets_by_holding: dict[str, InvestmentAsset] = {}
        for h in holdings:
            asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == h.asset_id).first()
            if asset:
                assets_by_holding[h.id] = asset

        # ponytail: hasta 8 hilos solo para el fetch HTTP; la BD se escribe en serie después.
        tickers = list({
            a.ticker
            for a in assets_by_holding.values()
            if a.ticker and (a.asset_type or "unknown") not in {"cash", "savings_account"}
        })
        prices: dict[str, Decimal | None] = {}
        if tickers:
            with ThreadPoolExecutor(max_workers=8) as pool:
                for ticker, price in zip(tickers, pool.map(cls.fetch_ticker_price, tickers)):
                    prices[ticker] = price

        for h in holdings:
            asset = assets_by_holding.get(h.id)
            if not asset:
                continue

            asset_type = asset.asset_type or "unknown"
            if asset_type in {"cash", "savings_account"}:
                result.skipped.append({
                    "holding_id": h.id,
                    "name": asset.name,
                    "asset_type": asset_type,
                    "reason": "cash_uses_account_balance",
                })
                continue

            # Se intenta el fetch siempre que haya ticker: price_source="manual" es el
            # default de los activos creados a mano y no debe vetar el precio automático.
            if not asset.ticker:
                item = {
                    "holding_id": h.id,
                    "name": asset.name,
                    "symbol": asset.ticker,
                    "asset_type": asset_type,
                    "reason": "missing_price_provider",
                }
                result.manual_required.append(item)
                result.needs_manual_nav.append(h.id)
                continue

            old_price = h.current_price
            price = prices.get(asset.ticker)
            if price is None:
                # Ticker pelado (p. ej. "IBE"): reintentar con el resuelto por nombre
                # (IBE.MC) y persistir la corrección para futuros refrescos.
                resolution = resolve_asset(asset.name)
                candidate = resolution.selected
                if candidate and candidate.yfinance_symbol != asset.ticker:
                    price = cls.fetch_ticker_price(candidate.yfinance_symbol)
                    if price is not None:
                        asset.ticker = candidate.ticker
                        asset.currency = candidate.currency
                        asset.price_source = "yfinance"
            if price is None:
                message = f"{asset.ticker}: provider_unavailable"
                result.failed.append(asset.ticker)
                result.errors.append(message)
                result.manual_required.append({
                    "holding_id": h.id,
                    "name": asset.name,
                    "symbol": asset.ticker,
                    "asset_type": asset_type,
                    "reason": "provider_unavailable",
                })
                result.needs_manual_nav.append(h.id)
                continue

            rate = cls.get_eur_rate(asset.currency, fx_cache)
            if rate is None:
                # Sin tipo de cambio no hay valor fiable: mejor pedir intervención
                # que valorar con un tipo inventado. Se marca antes de tocar el holding.
                result.manual_required.append({
                    "holding_id": h.id,
                    "name": asset.name,
                    "symbol": asset.ticker,
                    "asset_type": asset_type,
                    "reason": "fx_unavailable",
                })
                result.needs_manual_nav.append(h.id)
                continue

            if asset.price_source == "manual":
                asset.price_source = "yfinance"
            h.current_price = price
            h.current_price_currency = asset.currency
            h.current_price_updated_at = datetime.now(timezone.utc)
            h.market_value = (h.quantity * price / rate).quantize(Decimal("0.01"))
            db.add(HoldingValueHistory(holding_id=h.id, price=price, currency=asset.currency, source="yfinance"))

            result.updated += 1
            result.updated_items.append({
                "holding_id": h.id,
                "name": asset.name,
                "symbol": asset.ticker,
                "old_price": old_price,
                "new_price": price,
                "currency": asset.currency,
                "source": asset.price_source or "provider",
            })

        result.needs_manual_nav = list(dict.fromkeys(result.needs_manual_nav))
        db.commit()
        return result
