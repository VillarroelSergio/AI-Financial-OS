"""Comparativa 'Luz: pool eléctrico vs Casa' (Propuesta ECO-2b) — builder puro, sin BD."""
from app.modules.market_intelligence.api.impact import _MI_EMPTY, _build_comparatives


def _find(comps, cid):
    return next((c for c in comps if c.id == cid), None)


def _mi(**over):
    return {**_MI_EMPTY, **over}


def test_omitted_without_home_spend():
    comps = _build_comparatives({"home_monthly": 0.0}, _mi(pool_electrico=70.0))
    assert _find(comps, "electricity_pool_vs_home") is None


def test_no_data_when_pool_missing():
    comps = _build_comparatives({"home_monthly": 120.0}, _mi(pool_electrico=None))
    c = _find(comps, "electricity_pool_vs_home")
    assert c is not None and c.signal == "no_data"


def test_neutral_when_no_history_yet():
    comps = _build_comparatives({"home_monthly": 120.0}, _mi(pool_electrico=70.0))
    c = _find(comps, "electricity_pool_vs_home")
    assert c.signal == "neutral" and "sin histórico" in c.signal_text


def test_warning_when_pool_up_yoy():
    comps = _build_comparatives(
        {"home_monthly": 120.0}, _mi(pool_electrico=90.0, pool_electrico_year_ago=60.0)
    )  # +50% interanual
    c = _find(comps, "electricity_pool_vs_home")
    assert c.signal == "warning" and c.market_value == 90.0


def test_positive_when_pool_down_yoy():
    comps = _build_comparatives(
        {"home_monthly": 120.0}, _mi(pool_electrico=60.0, pool_electrico_year_ago=90.0)
    )  # -33% interanual
    c = _find(comps, "electricity_pool_vs_home")
    assert c.signal == "positive"


# --- Letras vs tu ahorro (Propuesta ECO-2b) ---

def test_letras_omitted_without_savings_account():
    comps = _build_comparatives({"best_savings_rate": None}, _mi(letras_12m=2.5))
    assert _find(comps, "letras_vs_savings") is None


def test_letras_beat_savings_is_negative_signal():
    comps = _build_comparatives(
        {"best_savings_rate": 1.0, "total_balance": 10000.0}, _mi(letras_12m=2.567)
    )
    c = _find(comps, "letras_vs_savings")
    assert c.signal == "negative" and "Letras 12M rentan más" in c.signal_text


def test_savings_beat_letras_is_positive_signal():
    comps = _build_comparatives({"best_savings_rate": 3.0}, _mi(letras_12m=2.5))
    c = _find(comps, "letras_vs_savings")
    assert c.signal == "positive"


# --- Inflación de tu cesta (Propuesta Nivel-1) ---

def test_basket_omitted_without_classified_spend():
    comps = _build_comparatives(
        {"monthly_expense": 1000.0, "food_home_monthly": 0.0},
        _mi(ipc_general=3.0, ipc_alimentacion=6.0),
    )
    assert _find(comps, "basket_inflation") is None


def test_basket_heavier_on_high_inflation_is_negative():
    # 500€ alimentación al 6% + 500€ resto al 2% → cesta 4% vs IPC 2% → peor que la media.
    comps = _build_comparatives(
        {"monthly_expense": 1000.0, "food_home_monthly": 500.0},
        _mi(ipc_general=2.0, ipc_alimentacion=6.0),
    )
    c = _find(comps, "basket_inflation")
    assert c is not None and c.signal == "negative"
    assert c.personal_value == 4.0 and "te cuesta" in c.signal_text


def test_basket_no_data_without_ipc_general():
    comps = _build_comparatives(
        {"monthly_expense": 1000.0, "food_home_monthly": 500.0},
        _mi(ipc_general=None, ipc_alimentacion=6.0),
    )
    c = _find(comps, "basket_inflation")
    assert c is not None and c.signal == "no_data"
