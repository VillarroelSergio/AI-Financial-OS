"""Valoración actual de cuentas y posiciones sin doble contabilización."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.investment import Holding, InvestmentAsset


def to_eur(
    amount: Decimal,
    currency: str | None,
    rates: dict[str, float | None],
) -> Decimal:
    currency = (currency or "EUR").upper()
    if currency == "EUR" or not amount:
        return amount
    if currency not in rates:
        from app.modules.investments.price_coverage_audit import fetch_fx_rate

        rates[currency] = fetch_fx_rate(currency)[0]
    rate = rates[currency]
    if not rate:
        return amount
    return (amount / Decimal(str(rate))).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class CurrentValuation:
    accounts: list[Account]
    cash_by_account: dict[str, Decimal]
    portfolio_by_account: dict[str, Decimal]
    position_count_by_account: dict[str, int]
    total_by_account: dict[str, Decimal]
    by_type: dict[str, Decimal]
    liquidity: Decimal
    investments: Decimal
    net_worth: Decimal


def build_current_valuation(db: Session) -> CurrentValuation:
    accounts = db.query(Account).filter(Account.is_active == True).all()  # noqa: E712
    account_ids = {account.id for account in accounts}
    rates: dict[str, float | None] = {}
    cash_by_account = {
        account.id: to_eur(account.current_balance or Decimal("0"), account.currency, rates)
        for account in accounts
    }
    portfolio_by_account = {account.id: Decimal("0") for account in accounts}
    position_count_by_account = {account.id: 0 for account in accounts}

    holdings = (
        db.query(Holding).filter(Holding.account_id.in_(account_ids)).all()
        if account_ids
        else []
    )
    asset_ids = {holding.asset_id for holding in holdings}
    assets = {
        asset.id: asset
        for asset in db.query(InvestmentAsset).filter(InvestmentAsset.id.in_(asset_ids)).all()
    } if asset_ids else {}
    accounts_by_id = {account.id: account for account in accounts}
    for holding in holdings:
        position_count_by_account[holding.account_id] += 1
        asset = assets.get(holding.asset_id)
        if asset and asset.asset_type == "savings_account":
            # La cuenta remunerada y su holding representan el mismo dinero. El holding
            # es la fuente actual usada por el motor de intereses; sustituye al saldo de
            # la cuenta para incluir datos antiguos con current_balance=0 sin duplicarlos.
            if holding.market_value is not None:
                account = accounts_by_id[holding.account_id]
                cash_by_account[holding.account_id] = to_eur(
                    holding.market_value,
                    asset.currency or account.currency,
                    rates,
                )
            continue
        if holding.market_value is not None:
            portfolio_by_account[holding.account_id] += holding.market_value

    total_by_account = {
        account.id: cash_by_account[account.id] + portfolio_by_account[account.id]
        for account in accounts
    }
    by_type: dict[str, Decimal] = {}
    for account in accounts:
        by_type[account.type] = by_type.get(account.type, Decimal("0")) + total_by_account[account.id]

    liquidity = sum(
        (
            cash_by_account[account.id]
            for account in accounts
            if account.type in ("cash", "bank", "savings")
        ),
        Decimal("0"),
    )
    portfolio_value = sum(portfolio_by_account.values(), Decimal("0"))
    investment_cash = sum(
        (
            cash_by_account[account.id]
            for account in accounts
            if account.type in ("broker", "investment")
        ),
        Decimal("0"),
    )
    remunerated_savings = sum(
        (
            cash_by_account[account.id]
            for account in accounts
            if account.type == "savings"
        ),
        Decimal("0"),
    )
    investments = remunerated_savings + investment_cash + portfolio_value
    net_worth = sum(cash_by_account.values(), Decimal("0")) + portfolio_value

    return CurrentValuation(
        accounts=accounts,
        cash_by_account=cash_by_account,
        portfolio_by_account=portfolio_by_account,
        position_count_by_account=position_count_by_account,
        total_by_account=total_by_account,
        by_type=by_type,
        liquidity=liquidity,
        investments=investments,
        net_worth=net_worth,
    )
