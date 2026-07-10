"""REE adapter: allowlist + agregación mensual del pool spot sin red."""
from datetime import date
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.spain.ree import (
    REEAdapter,
    _prev_month_range,
)


def test_supports_only_pool_indicator():
    ree = REEAdapter()
    assert ree.supports("precio_electricidad_spain") is True
    assert ree.supports("desempleo_spain") is False


def test_prev_month_range_wraps_january():
    assert _prev_month_range(date(2026, 7, 6)) == (date(2026, 6, 1), date(2026, 6, 30))
    assert _prev_month_range(date(2026, 1, 15)) == (date(2025, 12, 1), date(2025, 12, 31))


def _fake_response():
    # dos series como la API real: PVPC (regulado) y spot (pool). Debe promediar solo el spot.
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"included": [
        {"attributes": {"title": "PVPC", "values": [{"value": 200.0}, {"value": 220.0}]}},
        {"attributes": {"title": "Precio mercado spot", "values": [
            {"value": 60.0}, {"value": 70.0}, {"value": 80.0}, {"value": None}]}},
    ]}
    return resp


def test_fetch_averages_spot_not_pvpc():
    with patch("app.modules.market_intelligence.ingestion.adapters.spain.ree.requests.get",
               return_value=_fake_response()), \
         patch("app.modules.market_intelligence.ingestion.adapters.spain.ree.date") as mock_date:
        mock_date.today.return_value = date(2026, 7, 6)
        mock_date.side_effect = lambda *a, **k: date(*a, **k)
        rec = REEAdapter().fetch("precio_electricidad_spain").records[0]
    assert rec.value == 70.0  # media de spot (60,70,80), ignora PVPC y None
    assert rec.unit == "€/MWh"
    assert rec.period == "2026-06"
    assert rec.frequency == "monthly"
    assert rec.indicator_id == "precio_electricidad_spain"


def test_fetch_rejects_unsupported_indicator():
    result = REEAdapter().fetch("desempleo_spain")
    assert result.success is False
    assert "no sirve" in (result.error or "")
