"""ECO-4: lectura macro unificada, retorno de cartera ponderado y matching por palabra."""
from decimal import Decimal
from types import SimpleNamespace

from app.modules.market_intelligence.api import macro_series
from app.modules.market_intelligence.api.impact import weighted_portfolio_return
from app.modules.market_intelligence.api.personal_economy import keyword_hits


def _patch_history(monkeypatch, points):
    monkeypatch.setattr(
        macro_series.repository, "get_macro_history",
        lambda max_points=60: {"x": points},
    )


def test_macro_series_monthly(monkeypatch):
    points = [(f"2025-{m:02d}", 2.0) for m in range(1, 13)] + [("2026-01", 3.0)]
    # el de hace un año respecto a 2026-01 es 2025-01 = 2.0
    _patch_history(monkeypatch, points)
    assert macro_series.latest("x") == 3.0
    assert macro_series.history("x", limit=2) == [("2025-12", 2.0), ("2026-01", 3.0)]
    assert macro_series.value_year_ago("x") == 2.0
    assert macro_series.change_12m("x") == 50.0  # (3-2)/2*100


def test_macro_series_quarterly(monkeypatch):
    points = [("2025-Q1", 100.0), ("2025-Q2", 101.0), ("2025-Q3", 102.0),
              ("2025-Q4", 103.0), ("2026-Q1", 110.0)]
    _patch_history(monkeypatch, points)
    assert macro_series.latest("x") == 110.0
    assert macro_series.value_year_ago("x") == 100.0
    assert macro_series.change_12m("x") == 10.0


def test_macro_series_insufficient_history(monkeypatch):
    _patch_history(monkeypatch, [("2026-01", 3.0)])
    assert macro_series.value_year_ago("x") is None
    assert macro_series.change_12m("x") is None


def test_weighted_return_not_biased_by_tiny_position():
    # 100 € que dobla (+100%) vs 50.000 € que cae (-10%). La media simple daría +45%;
    # la ponderada por valor debe estar dominada por la posición grande (~-9.78%).
    holdings = [
        SimpleNamespace(quantity=Decimal("1"), average_price=Decimal("100"), current_price=Decimal("200")),
        SimpleNamespace(quantity=Decimal("1"), average_price=Decimal("50000"), current_price=Decimal("45000")),
    ]
    r = weighted_portfolio_return(holdings)
    assert r is not None
    assert -10.0 < r < -9.5           # ≈ -9.78%
    assert abs(r - 45.0) > 50         # nada que ver con la media simple


def test_weighted_return_skips_invalid_and_empty():
    assert weighted_portfolio_return([]) is None
    bad = [SimpleNamespace(quantity=Decimal("1"), average_price=Decimal("0"), current_price=Decimal("5"))]
    assert weighted_portfolio_return(bad) is None


def test_keyword_hits_word_boundary():
    keywords = ["bce", "ipc", "euribor"]
    assert keyword_hits("El BCE sube tipos", keywords) == ["bce"]
    assert keyword_hits("informe bceuropeo raro", keywords) == []       # no palabra completa
    assert set(keyword_hits("El IPC interanual y el Euríbor", keywords)) == {"ipc", "euribor"}
