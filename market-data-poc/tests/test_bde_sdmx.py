from unittest.mock import patch, Mock
from adapters.spain.bde import BDEAdapter


def _mock_sdmx_response(indicator_id: str):
    """Simula una respuesta SDMX exitosa del BDE."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = Mock()
    # Simular respuesta JSON SDMX mínima
    mock_resp.json.return_value = {
        "dataSets": [{
            "series": {
                "0:0:0": {
                    "observations": {
                        "0": [3.5, 0, None],
                        "1": [3.4, 0, None],
                    }
                }
            }
        }],
        "structure": {
            "dimensions": {
                "observation": [{"values": [{"id": "2024-01"}, {"id": "2024-02"}]}]
            }
        }
    }
    return mock_resp


def test_bde_supports_euribor_3m():
    adapter = BDEAdapter()
    assert adapter.supports("euribor_3m") is True


def test_bde_supports_euribor_12m():
    adapter = BDEAdapter()
    assert adapter.supports("euribor_12m") is True


def test_bde_supports_spain_10y():
    adapter = BDEAdapter()
    assert adapter.supports("spain_10y") is True


def test_bde_does_not_support_unknown():
    adapter = BDEAdapter()
    assert adapter.supports("cpi_usa") is False


def test_bde_fetch_without_indicator_uses_legacy():
    adapter = BDEAdapter()
    with patch("adapters.spain.bde.requests.head") as mock_head, \
         patch("adapters.spain.bde.requests.get") as mock_get:
        mock_head.return_value = Mock(status_code=200)
        mock_get.return_value = Mock(
            status_code=200,
            text="date;value\n2024-01;3.5\n",
            raise_for_status=Mock(),
        )
        result = adapter.fetch(indicator_id=None)
    assert result is not None
    assert result.provider == "Banco de España"


def test_bde_fetch_with_unsupported_indicator_uses_legacy():
    adapter = BDEAdapter()
    with patch("adapters.spain.bde.requests.head") as mock_head, \
         patch("adapters.spain.bde.requests.get") as mock_get:
        mock_head.return_value = Mock(status_code=200)
        mock_get.return_value = Mock(
            status_code=200,
            text="date;value\n2024-01;3.5\n",
            raise_for_status=Mock(),
        )
        result = adapter.fetch(indicator_id="cpi_usa")
    assert result is not None
