"""ECO-3 A3: `period` se canoniza en escritura (YYYY-MM / YYYY-Qn / YYYY).

Cubre el validador puro y la causa raíz de FRED (columna `observation_date`), que dejaba
`period` vacío y obligaba a parches defensivos en lectura.
"""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.usa.fred import FREDAdapter
from app.modules.market_intelligence.storage.repository import normalize_period


def test_normalize_period_canonical_forms():
    assert normalize_period("2026-05", "monthly") == "2026-05"
    assert normalize_period("2026-05-01", "monthly") == "2026-05"      # FRED mensual
    assert normalize_period("2026-01-01", "quarterly") == "2026-Q1"    # FRED GDP trimestral
    assert normalize_period("2026-04-15", "quarterly") == "2026-Q2"
    assert normalize_period("2026-Q1", "quarterly") == "2026-Q1"       # Eurostat ya canónico
    assert normalize_period("2026-q3", "quarterly") == "2026-Q3"
    assert normalize_period("2026M05", "monthly") == "2026-05"         # Eurostat 'YYYYMnn'
    assert normalize_period("2020-12-31", "annual") == "2020"
    assert normalize_period("2026-06-30", "daily") == "2026-06-30"     # diario conserva día


def test_normalize_period_edge_cases():
    assert normalize_period("", "monthly") == ""
    assert normalize_period(None, "monthly") == ""
    assert normalize_period("no-es-fecha", "monthly") == "no-es-fecha"  # no destruye lo desconocido


def test_normalize_period_idempotent():
    for p, f in [("2026-05-01", "monthly"), ("2026-01-01", "quarterly"), ("2020-12-31", "annual")]:
        once = normalize_period(p, f)
        assert normalize_period(once, f) == once


def test_fred_populates_period_from_observation_date():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = "observation_date,GDP\n2026-01-01,31865.721\n"
    with patch(
        "app.modules.market_intelligence.ingestion.adapters.usa.fred.requests.get",
        return_value=resp,
    ):
        result = FREDAdapter().fetch("gdp_usa")
    assert result.success is True
    # Antes: period="" (leía 'DATE'). Ahora sale poblado y el repository lo canoniza a 2026-Q1.
    assert result.records[0].period == "2026-01-01"
