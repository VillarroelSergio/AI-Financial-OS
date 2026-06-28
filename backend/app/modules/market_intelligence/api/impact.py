# backend/app/modules/market_intelligence/api/impact.py
"""Cómputo de los 11 comparativos de impacto personal — 100% determinista, sin LLM."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.duckdb import get_duckdb
from app.models.account import Account
from app.models.category import Category
from app.models.investment import Holding
from app.models.transaction import Transaction
from app.modules.market_intelligence.api.schemas import ImpactComparative, PersonalImpactOut

# ──────────────────────────────────────────────────────────────
# Signal helper
# ──────────────────────────────────────────────────────────────

def compute_signal(personal: float | None, threshold: float, higher_is_better: bool) -> str:
    if personal is None:
        return "neutral"
    delta = personal - threshold
    dead_band = max(abs(threshold) * 0.05, 0.01)
    if abs(delta) < dead_band:
        return "neutral"
    return "positive" if (delta > 0) == higher_is_better else "negative"


# ──────────────────────────────────────────────────────────────
# Personal data queries (SQLite)
# ──────────────────────────────────────────────────────────────

def _get_personal_data(db: Session) -> dict:
    cutoff = (date.today() - timedelta(days=90)).isoformat()

    total_balance = float(
        db.query(func.sum(Account.current_balance))
        .filter(Account.is_active == True)  # noqa: E712
        .scalar() or 0
    )

    raw_income = float(
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.amount > 0, Transaction.date >= cutoff)
        .scalar() or 0
    )
    raw_expense = abs(float(
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.amount < 0, Transaction.date >= cutoff)
        .scalar() or 0
    ))
    monthly_income = raw_income / 3
    monthly_expense = raw_expense / 3

    savings_rate: float | None = None
    if monthly_income > 0:
        savings_rate = (monthly_income - monthly_expense) / monthly_income * 100

    months_covered: float | None = None
    if monthly_expense > 0:
        months_covered = total_balance / monthly_expense

    # Portfolio average return % across all holdings with current_price
    holdings = db.query(Holding).filter(Holding.current_price.isnot(None)).all()
    portfolio_return: float | None = None
    if holdings:
        returns = [
            (float(h.current_price) - float(h.average_price)) / float(h.average_price) * 100
            for h in holdings
            if float(h.average_price) > 0
        ]
        portfolio_return = sum(returns) / len(returns) if returns else None

    # Total debt from loan/mortgage/credit accounts (negative balances stored as negative)
    total_debt = abs(float(
        db.query(func.sum(Account.current_balance))
        .filter(
            Account.type.in_(["loan", "mortgage", "credit"]),
            Account.is_active == True,  # noqa: E712
        )
        .scalar() or 0
    ))

    def _cat_monthly(keywords: list[str]) -> float:
        """Average monthly expense for transactions in categories matching any keyword."""
        keyword_filters = [func.lower(Category.name).contains(k.lower()) for k in keywords]
        txns = (
            db.query(func.sum(Transaction.amount))
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .filter(
                Transaction.amount < 0,
                Transaction.date >= cutoff,
                or_(*keyword_filters),
            )
            .scalar()
        )
        return abs(float(txns or 0)) / 3

    usd_monthly = abs(float(
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.amount < 0,
            Transaction.date >= cutoff,
            Transaction.currency == "USD",
        )
        .scalar() or 0
    )) / 3

    transport_monthly = _cat_monthly(["transporte", "gasolina"])
    food_home_monthly = _cat_monthly(["alimentaci"])

    return {
        "total_balance": total_balance,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "savings_rate": savings_rate,
        "months_covered": months_covered,
        "portfolio_return": portfolio_return,
        "total_debt": total_debt,
        "usd_monthly_expense": usd_monthly,
        "transport_monthly": transport_monthly,
        "food_home_monthly": food_home_monthly,
    }


# ──────────────────────────────────────────────────────────────
# MI data queries (DuckDB)
# ──────────────────────────────────────────────────────────────

def _get_mi_data() -> dict:
    from app.modules.market_intelligence.storage import repository as mi_repo

    mi_repo.ensure_baseline_market_data()
    duck = get_duckdb()

    def _scalar(table: str, val_col: str, cid: str, order_col: str) -> float | None:
        try:
            row = duck.execute(
                f"SELECT {val_col} FROM {table} WHERE catalog_item_id = ? "
                f"ORDER BY {order_col} DESC LIMIT 1",
                [cid],
            ).fetchone()
            return float(row[0]) if row and row[0] is not None else None
        except Exception:
            return None

    def _quote(cid: str) -> float | None:
        return _scalar("mi_market_quotes", "change_pct", cid, "observed_at")

    index_changes = [_quote(cid) for cid in ("sp500", "ibex35", "eurostoxx50") ]
    valid = [v for v in index_changes if v is not None]
    index_avg = sum(valid) / len(valid) if valid else None

    bono_spain = _scalar("mi_bond_yields", "yield_value", "spain_10y", "date")
    bund = _scalar("mi_bond_yields", "yield_value", "germany_10y", "date")
    spread = (bono_spain - bund) * 100 if bono_spain is not None and bund is not None else None

    return {
        "ipc_general": _scalar("mi_macro_observations", "value", "ipc_general", "retrieved_at"),
        "tipo_bce": _scalar("mi_macro_observations", "value", "tipo_bce", "retrieved_at"),
        "euribor_12m": _scalar("mi_macro_observations", "value", "euribor_12m", "retrieved_at"),
        "eur_usd": _scalar("mi_currency_rates", "rate", "eur_usd", "date"),
        "brent_crude": _scalar("mi_commodities", "price", "brent", "observed_at")
        or _scalar("mi_market_quotes", "price", "brent", "observed_at"),
        "bono_spain_10y": bono_spain,
        "bund_10y": bund,
        "risk_premium_bps": spread,
        "ipc_subyacente": _scalar("mi_macro_observations", "value", "ipc_subyacente", "retrieved_at"),
        "confianza_consumidor_spain": _scalar("mi_macro_observations", "value", "confianza_consumidor_spain", "retrieved_at"),
        "index_avg_change_pct": index_avg,
    }


# ──────────────────────────────────────────────────────────────
# 11 comparatives builder
# ──────────────────────────────────────────────────────────────

def _fmt(v: float | None, suffix: str = "%", decimals: int = 2) -> str:
    if v is None:
        return "Sin datos"
    return f"{v:.{decimals}f}{suffix}"


def _build_comparatives(personal: dict, mi: dict) -> list[ImpactComparative]:
    comparatives: list[ImpactComparative] = []

    # 1. Inflación vs tasa de ahorro
    ipc = mi.get("ipc_general")
    sav = personal.get("savings_rate")
    comparatives.append(ImpactComparative(
        id="inflation_vs_savings",
        title="Inflación vs tu tasa de ahorro",
        description="Tu tasa de ahorro mensual comparada con el IPC general. Por encima de la inflación significa que mantienes poder adquisitivo.",
        market_value=ipc,
        market_label=f"IPC General: {_fmt(ipc)}",
        personal_value=sav,
        personal_label=f"Tu ahorro: {_fmt(sav)}",
        signal=compute_signal(sav, ipc or 0, higher_is_better=True),
        signal_text="Estás por encima de la inflación" if (sav or 0) > (ipc or 0) else "Tu ahorro no supera la inflación",
        source_ids=["ipc_general"],
    ))

    # 2. Tipo BCE vs meses de liquidez
    bce = mi.get("tipo_bce")
    months = personal.get("months_covered")
    signal2 = "positive" if (months or 0) >= 3 else ("negative" if months is not None else "neutral")
    comparatives.append(ImpactComparative(
        id="rates_vs_liquidity",
        title="Tipos BCE vs tu liquidez",
        description="Con tipos altos conviene tener colchón de liquidez. Se recomiendan mínimo 3 meses de gastos cubiertos.",
        market_value=bce,
        market_label=f"Tipo BCE: {_fmt(bce)}",
        personal_value=months,
        personal_label=f"Tu liquidez: {_fmt(months, ' meses', 1)}",
        signal=signal2,
        signal_text="Tienes colchón suficiente" if (months or 0) >= 3 else "Liquidez por debajo del mínimo recomendado",
        source_ids=["tipo_bce"],
    ))

    # 3. Mercado vs rentabilidad de tu cartera
    mkt = mi.get("index_avg_change_pct")
    port = personal.get("portfolio_return")
    comparatives.append(ImpactComparative(
        id="market_vs_portfolio",
        title="Mercado vs rentabilidad de tu cartera",
        description="Tu rentabilidad media actual comparada con la variación media de los principales índices.",
        market_value=mkt,
        market_label=f"Índices (media): {_fmt(mkt)}",
        personal_value=port,
        personal_label=f"Tu cartera: {_fmt(port)}",
        signal=compute_signal(port, mkt or 0, higher_is_better=True),
        signal_text="Tu cartera supera al mercado" if (port or 0) >= (mkt or 0) else "Tu cartera está por debajo del mercado",
        source_ids=["sp500", "ibex35", "eurostoxx50"],
    ))

    # 4. Poder adquisitivo (informativo)
    ipc2 = mi.get("ipc_general")
    signal4 = "positive" if (ipc2 or 99) < 2.0 else ("negative" if (ipc2 or 0) > 3.0 else "neutral")
    comparatives.append(ImpactComparative(
        id="purchasing_power",
        title="Poder adquisitivo actual",
        description="El IPC general mide la pérdida de poder adquisitivo. Por debajo del 2% es el objetivo del BCE.",
        market_value=ipc2,
        market_label=f"IPC General: {_fmt(ipc2)}",
        personal_value=None,
        personal_label="Indicador macro",
        signal=signal4,
        signal_text="Inflación en objetivo BCE" if (ipc2 or 99) < 2.0 else f"Inflación en {_fmt(ipc2)} — reduce poder de compra",
        source_ids=["ipc_general"],
    ))

    # 5. Euríbor vs deuda hipotecaria
    euribor = mi.get("euribor_12m")
    debt = personal.get("total_debt")
    signal5 = "positive" if (euribor or 99) < 3.0 else ("warning" if debt and debt > 0 else "neutral")
    comparatives.append(ImpactComparative(
        id="euribor_vs_mortgage",
        title="Euríbor vs tu deuda hipotecaria",
        description="El Euríbor 12M marca el coste de la financiación variable. Por encima del 3% encarece las hipotecas a tipo variable.",
        market_value=euribor,
        market_label=f"Euríbor 12M: {_fmt(euribor)}",
        personal_value=debt if debt else None,
        personal_label=f"Tu deuda: {_fmt(debt, ' €', 0)}" if debt else "Sin deuda detectada",
        signal=signal5,
        signal_text="Euríbor en zona razonable" if (euribor or 99) < 3.0 else "Euríbor elevado — revisa tu hipoteca variable",
        source_ids=["euribor_12m"],
    ))

    # 6. EUR/USD vs gasto en dólares
    eurusd = mi.get("eur_usd")
    usd_exp = personal.get("usd_monthly_expense")
    signal6 = compute_signal(eurusd, 1.10, higher_is_better=True)
    comparatives.append(ImpactComparative(
        id="eurusd_vs_intl_spending",
        title="EUR/USD vs tu gasto en dólares",
        description="Con EUR/USD > 1.10 el euro es fuerte y tus compras en dólares son más baratas.",
        market_value=eurusd,
        market_label=f"EUR/USD: {_fmt(eurusd, '', 4)}",
        personal_value=usd_exp if usd_exp else None,
        personal_label=f"Gasto USD/mes: {_fmt(usd_exp, ' €', 0)}" if usd_exp else "Sin gasto en USD detectado",
        signal=signal6,
        signal_text="Euro fuerte — buen momento para compras en USD" if signal6 == "positive" else "Euro débil frente al dólar",
        source_ids=["eur_usd"],
    ))

    # 7. Petróleo vs gasto en transporte
    brent = mi.get("brent_crude")
    transport = personal.get("transport_monthly")
    signal7 = "positive" if (brent or 999) < 80 else ("negative" if (brent or 0) > 90 else "neutral")
    comparatives.append(ImpactComparative(
        id="oil_vs_transport",
        title="Petróleo vs tu gasto en transporte",
        description="El precio del Brent impacta en los carburantes. Por debajo de 80 USD/barril es favorable.",
        market_value=brent,
        market_label=f"Brent: {_fmt(brent, ' USD', 1)}",
        personal_value=transport if transport else None,
        personal_label=f"Transporte/mes: {_fmt(transport, ' €', 0)}" if transport else "Sin gasto en transporte detectado",
        signal=signal7,
        signal_text="Precio del petróleo favorable" if signal7 == "positive" else "Petróleo elevado — puede encarecer combustibles",
        source_ids=["brent_crude"],
    ))

    # 8. Prima de riesgo España (informativo)
    spread = mi.get("risk_premium_bps")
    signal8 = "positive" if (spread or 999) < 100 else ("negative" if (spread or 0) > 200 else "neutral")
    comparatives.append(ImpactComparative(
        id="risk_premium_spain",
        title="Prima de riesgo España",
        description="Diferencial bono español 10Y vs bund alemán en puntos básicos. Por encima de 100 bps señala tensión en la deuda española.",
        market_value=spread,
        market_label=f"Prima de riesgo: {_fmt(spread, ' bps', 0)}" if spread is not None else "Sin datos",
        personal_value=None,
        personal_label="Indicador macro",
        signal=signal8,
        signal_text="Prima de riesgo controlada" if signal8 == "positive" else "Prima de riesgo elevada",
        source_ids=["spain_10y", "germany_10y"],
    ))

    # 9. Rentabilidad real de la cartera
    real = (personal.get("portfolio_return") or 0) - (mi.get("ipc_general") or 0) if personal.get("portfolio_return") is not None else None
    signal9 = compute_signal(real, 0, higher_is_better=True)
    comparatives.append(ImpactComparative(
        id="real_portfolio_return",
        title="Rentabilidad real de tu cartera",
        description="Rentabilidad de tu cartera menos la inflación. Positiva significa que ganas poder adquisitivo.",
        market_value=mi.get("ipc_general"),
        market_label=f"IPC (referencia): {_fmt(mi.get('ipc_general'))}",
        personal_value=real,
        personal_label=f"Rentabilidad real: {_fmt(real)}",
        signal=signal9,
        signal_text="Tu cartera gana en términos reales" if signal9 == "positive" else "Tu cartera pierde frente a la inflación",
        source_ids=["ipc_general"],
    ))

    # 10. IPC subyacente vs gasto en alimentación y hogar
    ipc_sub = mi.get("ipc_subyacente")
    food = personal.get("food_home_monthly")
    monthly_exp = personal.get("monthly_expense") or 0
    food_pct = (food / monthly_exp * 100) if food and monthly_exp > 0 else None
    signal10 = compute_signal(food_pct, ipc_sub or 0, higher_is_better=False)
    comparatives.append(ImpactComparative(
        id="core_cpi_vs_food_spending",
        title="IPC subyacente vs tu gasto en alimentación y hogar",
        description="El IPC subyacente excluye energía y alimentación no elaborada. Si tu gasto en hogar/alimentos sube más que el subyacente, sufres más inflación que la media.",
        market_value=ipc_sub,
        market_label=f"IPC Subyacente: {_fmt(ipc_sub)}",
        personal_value=food_pct,
        personal_label=f"Alim.+Hogar sobre gasto: {_fmt(food_pct)}",
        signal=signal10,
        signal_text="Tu gasto esencial está bajo control" if signal10 == "positive" else "Tu gasto esencial supera el IPC subyacente",
        source_ids=["ipc_subyacente"],
    ))

    # 11. Confianza consumidor vs liquidez
    confidence = mi.get("confianza_consumidor_spain")
    months2 = personal.get("months_covered")
    min_months = 6.0 if (confidence or 100) < 90 else 3.0
    signal11 = "positive" if (months2 or 0) >= min_months else ("negative" if months2 is not None else "neutral")
    comparatives.append(ImpactComparative(
        id="consumer_confidence_vs_liquidity",
        title="Confianza del consumidor vs tu liquidez",
        description="Cuando la confianza del consumidor baja de 90, conviene tener 6 meses de colchón en lugar de 3.",
        market_value=confidence,
        market_label=f"Confianza: {_fmt(confidence, ' pts', 1)}",
        personal_value=months2,
        personal_label=f"Tu liquidez: {_fmt(months2, ' meses', 1)}",
        signal=signal11,
        signal_text=f"Liquidez suficiente (mínimo recomendado: {min_months:.0f} meses)" if signal11 == "positive" else f"Aumenta tu colchón a {min_months:.0f} meses",
        source_ids=["confianza_consumidor_spain"],
    ))

    return comparatives


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def compute_personal_impact(db: Session) -> PersonalImpactOut:
    now = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []

    try:
        personal = _get_personal_data(db)
    except Exception as exc:
        warnings.append(f"Error leyendo datos personales: {exc}")
        personal = {
            "total_balance": 0.0, "monthly_income": 0.0, "monthly_expense": 0.0,
            "savings_rate": None, "months_covered": None, "portfolio_return": None,
            "total_debt": 0.0, "usd_monthly_expense": 0.0,
            "transport_monthly": 0.0, "food_home_monthly": 0.0,
        }

    try:
        mi_data = _get_mi_data()
    except Exception as exc:
        warnings.append(f"Error leyendo datos MI: {exc}")
        mi_data = {k: None for k in (
            "ipc_general", "tipo_bce", "euribor_12m", "eur_usd", "brent_crude",
            "bono_spain_10y", "bund_10y", "risk_premium_bps", "ipc_subyacente",
            "confianza_consumidor_spain", "index_avg_change_pct",
        )}

    comparatives = _build_comparatives(personal, mi_data)
    return PersonalImpactOut(generated_at=now, comparatives=comparatives, warnings=warnings)
