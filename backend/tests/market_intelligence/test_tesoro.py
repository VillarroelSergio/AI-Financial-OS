"""Tesoro adapter: allowlist + parseo de la tabla de subastas sin red."""
from unittest.mock import MagicMock, patch

from app.modules.market_intelligence.ingestion.adapters.spain.tesoro import (
    TesoroAdapter,
    _select_column,
)

# Estructura real (Drupal views): th scope=row = etiqueta, columnas = subastas.
_LETRAS_HTML = """
<table><tbody>
<tr><th scope="row">Plazo</th><td>3 MESES</td><td>12 MESES</td></tr>
<tr><th scope="row">Fecha subasta</th><td>09/06/2026</td><td>02/06/2026</td></tr>
<tr><th scope="row">Tipo de interés marginal</th><td>2,244</td><td>2,567</td></tr>
<tr><th scope="row">Anterior tipo marginal</th><td>2,163</td><td>2,651</td></tr>
</tbody></table>
""".encode("utf-8")

# Bonos: plazo rotativo; la última subasta es la de fecha máxima (05 años, 02/07).
_BONOS_HTML = """
<table><tbody>
<tr><th scope="row">Plazo</th><td>3 AÑOS</td><td>5 AÑOS</td></tr>
<tr><th scope="row">Fecha subasta</th><td>04/06/2026</td><td>02/07/2026</td></tr>
<tr><th scope="row">Tipo de interés marginal</th><td>2,775</td><td>2,840</td></tr>
</tbody></table>
""".encode("utf-8")


def _resp(body: bytes):
    r = MagicMock()
    r.raise_for_status.return_value = None
    r.content = body
    r.status_code = 200
    return r


def test_supports_allowlist():
    a = TesoroAdapter()
    assert a.supports("letras_12m") is True
    assert a.supports("bono_estado_subasta") is True
    assert a.supports("deuda_publica_spain") is False


def test_letras_selected_by_maturity():
    col = _select_column(_LETRAS_HTML, 3)
    assert col["marginal"] == 2.244 and col["plazo"] == "3 meses" and col["period"] == "2026-06"
    assert _select_column(_LETRAS_HTML, 12)["marginal"] == 2.567


def test_ignores_anterior_marginal_row():
    # No debe coger "Anterior tipo marginal" (2,163) sino el marginal actual (2,244).
    assert _select_column(_LETRAS_HTML, 3)["marginal"] == 2.244


def test_bonos_picks_latest_auction_by_date():
    col = _select_column(_BONOS_HTML, None)  # última = 5 años, 02/07
    assert col["marginal"] == 2.840 and col["plazo"] == "5 años" and col["period"] == "2026-07"


def test_fetch_maps_id_and_rejects_unknown():
    with patch("app.modules.market_intelligence.ingestion.adapters.spain.tesoro.requests.get",
               return_value=_resp(_LETRAS_HTML)):
        rec = TesoroAdapter().fetch("letras_3m").records[0]
    assert rec.indicator_id == "letras_3m" and rec.value == 2.244 and rec.unit == "%"

    bad = TesoroAdapter().fetch("xxx")
    assert bad.success is False and "no sirve" in (bad.error or "")
