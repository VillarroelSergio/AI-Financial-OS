from datetime import datetime, timezone
from decimal import Decimal

import yfinance as yf

from app.models.investment import Holding, InvestmentAsset


class PriceRefreshResult:
    def __init__(self) -> None:
        self.updated: int = 0
        self.failed: list[str] = []
        self.needs_manual_nav: list[str] = []


class PriceService:
    @staticmethod
    def fetch_ticker_price(ticker: str) -> Decimal | None:
        try:
            price = yf.Ticker(ticker).fast_info.last_price
            return Decimal(str(price)) if price is not None else None
        except Exception:
            return None

    @classmethod
    def get_eur_usd_rate(cls) -> Decimal:
        rate = cls.fetch_ticker_price("EURUSD=X")
        return rate if rate is not None else Decimal("1.0")

    @classmethod
    def refresh_prices(cls, db, holding_ids: list[str] | None = None) -> PriceRefreshResult:
        result = PriceRefreshResult()
        q = db.query(Holding)
        if holding_ids:
            q = q.filter(Holding.id.in_(holding_ids))
        holdings = q.all()

        eur_usd = cls.get_eur_usd_rate()

        for h in holdings:
            asset: InvestmentAsset | None = (
                db.query(InvestmentAsset)
                .filter(InvestmentAsset.id == h.asset_id)
                .first()
            )
            if not asset:
                continue

            if asset.price_source == "manual" or not asset.ticker:
                result.needs_manual_nav.append(h.asset_id)
                continue

            price = cls.fetch_ticker_price(asset.ticker)
            if price is None:
                result.failed.append(asset.ticker)
                continue

            h.current_price = price
            h.current_price_currency = asset.currency
            h.current_price_updated_at = datetime.now(timezone.utc)

            if asset.currency == "USD":
                h.market_value = (h.quantity * price / eur_usd).quantize(Decimal("0.01"))
            else:
                h.market_value = (h.quantity * price).quantize(Decimal("0.01"))

            result.updated += 1

        result.needs_manual_nav = list(dict.fromkeys(result.needs_manual_nav))
        db.commit()
        return result
