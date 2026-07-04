# backend/tests/market_intelligence/test_personal_impact.py
from app.modules.market_intelligence.api.impact import (
    _MI_EMPTY,
    _build_comparatives,
    compute_signal,
)
from app.modules.market_intelligence.api.schemas import ImpactComparative

FULL_PERSONAL = {
    "total_balance": 5000.0,
    "monthly_income": 3000.0,
    "monthly_expense": 2000.0,
    "savings_rate": 33.3,
    "months_covered": 2.5,
    "portfolio_return": 8.0,
    "total_debt": 12000.0,
    "usd_monthly_expense": 50.0,
    "transport_monthly": 200.0,
    "food_home_monthly": 500.0,
}

FULL_MI = {
    "ipc_general": 3.2,
    "tipo_bce": 4.0,
    "euribor_12m": 3.5,
    "eur_usd": 1.08,
    "brent": 85.0,
    "spain_10y": 3.4,
    "germany_10y": 2.3,
    "risk_premium_bps": 110.0,
    "ipc_subyacente": 3.0,
    "confianza_consumidor_spain": 95.0,
    "index_avg_change_1y": 5.0,
}


def test_compute_signal_positive():
    assert compute_signal(personal=10.0, threshold=5.0, higher_is_better=True) == "positive"


def test_compute_signal_negative():
    assert compute_signal(personal=3.0, threshold=5.0, higher_is_better=True) == "negative"


def test_compute_signal_neutral_when_none():
    assert compute_signal(personal=None, threshold=5.0, higher_is_better=True) == "neutral"


def test_compute_signal_neutral_within_5pct():
    assert compute_signal(personal=5.1, threshold=5.0, higher_is_better=True) == "neutral"


def test_build_comparatives_full_data_returns_11():
    comparatives = _build_comparatives(FULL_PERSONAL, FULL_MI)
    assert len(comparatives) == 11
    for c in comparatives:
        assert isinstance(c, ImpactComparative)
        assert c.signal in ("positive", "negative", "neutral", "warning")


def test_no_market_data_never_asserts_verdicts():
    """Sin datos de mercado → signal no_data, nunca un veredicto inventado."""
    comparatives = _build_comparatives(FULL_PERSONAL, dict(_MI_EMPTY))
    assert comparatives, "las comparativas aplicables deben seguir presentes"
    for c in comparatives:
        assert c.signal == "no_data", f"{c.id} afirma '{c.signal_text}' sin datos de mercado"
        assert "Sin datos de mercado" in c.signal_text


def test_purchasing_power_no_data_has_no_interpolated_none():
    comparatives = _build_comparatives(FULL_PERSONAL, dict(_MI_EMPTY))
    pp = next(c for c in comparatives if c.id == "purchasing_power")
    assert pp.signal == "no_data"
    assert "Sin datos —" not in pp.signal_text.replace("Sin datos de mercado", "")


def test_relevance_skips_non_applicable_cards():
    personal = dict(FULL_PERSONAL, total_debt=0.0, usd_monthly_expense=0.0,
                    transport_monthly=0.0, portfolio_return=None)
    ids = {c.id for c in _build_comparatives(personal, FULL_MI)}
    assert "euribor_vs_mortgage" not in ids
    assert "eurusd_vs_intl_spending" not in ids
    assert "oil_vs_transport" not in ids
    assert "market_vs_portfolio" not in ids
    assert "real_portfolio_return" not in ids
    # Las informativas y las que sí aplican permanecen
    assert "purchasing_power" in ids
    assert "inflation_vs_savings" in ids


def test_euro_quantification_in_signal_text():
    comparatives = _build_comparatives(FULL_PERSONAL, FULL_MI)
    infl = next(c for c in comparatives if c.id == "inflation_vs_savings")
    assert "€/mes" in infl.signal_text
    liq = next(c for c in comparatives if c.id == "rates_vs_liquidity")
    assert "€/mes" in liq.signal_text


def test_market_vs_portfolio_uses_yearly_window_label():
    comparatives = _build_comparatives(FULL_PERSONAL, FULL_MI)
    mkt = next(c for c in comparatives if c.id == "market_vs_portfolio")
    assert "12 meses" in mkt.market_label
    assert "desde compra" in mkt.personal_label
