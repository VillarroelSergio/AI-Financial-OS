"""Extracción de posiciones desde captura con modelo de visión local (mockeado)."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.investments.portfolio_import_service import extract_positions_from_image

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def _provider(content: str, available: bool = True):
    provider = MagicMock()
    provider.name = "ollama"
    provider.health = AsyncMock(return_value=MagicMock(available=available, error=None))
    provider.chat = AsyncMock(return_value=MagicMock(content=content))
    return provider


@pytest.mark.anyio
async def test_extract_parses_model_json():
    content = '```json\n[{"name": "Iberdrola", "quantity": 5, "current_value": 107.6, "currency": "EUR", "return_pct": 2.1}]\n```'
    with patch("app.modules.ai.service.get_provider", return_value=_provider(content)):
        positions = await extract_positions_from_image("b64data", "image/png")
    assert len(positions) == 1
    assert positions[0].raw_name == "Iberdrola"
    assert positions[0].quantity == 5
    assert positions[0].current_value_currency == "EUR"


@pytest.mark.anyio
async def test_extract_raises_when_provider_offline():
    with patch("app.modules.ai.service.get_provider", return_value=_provider("", available=False)):
        with pytest.raises(RuntimeError, match="no está disponible"):
            await extract_positions_from_image("b64data", "image/png")


@pytest.mark.anyio
async def test_extract_raises_on_non_json_response():
    with patch("app.modules.ai.service.get_provider", return_value=_provider("No veo ninguna imagen.")):
        with pytest.raises(RuntimeError, match="visión"):
            await extract_positions_from_image("b64data", "image/png")


def test_parse_image_endpoint_rejects_non_image(client):
    r = client.post(
        "/api/investments/import/parse-image",
        files={"file": ("datos.txt", io.BytesIO(b"hola"), "text/plain")},
    )
    assert r.status_code == 422


def test_parse_image_endpoint_returns_positions(client):
    content = '[{"name": "Apple", "quantity": 1, "current_value": 250.0, "currency": "USD", "return_pct": null}]'
    with patch("app.modules.ai.service.get_provider", return_value=_provider(content)):
        r = client.post(
            "/api/investments/import/parse-image",
            files={"file": ("captura.png", io.BytesIO(PNG), "image/png")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body[0]["raw_name"] == "Apple"
    assert body[0]["current_value_currency"] == "USD"


def test_parse_image_endpoint_503_when_offline(client):
    with patch("app.modules.ai.service.get_provider", return_value=_provider("", available=False)):
        r = client.post(
            "/api/investments/import/parse-image",
            files={"file": ("captura.png", io.BytesIO(PNG), "image/png")},
        )
    assert r.status_code == 503
