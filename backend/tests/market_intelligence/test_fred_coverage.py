"""ECO-2: FRED cubre las series USA que BLS/BEA/Census no emiten.

Series y unidades verificadas contra fredgraph.csv en vivo (2026-07-06). Aquí se
mockea la red y se comprueba que fetch(id) devuelve la unidad correcta del catálogo
(clave para no reintroducir el bug de unidad equivocada que cerró ECO-1).
"""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter


def _csv_response(header_col: str, value: str, period: str = "2026-05-01"):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = f"observation_date,{header_col}\n{period},{value}\n"
    return resp


def _fetch(indicator_id: str, header_col: str, value: str, period: str = "2026-05-01"):
    with patch(
        "app.modules.market_intelligence.ingestion.adapters.usa.fred.requests.get",
        return_value=_csv_response(header_col, value, period),
    ):
        return FREDAdapter().fetch(indicator_id)


def test_cpi_usa_is_percent_yoy():
    result = _fetch("cpi_usa", "CPIAUCSL_PC1", "4.16661")
    assert result.success is True
    assert result.records[0].unit == "%"
    assert result.records[0].value == 4.16661


def test_core_cpi_usa_is_percent_yoy():
    result = _fetch("core_cpi_usa", "CPILFESL_PC1", "3.5")
    assert result.success is True
    assert result.records[0].unit == "%"


def test_gdp_usa_is_usd_bn_quarterly():
    result = _fetch("gdp_usa", "GDP", "31865.721", period="2026-01-01")
    assert result.success is True
    rec = result.records[0]
    assert rec.unit == "USD bn"
    assert rec.frequency == "quarterly"
    assert rec.value == 31865.721


def test_units_for_remaining_series():
    cases = {
        "nfp_usa": ("PAYEMS", "158984", "thousands"),
        "retail_sales_usa": ("RSAFS", "763705", "USD mn"),
        "housing_starts_usa": ("HOUST", "1177", "thousands"),
    }
    for indicator_id, (col, val, unit) in cases.items():
        result = _fetch(indicator_id, col, val)
        assert result.success is True, indicator_id
        assert result.records[0].unit == unit, indicator_id
