"""ECO-2 2b: Eurostat cubre las series ES/EA que INE/BCE/DG-ECFIN no emitían, y el
BCE sirve el Euríbor. Datasets, filtros y unidades verificados contra la API en vivo
(2026-07-06); aquí se mockea la red y se comprueba que fetch(id) devuelve la unidad del
catálogo (y la escala millones→EUR bn), para no reintroducir el bug de unidad de ECO-1.
"""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.europe.ecb import ECBAdapter
from app.modules.market_intelligence.ingestion.adapters.europe.eurostat import EurostatAdapter


def _jsonstat(value: float, period: str = "2026-05"):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "value": {"0": value},
        "id": ["geo", "time"],
        "size": [1, 1],
        "dimension": {"time": {"category": {"index": {period: 0}}}},
    }
    return resp


def _fetch_eurostat(indicator_id: str, value: float, period: str = "2026-05"):
    with patch(
        "app.modules.market_intelligence.ingestion.adapters.europe.eurostat.requests.get",
        return_value=_jsonstat(value, period),
    ):
        return EurostatAdapter().fetch(indicator_id)


def test_gdp_eurozone_scaled_to_eur_bn():
    # 4_023_298.3 millones € → 4023.2983 EUR bn.
    result = _fetch_eurostat("gdp_eurozone", 4_023_298.3, period="2026-Q1")
    assert result.success is True
    rec = result.records[0]
    assert rec.unit == "EUR bn"
    assert round(rec.value, 3) == 4023.298
    assert rec.frequency == "quarterly"


def test_units_and_country_per_series():
    cases = {
        "ipc_subyacente": ("%", "ES", 3.0),
        "produccion_industrial_spain": ("index", "ES", 104.9),
        "industrial_production_eurozone": ("index", "EA", 98.3),
        "deuda_publica_spain": ("% PIB", "ES", 100.7),
        "deficit_spain": ("% PIB", "ES", -4.6),
        "confianza_consumidor_spain": ("index", "ES", -5.3),
        "consumer_confidence_eurozone": ("index", "EA", -17.7),
    }
    for indicator_id, (unit, country, val) in cases.items():
        result = _fetch_eurostat(indicator_id, val)
        assert result.success is True, indicator_id
        rec = result.records[0]
        assert rec.unit == unit, indicator_id
        assert rec.country == country, indicator_id
        assert rec.value == val, indicator_id


def test_eurostat_uses_verified_geo_for_eurozone_confidence():
    # El agregado euro-área de confianza vive en EA21 (EA20 no publica esta celda).
    with patch(
        "app.modules.market_intelligence.ingestion.adapters.europe.eurostat.requests.get",
        return_value=_jsonstat(-17.7, "2026-06"),
    ) as get:
        EurostatAdapter().fetch("consumer_confidence_eurozone")
    assert "geo=EA21" in get.call_args[0][0]


def test_ecb_serves_euribor_3m_and_12m():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = (
        "KEY,FREQ,TIME_PERIOD,OBS_VALUE\n"
        "FM.M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA,M,2026-06,2.339\n"
    )
    for indicator_id in ("euribor_3m", "euribor_12m"):
        with patch(
            "app.modules.market_intelligence.ingestion.adapters.europe.ecb.requests.get",
            return_value=resp,
        ):
            result = ECBAdapter().fetch(indicator_id)
        assert result.success is True, indicator_id
        assert result.records[0].unit == "%", indicator_id
        assert result.records[0].value == 2.339, indicator_id
