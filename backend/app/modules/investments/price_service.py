from datetime import datetime, timezone
from decimal import Decimal

import yfinance as yf

from app.models.investment import Holding, InvestmentAsset


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

            asset_type = asset.asset_type or "unknown"
            if asset_type in {"cash", "savings_account"}:
                result.skipped.append({
                    "holding_id": h.id,
                    "name": asset.name,
                    "asset_type": asset_type,
                    "reason": "cash_uses_account_balance",
                })
                continue

            if asset.price_source == "manual" or not asset.ticker:
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
            price = cls.fetch_ticker_price(asset.ticker)
            if price is None:
                message = f"{asset.ticker}: provider_unavailable"
                result.failed.append(asset.ticker)
                result.errors.append(message)
                continue

            h.current_price = price
            h.current_price_currency = asset.currency
            h.current_price_updated_at = datetime.now(timezone.utc)

            if asset.currency == "USD":
                h.market_value = (h.quantity * price / eur_usd).quantize(Decimal("0.01"))
            else:
                h.market_value = (h.quantity * price).quantize(Decimal("0.01"))

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
