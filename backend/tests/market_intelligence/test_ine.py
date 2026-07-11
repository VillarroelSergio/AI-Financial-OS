"""INE adapter: allowlist + parseo Tempus3 sin red."""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.spain.ine import (
    INEAdapter,
    _period_label,
)


def test_supports_only_verified_series():
    ine = INEAdapter()
    assert ine.supports("ipc_general") is True
    assert ine.supports("ipc_alimentacion") is True
    assert ine.supports("ipc_vivienda") is True
    assert ine.supports("desempleo_spain") is True
    assert ine.supports("pib_spain") is True
    assert ine.supports("ipv_spain") is True
    assert ine.supports("coste_laboral_spain") is True
    assert ine.supports("comercio_minorista_spain") is True
    assert ine.supports("hipotecas_numero_spain") is True
    assert ine.supports("hipotecas_importe_spain") is True
    assert ine.supports("deuda_publica_spain") is False  # sin verificar → fuera


def test_importe_scaled_thousands_to_billions():
    # HPT34671 viene en miles€ (10.325.574) → ×1e-6 = EUR bn (10.33).
    items = [{"Anyo": 2026, "FK_Periodo": 3, "Valor": 10325574.0, "Fecha": 1774994400000}]
    with patch("app.modules.market_intelligence.ingestion.adapters.spain.ine.requests.get",
               return_value=_fake_response(items)):
        rec = INEAdapter().fetch("hipotecas_importe_spain").records[-1]
    assert round(rec.value, 3) == 10.326
    assert rec.unit == "EUR bn"


def test_period_label_from_fecha_absorbs_madrid_utc_offset():
    # Fecha viene a las 00:00 hora Madrid → 2021-11-30 23:00 UTC; el nudge de +12h
    # evita que caiga en noviembre. IPC dic-2021 = COD IPC206449, Fecha real.
    dec_2021 = {"Fecha": 1638313200000, "Anyo": 2021, "FK_Periodo": 12}
    assert _period_label(dec_2021, "monthly") == "2021-12"
    # Q2 2023 (1-abr = inicio de trimestre) → canónico YYYY-Qn (con "Q", no "T")
    q2_2023 = {"Fecha": 1680300000000, "Anyo": 2023, "FK_Periodo": 22}
    assert _period_label(q2_2023, "quarterly") == "2023-Q2"
    # sin Fecha → fallback crudo Anyo-FK_Periodo
    assert _period_label({"Anyo": 2020, "FK_Periodo": 9}, "monthly") == "2020-9"


def test_pib_scaled_millions_to_billions():
    items = [{"Anyo": 2026, "FK_Periodo": 19, "Valor": 437288.0, "Fecha": 1735689600000}]
    with patch("app.modules.market_intelligence.ingestion.adapters.spain.ine.requests.get",
               return_value=_fake_response(items)):
        result = INEAdapter().fetch("pib_spain")
    rec = result.records[0]
    assert rec.value == 437.288  # millones € → EUR bn
    assert rec.unit == "EUR bn"
    assert rec.frequency == "quarterly"


def _fake_response(items):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"Data": items}
    return resp


def test_fetch_parses_quarterly_unemployment_with_unit_and_period():
    items = [{"Anyo": 2023, "FK_Periodo": 22, "Valor": 11.76, "Fecha": 1680300000000}]
    with patch("app.modules.market_intelligence.ingestion.adapters.spain.ine.requests.get",
               return_value=_fake_response(items)):
        result = INEAdapter().fetch("desempleo_spain")
    assert result.success is True
    rec = result.records[0]
    assert rec.value == 11.76
    assert rec.unit == "%"
    assert rec.period == "2023-Q2"
    assert rec.frequency == "quarterly"
    assert rec.indicator_id == "desempleo_spain"


def test_fetch_rejects_unsupported_indicator():
    result = INEAdapter().fetch("deuda_publica_spain")
    assert result.success is False
    assert "no sirve" in (result.error or "")
