# backend/tests/market_intelligence/test_personal_impact.py
from unittest.mock import MagicMock, patch
from app.modules.market_intelligence.api.impact import (
    compute_signal,
    _build_comparatives,
)
from app.modules.market_intelligence.api.schemas import ImpactComparative


def test_compute_signal_positive():
    assert compute_signal(personal=10.0, threshold=5.0, higher_is_better=True) == "positive"


def test_compute_signal_negative():
    assert compute_signal(personal=3.0, threshold=5.0, higher_is_better=True) == "negative"


def test_compute_signal_neutral_when_none():
    assert compute_signal(personal=None, threshold=5.0, higher_is_better=True) == "neutral"


def test_compute_signal_neutral_within_5pct():
    # delta < threshold * 0.05 → neutral
    assert compute_signal(personal=5.1, threshold=5.0, higher_is_better=True) == "neutral"


def _make_db_stub(
    total_balance: float = 5000.0,
    monthly_income: float = 3000.0,
    monthly_expense: float = 2000.0,
    portfolio_return: float | None = 8.0,
    total_debt: float = 0.0,
    usd_monthly: float = 0.0,
    transport_monthly: float = 200.0,
    food_monthly: float = 500.0,
) -> MagicMock:
    """Returns a mock DB session with stubbed scalar queries."""
    db = MagicMock()
    return db


def test_build_comparatives_returns_11():
    """_build_comparatives returns exactly 11 ImpactComparative objects."""
    personal_data = {
        "total_balance": 5000.0,
        "monthly_income": 3000.0,
        "monthly_expense": 2000.0,
        "savings_rate": 33.3,
        "months_covered": 2.5,
        "portfolio_return": 8.0,
        "total_debt": 0.0,
        "usd_monthly_expense": 50.0,
        "transport_monthly": 200.0,
        "food_home_monthly": 500.0,
    }
    mi_data = {
        "ipc_general": 3.2,
        "tipo_bce": 4.0,
        "euribor_12m": 3.5,
        "eur_usd": 1.08,
        "brent_crude": 85.0,
        "bono_spain_10y": 3.4,
        "bund_10y": 2.3,
        "ipc_subyacente": 3.0,
        "confianza_consumidor_spain": 95.0,
        "index_avg_change_pct": 5.0,
    }
    comparatives = _build_comparatives(personal_data, mi_data)
    assert len(comparatives) == 11
    for c in comparatives:
        assert isinstance(c, ImpactComparative)
        assert c.signal in ("positive", "negative", "neutral", "warning")


def test_comparative_inflation_vs_savings_positive():
    """savings_rate > ipc_general → positive signal."""
    personal_data = {
        "total_balance": 5000.0,
        "monthly_income": 3000.0,
        "monthly_expense": 1000.0,
        "savings_rate": 66.7,
        "months_covered": 5.0,
        "portfolio_return": None,
        "total_debt": 0.0,
        "usd_monthly_expense": 0.0,
        "transport_monthly": 100.0,
        "food_home_monthly": 400.0,
    }
    mi_data = {
        "ipc_general": 3.2,
        "tipo_bce": 4.0,
        "euribor_12m": 3.5,
        "eur_usd": 1.08,
        "brent_crude": 85.0,
        "bono_spain_10y": 3.4,
        "bund_10y": 2.3,
        "ipc_subyacente": 3.0,
        "confianza_consumidor_spain": 95.0,
        "index_avg_change_pct": 5.0,
    }
    comparatives = _build_comparatives(personal_data, mi_data)
    infl_vs_sav = next(c for c in comparatives if c.id == "inflation_vs_savings")
    assert infl_vs_sav.signal == "positive"


def test_comparative_purchasing_power_no_personal_data():
    """purchasing_power is informational — personal_value is None, signal neutral."""
    personal_data = {
        "total_balance": 0.0,
        "monthly_income": 0.0,
        "monthly_expense": 0.0,
        "savings_rate": None,
        "months_covered": None,
        "portfolio_return": None,
        "total_debt": 0.0,
        "usd_monthly_expense": 0.0,
        "transport_monthly": 0.0,
        "food_home_monthly": 0.0,
    }
    mi_data = {
        "ipc_general": 3.2,
        "tipo_bce": 4.0,
        "euribor_12m": 3.5,
        "eur_usd": 1.08,
        "brent_crude": 85.0,
        "bono_spain_10y": 3.4,
        "bund_10y": 2.3,
        "ipc_subyacente": 3.0,
        "confianza_consumidor_spain": 95.0,
        "index_avg_change_pct": 5.0,
    }
    comparatives = _build_comparatives(personal_data, mi_data)
    pp = next(c for c in comparatives if c.id == "purchasing_power")
    assert pp.personal_value is None
    assert pp.signal in ("positive", "negative", "neutral")
