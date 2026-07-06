"""ECO-1: contrato honesto de adapters — cada adapter declara y sirve solo los
catalog ids que realmente cubre, cerrando los 'indicadores clonados' (P1) en origen.

Antes, un adapter multiuso (Eurostat, ECB, OECD, World Bank, BLS) devolvía su serie
por defecto para *cualquier* id pedido y el orquestador lo aceptaba como fallback,
persistiendo el mismo valor bajo varios indicadores. Con allowlist honesta + fetch
parametrizado, un id no soportado se salta (supports()=False) o devuelve vacío.
"""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.europe.ecb import ECBAdapter
from app.modules.market_intelligence.ingestion.adapters.europe.eurostat import EurostatAdapter
from app.modules.market_intelligence.ingestion.adapters.europe.oecd import OECDAdapter
from app.modules.market_intelligence.ingestion.adapters.global_.world_bank import WorldBankAdapter
from app.modules.market_intelligence.ingestion.adapters.usa.bls import BLSAdapter
from app.modules.market_intelligence.ingestion.models import CurrencyRate, MacroIndicator


# ── supports(): allowlist honesta (sin red) ──────────────────────────────────

def test_single_series_adapters_only_support_their_indicator():
    assert BLSAdapter().supports("unemployment_usa") is True
    assert BLSAdapter().supports("cpi_usa") is False  # antes clonaba paro bajo CPI
    assert WorldBankAdapter().supports("pib_spain") is True
    assert WorldBankAdapter().supports("gdp_usa") is False  # antes clonaba PIB ES bajo PIB USA
    assert OECDAdapter().supports("pib_spain") is True
    assert OECDAdapter().supports("ipc_general") is False


def test_ecb_supports_only_its_rates_and_eur_pairs():
    ecb = ECBAdapter()
    assert ecb.supports("tipo_bce") is True
    assert ecb.supports("deposit_facility_eurozone") is True
    assert ecb.supports("eur_usd") is True
    assert ecb.supports("desempleo_spain") is False  # macro que no cubre
    assert ecb.supports("usd_jpy") is False  # no es par base-EUR


def test_eurostat_supports_only_unit_matching_series():
    es = EurostatAdapter()
    assert es.supports("desempleo_spain") is True
    assert es.supports("inflation_eurozone") is True
    # ECO-2: gdp_eurozone ahora se sirve como nivel (CP_MEUR → EUR bn), no QoQ.
    assert es.supports("gdp_eurozone") is True
    assert es.supports("ipc_subyacente") is True
    # pib_spain sigue fuera de Eurostat (lo sirven ine/world_bank/oecd).
    assert es.supports("pib_spain") is False
    assert es.supports("cpi_usa") is False


# ── fetch(id): devuelve solo la serie pedida ─────────────────────────────────

def test_ecb_fetch_unsupported_id_returns_no_records_without_network():
    # No debe llamar a la red ni inventar datos para un id que no sirve.
    with patch("app.modules.market_intelligence.ingestion.adapters.europe.ecb.requests") as req:
        result = ECBAdapter().fetch("desempleo_spain")
    assert result.success is False
    assert result.records == []
    req.get.assert_not_called()


def test_ecb_fetch_forex_returns_only_requested_pair():
    resp = MagicMock()
    resp.text = "KEY,TIME_PERIOD,OBS_VALUE\nX,2026-06-30,1.0850\n"
    resp.raise_for_status = MagicMock()
    with patch("app.modules.market_intelligence.ingestion.adapters.europe.ecb.requests.get", return_value=resp):
        result = ECBAdapter().fetch("eur_usd")
    assert result.success is True
    assert len(result.records) == 1
    rec = result.records[0]
    assert isinstance(rec, CurrencyRate)
    assert rec.quote_currency == "USD"  # solo el par pedido, no los 7


def test_eurostat_fetch_unsupported_id_returns_no_records_without_network():
    with patch("app.modules.market_intelligence.ingestion.adapters.europe.eurostat.requests") as req:
        result = EurostatAdapter().fetch("pib_spain")
    assert result.success is False
    assert result.records == []
    req.get.assert_not_called()


def test_eurostat_fetch_uses_spain_geo_for_es_indicator():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "value": {"0": 12.3},
        "id": ["geo", "time"],
        "size": [1, 1],
        "dimension": {"time": {"category": {"index": {"2026-05": 0}}}},
    }
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        return resp

    with patch("app.modules.market_intelligence.ingestion.adapters.europe.eurostat.requests.get", side_effect=fake_get):
        result = EurostatAdapter().fetch("desempleo_spain")

    assert result.success is True
    assert "geo=ES" in captured["url"]
    assert all(isinstance(r, MacroIndicator) for r in result.records)
    assert result.records[0].value == 12.3
