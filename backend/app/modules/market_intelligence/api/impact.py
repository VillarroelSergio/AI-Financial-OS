# backend/app/modules/market_intelligence/api/impact.py
"""Comparativas de impacto personal — 100% determinista, sin LLM.

Reglas:
- Sin dato de mercado → signal "no_data" y ningún veredicto (nunca se afirma nada desde un None).
- Comparativas que no aplican al perfil (sin deuda, sin gasto USD, sin cartera...) se omiten.
- Cuando hay datos, se cuantifica el impacto en €/mes además del porcentaje.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.investment import Holding
from app.models.transaction import Transaction
from app.modules.market_intelligence.api import constants as C
from app.modules.market_intelligence.api import macro_series
from app.modules.market_intelligence.api.schemas import ImpactComparative, PersonalImpactOut
from app.modules.market_intelligence.storage import repository

# ECO-4: buckets de gasto → categorías canónicas del sistema (seeds/categories.py), con
# substrings de fallback documentados para categorías creadas por el usuario. Sustituye el
# matching por subcadena suelta ("casa", "alimentaci") que podía colar coincidencias falsas.
_CATEGORY_BUCKETS: dict[str, dict[str, list[str]]] = {
    "transport": {"canonical": ["Transporte"], "fallback": ["gasolina", "combustible"]},
    "food": {"canonical": ["Alimentación"], "fallback": ["aliment"]},
    "home": {"canonical": ["Casa"], "fallback": ["hogar", "suministro"]},
}

# ──────────────────────────────────────────────────────────────
# Signal helper
# ──────────────────────────────────────────────────────────────

def weighted_portfolio_return(holdings) -> float | None:
    """ECO-4: retorno de cartera PONDERADO por valor de posición.

    Media simple = sesgo: una posición de 100 € pesaba igual que una de 50.000 €. Aquí
    (Σ valor_mercado − Σ coste) / Σ coste. Decimal en todo el cálculo (regla del proyecto:
    nada de float en dinero). None si no hay coste base positivo.
    """
    cost_basis = Decimal("0")
    market_val = Decimal("0")
    for h in holdings:
        if h.average_price is None or h.quantity is None or h.current_price is None or h.average_price <= 0:
            continue
        cost_basis += h.average_price * h.quantity
        market_val += h.current_price * h.quantity
    if cost_basis <= 0:
        return None
    return float((market_val - cost_basis) / cost_basis * 100)


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

    holdings = db.query(Holding).filter(Holding.current_price.isnot(None)).all()
    portfolio_return = weighted_portfolio_return(holdings)

    # Total debt from loan/mortgage/credit accounts (negative balances stored as negative)
    total_debt = abs(float(
        db.query(func.sum(Account.current_balance))
        .filter(
            Account.type.in_(["loan", "mortgage", "credit"]),
            Account.is_active == True,  # noqa: E712
        )
        .scalar() or 0
    ))

    def _cat_monthly(bucket: str) -> float:
        """Gasto mensual medio del bucket: categoría canónica (match exacto) o fallback."""
        spec = _CATEGORY_BUCKETS[bucket]
        name_l = func.lower(Category.name)
        filters = [name_l == c.lower() for c in spec["canonical"]]
        filters += [name_l.contains(fb.lower()) for fb in spec["fallback"]]
        txns = (
            db.query(func.sum(Transaction.amount))
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .filter(
                Transaction.amount < 0,
                Transaction.date >= cutoff,
                or_(*filters),
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

    transport_monthly = _cat_monthly("transport")
    food_home_monthly = _cat_monthly("food")
    home_monthly = _cat_monthly("home")

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
        "home_monthly": home_monthly,
    }


# ──────────────────────────────────────────────────────────────
# MI data queries (DuckDB)
# ──────────────────────────────────────────────────────────────

_MI_EMPTY = {
    "ipc_general": None, "tipo_bce": None, "euribor_12m": None, "eur_usd": None,
    "brent": None, "spain_10y": None, "germany_10y": None, "risk_premium_bps": None,
    "ipc_subyacente": None, "confianza_consumidor_spain": None, "index_avg_change_1y": None,
    "euribor_12m_year_ago": None, "brent_change_1y": None,
}


def _get_mi_data() -> dict:
    """ECO-4: sin SQL crudo. Lecturas macro vía `macro_series`; el resto vía helpers del
    repository (única puerta al almacén)."""
    def _num(v) -> float | None:
        return float(v) if v is not None else None

    forex = {r["catalog_item_id"]: r for r in repository.get_latest_forex()}
    bonds = {r["catalog_item_id"]: r for r in repository.get_latest_bonds()}
    quotes = {r["catalog_item_id"]: r for r in repository.get_latest_quotes()}
    commodities = {r["catalog_item_id"]: r for r in repository.get_latest_commodities()}

    spain_10y = _num(bonds.get("spain_10y", {}).get("yield_value"))
    germany_10y = _num(bonds.get("germany_10y", {}).get("yield_value"))
    spread = (spain_10y - germany_10y) * 100 if spain_10y is not None and germany_10y is not None else None

    brent = _num(quotes.get("brent", {}).get("price"))
    if brent is None:
        brent = _num(commodities.get("brent", {}).get("price"))

    index_changes = [repository.get_price_change_1y(cid) for cid in ("sp500", "ibex35", "eurostoxx50")]
    valid = [v for v in index_changes if v is not None]
    index_avg = sum(valid) / len(valid) if valid else None

    return {
        "ipc_general": macro_series.latest("ipc_general"),
        "tipo_bce": macro_series.latest("tipo_bce"),
        "euribor_12m": macro_series.latest("euribor_12m"),
        "eur_usd": _num(forex.get("eur_usd", {}).get("rate")),
        "brent": brent,
        "spain_10y": spain_10y,
        "germany_10y": germany_10y,
        "risk_premium_bps": spread,
        "ipc_subyacente": macro_series.latest("ipc_subyacente"),
        "confianza_consumidor_spain": macro_series.latest("confianza_consumidor_spain"),
        "index_avg_change_1y": index_avg,
        "euribor_12m_year_ago": macro_series.value_year_ago("euribor_12m"),
        "brent_change_1y": repository.get_price_change_1y("brent"),
    }


# ──────────────────────────────────────────────────────────────
# Comparatives builder
# ──────────────────────────────────────────────────────────────

def _fmt(v: float | None, suffix: str = "%", decimals: int = 2) -> str:
    if v is None:
        return "Sin datos"
    return f"{v:.{decimals}f}{suffix}"


_NO_DATA_TEXT = "Sin datos de mercado — comparativa no disponible"


def _build_comparatives(personal: dict, mi: dict) -> list[ImpactComparative]:
    comparatives: list[ImpactComparative] = []
    balance = personal.get("total_balance") or 0.0

    # 1. Inflación vs tasa de ahorro (aplica si conocemos ingresos)
    ipc = mi.get("ipc_general")
    sav = personal.get("savings_rate")
    if sav is not None:
        if ipc is None:
            signal1, text1 = "no_data", _NO_DATA_TEXT
        else:
            signal1 = compute_signal(sav, ipc, higher_is_better=True)
            text1 = "Estás por encima de la inflación" if sav > ipc else "Tu ahorro no supera la inflación"
            drag = balance * ipc / 100 / 12
            if drag >= C.MIN_EUR_PER_MONTH_TO_SHOW:
                text1 += f" · La inflación cuesta ~{drag:,.0f} €/mes a tu efectivo"
        comparatives.append(ImpactComparative(
            id="inflation_vs_savings",
            title="Inflación vs tu tasa de ahorro",
            description="Tu tasa de ahorro mensual comparada con el IPC general. Por encima de la inflación significa que mantienes poder adquisitivo.",
            market_value=ipc,
            market_label=f"IPC General: {_fmt(ipc)}",
            personal_value=sav,
            personal_label=f"Tu ahorro: {_fmt(sav)}",
            signal=signal1,
            signal_text=text1,
            source_ids=["ipc_general"],
        ))

    # 2. Tipo BCE vs meses de liquidez (aplica si conocemos gastos)
    bce = mi.get("tipo_bce")
    months = personal.get("months_covered")
    if months is not None:
        if bce is None:
            signal2, text2 = "no_data", _NO_DATA_TEXT
        else:
            signal2 = "positive" if months >= C.LIQUIDITY_MIN_MONTHS else "negative"
            text2 = "Tienes colchón suficiente" if months >= C.LIQUIDITY_MIN_MONTHS else "Liquidez por debajo del mínimo recomendado"
            opportunity = balance * bce / 100 / 12
            if opportunity >= C.MIN_EUR_PER_MONTH_TO_SHOW:
                text2 += f" · A tipo BCE tu efectivo podría rentar ~{opportunity:,.0f} €/mes"
        comparatives.append(ImpactComparative(
            id="rates_vs_liquidity",
            title="Tipos BCE vs tu liquidez",
            description="Con tipos altos conviene tener colchón de liquidez. Se recomiendan mínimo 3 meses de gastos cubiertos.",
            market_value=bce,
            market_label=f"Tipo BCE: {_fmt(bce)}",
            personal_value=months,
            personal_label=f"Tu liquidez: {_fmt(months, ' meses', 1)}",
            signal=signal2,
            signal_text=text2,
            source_ids=["tipo_bce"],
        ))

    # 3. Mercado (12 meses) vs tu cartera (aplica si hay cartera)
    mkt = mi.get("index_avg_change_1y")
    port = personal.get("portfolio_return")
    if port is not None:
        if mkt is None:
            signal3, text3 = "no_data", _NO_DATA_TEXT
        else:
            signal3 = compute_signal(port, mkt, higher_is_better=True)
            text3 = "Tu cartera supera al mercado" if port >= mkt else "Tu cartera está por debajo del mercado"
        comparatives.append(ImpactComparative(
            id="market_vs_portfolio",
            title="Mercado vs rentabilidad de tu cartera",
            description="Variación media de S&P 500, IBEX 35 y EuroStoxx 50 en los últimos 12 meses frente al retorno de tu cartera desde la compra. Las ventanas no son idénticas: úsalo como orientación.",
            market_value=mkt,
            market_label=f"Índices (12 meses): {_fmt(mkt)}",
            personal_value=port,
            personal_label=f"Tu cartera (desde compra): {_fmt(port)}",
            signal=signal3,
            signal_text=text3,
            source_ids=["sp500", "ibex35", "eurostoxx50"],
        ))

    # 4. Poder adquisitivo (informativo, siempre que haya IPC)
    if ipc is None:
        signal4, text4 = "no_data", _NO_DATA_TEXT
    elif ipc < C.INFLATION_BCE_TARGET:
        signal4, text4 = "positive", "Inflación en objetivo BCE"
    elif ipc > C.INFLATION_HIGH:
        signal4, text4 = "negative", f"Inflación en {_fmt(ipc)} — reduce poder de compra"
    else:
        signal4, text4 = "neutral", f"Inflación moderada ({_fmt(ipc)})"
    comparatives.append(ImpactComparative(
        id="purchasing_power",
        title="Poder adquisitivo actual",
        description="El IPC general mide la pérdida de poder adquisitivo. Por debajo del 2% es el objetivo del BCE.",
        market_value=ipc,
        market_label=f"IPC General: {_fmt(ipc)}",
        personal_value=None,
        personal_label="Indicador macro",
        signal=signal4,
        signal_text=text4,
        source_ids=["ipc_general"],
    ))

    # 5. Euríbor vs deuda hipotecaria (solo si hay deuda)
    euribor = mi.get("euribor_12m")
    debt = personal.get("total_debt") or 0.0
    if debt > 0:
        if euribor is None:
            signal5, text5 = "no_data", _NO_DATA_TEXT
        elif euribor < C.EURIBOR_COMFORT_MAX:
            signal5, text5 = "positive", "Euríbor en zona razonable"
        else:
            signal5, text5 = "warning", "Euríbor elevado — revisa tu hipoteca variable"
        # Cuantificación: variación anual del Euríbor aplicada a tu deuda pendiente.
        euribor_ya = mi.get("euribor_12m_year_ago")
        if euribor is not None and euribor_ya is not None:
            monthly_delta = debt * (euribor - euribor_ya) / 100 / 12
            if abs(monthly_delta) >= C.MIN_EUR_PER_MONTH_TO_SHOW:
                direction = "encarece" if monthly_delta > 0 else "abarata"
                text5 += (
                    f" · La variación anual del Euríbor ({euribor_ya:.2f}%→{euribor:.2f}%) "
                    f"{direction} tu revisión ~{abs(monthly_delta):,.0f} €/mes (aprox.)"
                )
        comparatives.append(ImpactComparative(
            id="euribor_vs_mortgage",
            title="Euríbor vs tu deuda hipotecaria",
            description="El Euríbor 12M marca el coste de la financiación variable. Por encima del 3% encarece las hipotecas a tipo variable.",
            market_value=euribor,
            market_label=f"Euríbor 12M: {_fmt(euribor)}",
            personal_value=debt,
            personal_label=f"Tu deuda: {_fmt(debt, ' €', 0)}",
            signal=signal5,
            signal_text=text5,
            source_ids=["euribor_12m"],
        ))

    # 6. EUR/USD vs gasto en dólares (solo si hay gasto en USD)
    eurusd = mi.get("eur_usd")
    usd_exp = personal.get("usd_monthly_expense") or 0.0
    if usd_exp > 0:
        if eurusd is None:
            signal6, text6 = "no_data", _NO_DATA_TEXT
        else:
            signal6 = compute_signal(eurusd, C.EURUSD_STRONG_EURO, higher_is_better=True)
            text6 = ("Euro fuerte — buen momento para compras en USD"
                     if signal6 == "positive" else "Euro débil frente al dólar")
        comparatives.append(ImpactComparative(
            id="eurusd_vs_intl_spending",
            title="EUR/USD vs tu gasto en dólares",
            description="Con EUR/USD > 1.10 el euro es fuerte y tus compras en dólares son más baratas.",
            market_value=eurusd,
            market_label=f"EUR/USD: {_fmt(eurusd, '', 4)}",
            personal_value=usd_exp,
            personal_label=f"Gasto USD/mes: {_fmt(usd_exp, ' €', 0)}",
            signal=signal6,
            signal_text=text6,
            source_ids=["eur_usd"],
        ))

    # 7. Petróleo vs gasto en transporte (solo si hay gasto en transporte)
    brent = mi.get("brent")
    transport = personal.get("transport_monthly") or 0.0
    if transport > 0:
        if brent is None:
            signal7, text7 = "no_data", _NO_DATA_TEXT
        elif brent < C.BRENT_FAVORABLE:
            signal7, text7 = "positive", "Precio del petróleo favorable"
        elif brent > C.BRENT_HIGH:
            signal7, text7 = "negative", "Petróleo elevado — puede encarecer combustibles"
        else:
            signal7, text7 = "neutral", "Petróleo en rango medio"
        comparatives.append(ImpactComparative(
            id="oil_vs_transport",
            title="Petróleo vs tu gasto en transporte",
            description="El precio del Brent impacta en los carburantes. Por debajo de 80 USD/barril es favorable.",
            market_value=brent,
            market_label=f"Brent: {_fmt(brent, ' USD', 1)}",
            personal_value=transport,
            personal_label=f"Transporte/mes: {_fmt(transport, ' €', 0)}",
            signal=signal7,
            signal_text=text7,
            source_ids=["brent"],
        ))

    # 7b. Energía vs tu gasto en Casa (solo si hay gasto en hogar)
    brent_yoy = mi.get("brent_change_1y")
    home = personal.get("home_monthly") or 0.0
    if home > 0:
        if brent_yoy is None:
            signal7b, text7b = "no_data", _NO_DATA_TEXT
        elif brent_yoy > C.ENERGY_YOY_UP:
            signal7b = "warning"
            text7b = f"La energía sube {_fmt(brent_yoy, '%', 1)} interanual — vigila luz y gas en tu gasto de Casa"
        elif brent_yoy < C.ENERGY_YOY_DOWN:
            signal7b = "positive"
            text7b = f"La energía baja {_fmt(abs(brent_yoy), '%', 1)} interanual — alivio en los suministros del hogar"
        else:
            signal7b, text7b = "neutral", "Precio de la energía estable en el último año"
        comparatives.append(ImpactComparative(
            id="energy_vs_home",
            title="Energía vs tu gasto en Casa",
            description="Variación interanual del Brent como proxy del coste energético frente a tu gasto mensual en el hogar (luz, gas, suministros).",
            market_value=brent_yoy,
            market_label=f"Energía (12 meses): {_fmt(brent_yoy, '%', 1)}",
            personal_value=home,
            personal_label=f"Casa/mes: {_fmt(home, ' €', 0)}",
            signal=signal7b,
            signal_text=text7b,
            source_ids=["brent"],
        ))

    # 8. Prima de riesgo España (informativo)
    spread = mi.get("risk_premium_bps")
    if spread is None:
        signal8, text8 = "no_data", _NO_DATA_TEXT
    elif spread < C.RISK_PREMIUM_LOW:
        signal8, text8 = "positive", "Prima de riesgo controlada"
    elif spread > C.RISK_PREMIUM_HIGH:
        signal8, text8 = "negative", "Prima de riesgo elevada"
    else:
        signal8, text8 = "neutral", "Prima de riesgo en rango medio"
    comparatives.append(ImpactComparative(
        id="risk_premium_spain",
        title="Prima de riesgo España",
        description="Diferencial bono español 10Y vs bund alemán en puntos básicos. Por encima de 100 bps señala tensión en la deuda española.",
        market_value=spread,
        market_label=f"Prima de riesgo: {_fmt(spread, ' bps', 0)}",
        personal_value=None,
        personal_label="Indicador macro",
        signal=signal8,
        signal_text=text8,
        source_ids=["spain_10y", "germany_10y"],
    ))

    # 9. Rentabilidad real de la cartera (solo con cartera e IPC)
    if port is not None:
        if ipc is None:
            real: float | None = None
            signal9, text9 = "no_data", _NO_DATA_TEXT
        else:
            real = port - ipc
            signal9 = compute_signal(real, 0, higher_is_better=True)
            text9 = ("Tu cartera gana en términos reales" if signal9 == "positive"
                     else "Tu cartera pierde frente a la inflación")
        comparatives.append(ImpactComparative(
            id="real_portfolio_return",
            title="Rentabilidad real de tu cartera",
            description="Rentabilidad de tu cartera menos la inflación. Positiva significa que ganas poder adquisitivo.",
            market_value=ipc,
            market_label=f"IPC (referencia): {_fmt(ipc)}",
            personal_value=real,
            personal_label=f"Rentabilidad real: {_fmt(real)}",
            signal=signal9,
            signal_text=text9,
            source_ids=["ipc_general"],
        ))

    # 10. IPC subyacente vs gasto en alimentación y hogar (solo con datos de gasto)
    ipc_sub = mi.get("ipc_subyacente")
    food = personal.get("food_home_monthly") or 0.0
    monthly_exp = personal.get("monthly_expense") or 0.0
    if food > 0 and monthly_exp > 0:
        food_pct = food / monthly_exp * 100
        if ipc_sub is None:
            signal10, text10 = "no_data", _NO_DATA_TEXT
        else:
            signal10 = compute_signal(food_pct, ipc_sub, higher_is_better=False)
            text10 = ("Tu gasto esencial está bajo control" if signal10 == "positive"
                      else "Tu gasto esencial supera el IPC subyacente")
        comparatives.append(ImpactComparative(
            id="core_cpi_vs_food_spending",
            title="IPC subyacente vs tu gasto en alimentación y hogar",
            description="El IPC subyacente excluye energía y alimentación no elaborada. Si tu gasto en hogar/alimentos sube más que el subyacente, sufres más inflación que la media.",
            market_value=ipc_sub,
            market_label=f"IPC Subyacente: {_fmt(ipc_sub)}",
            personal_value=food_pct,
            personal_label=f"Alim.+Hogar sobre gasto: {_fmt(food_pct)}",
            signal=signal10,
            signal_text=text10,
            source_ids=["ipc_subyacente"],
        ))

    # 11. Confianza consumidor vs liquidez (aplica si conocemos gastos)
    confidence = mi.get("confianza_consumidor_spain")
    if months is not None:
        if confidence is None:
            signal11, text11 = "no_data", _NO_DATA_TEXT
        else:
            min_months = (C.LIQUIDITY_MIN_MONTHS_LOW_CONFIDENCE
                          if confidence < C.CONSUMER_CONFIDENCE_LOW else C.LIQUIDITY_MIN_MONTHS)
            signal11 = "positive" if months >= min_months else "negative"
            text11 = (f"Liquidez suficiente (mínimo recomendado: {min_months:.0f} meses)"
                      if signal11 == "positive" else f"Aumenta tu colchón a {min_months:.0f} meses")
        comparatives.append(ImpactComparative(
            id="consumer_confidence_vs_liquidity",
            title="Confianza del consumidor vs tu liquidez",
            description="Cuando la confianza del consumidor baja de 90, conviene tener 6 meses de colchón en lugar de 3.",
            market_value=confidence,
            market_label=f"Confianza: {_fmt(confidence, ' pts', 1)}",
            personal_value=months,
            personal_label=f"Tu liquidez: {_fmt(months, ' meses', 1)}",
            signal=signal11,
            signal_text=text11,
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
            "transport_monthly": 0.0, "food_home_monthly": 0.0, "home_monthly": 0.0,
        }

    try:
        mi_data = _get_mi_data()
    except Exception as exc:
        warnings.append(f"Error leyendo datos MI: {exc}")
        mi_data = dict(_MI_EMPTY)

    comparatives = _build_comparatives(personal, mi_data)
    no_data = sum(1 for c in comparatives if c.signal == "no_data")
    if no_data:
        warnings.append(f"{no_data} comparativas sin datos de mercado disponibles.")
    return PersonalImpactOut(generated_at=now, comparatives=comparatives, warnings=warnings)
