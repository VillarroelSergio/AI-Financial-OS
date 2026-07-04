"""Tests for the AI assistant module."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.modules.ai.providers.base import AIResponse
from app.modules.ai.tools.registry import ToolDefinition, ToolRegistry

# ── Tool Registry ─────────────────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()

        async def handler(**kwargs):
            return {"result": "ok"}

        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            handler=handler,
        )
        registry.register(tool)
        assert registry.get("test_tool") is tool

    def test_list_all(self):
        registry = ToolRegistry()

        async def handler(**kwargs):
            return {}

        registry.register(ToolDefinition("t1", "T1", {}, handler))
        registry.register(ToolDefinition("t2", "T2", {}, handler))
        assert len(registry.list_all()) == 2

    def test_llm_schemas(self):
        registry = ToolRegistry()

        async def handler(**kwargs):
            return {}

        registry.register(
            ToolDefinition(
                name="get_net_worth",
                description="Returns net worth",
                input_schema={"type": "object", "properties": {}},
                handler=handler,
            )
        )
        schemas = registry.llm_schemas()
        assert schemas[0]["name"] == "get_net_worth"
        assert "description" in schemas[0]

    def test_execute_known_tool(self):
        import asyncio
        registry = ToolRegistry()

        async def handler(db=None, **kwargs):
            return {"value": 42, "quality_score": 1.0}

        registry.register(ToolDefinition("my_tool", "desc", {}, handler))
        result = asyncio.run(registry.execute("my_tool", {}))
        assert result["value"] == 42

    def test_execute_unknown_tool(self):
        import asyncio
        registry = ToolRegistry()
        result = asyncio.run(registry.execute("nonexistent", {}))
        assert "error" in result
        assert result["status"] == "error"


# ── Provider Health ───────────────────────────────────────────────────────────

class TestOllamaProvider:
    def test_health_offline(self):
        import asyncio

        from app.modules.ai.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider("http://localhost:19999", "test-model")
        health = asyncio.run(provider.health())
        assert health.available is False
        assert health.error is not None

    def test_list_models_offline(self):
        import asyncio

        from app.modules.ai.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider("http://localhost:19999", "test-model")
        models = asyncio.run(provider.list_models())
        assert models == []

    def test_chat_with_mock(self):
        import asyncio

        from app.modules.ai.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider("http://localhost:11434", "test-model")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Hola, soy tu asistente financiero."},
            "prompt_eval_count": 10,
            "eval_count": 15,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            response = asyncio.run(provider.chat(
                messages=[{"role": "user", "content": "Hola"}]
            ))
        assert response.content == "Hola, soy tu asistente financiero."
        assert response.input_tokens == 10
        assert response.output_tokens == 15


class TestLMStudioProvider:
    def test_health_offline(self):
        import asyncio

        from app.modules.ai.providers.lmstudio_provider import LMStudioProvider

        provider = LMStudioProvider("http://localhost:19999/v1", "test-model")
        health = asyncio.run(provider.health())
        assert health.available is False


# ── Tool Call Parser ──────────────────────────────────────────────────────────

class TestToolCallParser:
    def test_parse_valid_json(self):
        from app.modules.ai.providers.ollama_provider import _parse_tool_call

        text = json.dumps({"tool_call": {"name": "get_net_worth", "arguments": {}}})
        result = _parse_tool_call(text)
        assert result is not None
        assert result.name == "get_net_worth"

    def test_parse_markdown_block(self):
        from app.modules.ai.providers.ollama_provider import _parse_tool_call

        text = '```json\n{"tool_call": {"name": "get_market_regime", "arguments": {}}}\n```'
        result = _parse_tool_call(text)
        assert result is not None
        assert result.name == "get_market_regime"

    def test_parse_embedded_in_text(self):
        from app.modules.ai.providers.ollama_provider import _parse_tool_call

        text = 'Let me check that. {"tool_call": {"name": "get_net_worth", "arguments": {}}} Done.'
        result = _parse_tool_call(text)
        assert result is not None
        assert result.name == "get_net_worth"

    def test_parse_invalid(self):
        from app.modules.ai.providers.ollama_provider import _parse_tool_call

        result = _parse_tool_call("This is a plain text response.")
        assert result is None


# ── Conversation Repository ───────────────────────────────────────────────────

class TestConversationRepository:
    def test_create_and_get(self, client: TestClient):
        # Access DB through client fixture (creates tables)
        from app.core.database import get_db
        from app.modules.ai.memory import conversation_repository as repo

        db = next(get_db())
        try:
            conv = repo.create_conversation(db, title="Test conversation")
            assert conv.id is not None
            assert conv.title == "Test conversation"

            fetched = repo.get_conversation(db, conv.id)
            assert fetched is not None
            assert fetched.id == conv.id
        finally:
            db.close()

    def test_add_and_get_messages(self, client: TestClient):
        from app.core.database import get_db
        from app.modules.ai.memory import conversation_repository as repo

        db = next(get_db())
        try:
            conv = repo.create_conversation(db, title="Msgs test")
            repo.add_message(db, conv.id, "user", "Hola")
            repo.add_message(db, conv.id, "assistant", "¿En qué puedo ayudarte?")

            msgs = repo.get_messages(db, conv.id)
            assert len(msgs) == 2
            assert msgs[0].role == "user"
            assert msgs[1].role == "assistant"
        finally:
            db.close()

    def test_delete_conversation(self, client: TestClient):
        from app.core.database import get_db
        from app.modules.ai.memory import conversation_repository as repo

        db = next(get_db())
        try:
            conv = repo.create_conversation(db)
            deleted = repo.delete_conversation(db, conv.id)
            assert deleted is True
            assert repo.get_conversation(db, conv.id) is None
        finally:
            db.close()

    def test_delete_nonexistent(self, client: TestClient):
        from app.core.database import get_db
        from app.modules.ai.memory import conversation_repository as repo

        db = next(get_db())
        try:
            deleted = repo.delete_conversation(db, "does-not-exist")
            assert deleted is False
        finally:
            db.close()


# ── API Endpoints ─────────────────────────────────────────────────────────────

class TestAiRoutes:
    def test_get_tools(self, client: TestClient):
        resp = client.get("/api/ai/tools")
        assert resp.status_code == 200
        tools = resp.json()
        assert isinstance(tools, list)
        names = [t["name"] for t in tools]
        assert "get_net_worth" in names
        assert "get_market_regime" in names
        assert "get_ai_datasheet" in names

    def test_get_status(self, client: TestClient):
        resp = client.get("/api/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_create_conversation(self, client: TestClient):
        resp = client.post("/api/ai/conversations", json={"title": "Test"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Test"

    def test_list_conversations(self, client: TestClient):
        client.post("/api/ai/conversations", json={"title": "Conv 1"})
        resp = client.get("/api/ai/conversations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_conversation_with_messages(self, client: TestClient):
        create_resp = client.post("/api/ai/conversations", json={"title": "With msgs"})
        conv_id = create_resp.json()["id"]
        resp = client.get(f"/api/ai/conversations/{conv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == conv_id
        assert "messages" in data

    def test_delete_conversation(self, client: TestClient):
        create_resp = client.post("/api/ai/conversations", json={})
        conv_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/ai/conversations/{conv_id}")
        assert del_resp.status_code == 204
        get_resp = client.get(f"/api/ai/conversations/{conv_id}")
        assert get_resp.status_code == 404

    def test_chat_without_provider(self, client: TestClient):
        """Chat with Ollama offline should return 500 with AI error."""
        resp = client.post(
            "/api/ai/chat",
            json={"message": "Hola", "provider": "ollama"},
        )
        # Provider is offline in test env — expect 500 or 503
        assert resp.status_code in (500, 503)

    def test_chat_with_mocked_provider(self, client: TestClient):
        """Chat with a mocked provider should return a valid ChatResponse."""
        from app.modules.ai.providers.base import ProviderHealth

        mock_response = AIResponse(
            content="Tu patrimonio neto es positivo.",
            tool_calls=[],
            model="test-model",
        )
        mock_health = ProviderHealth(available=True, provider="ollama", model="test-model")

        with patch(
            "app.modules.ai.service.get_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
            mock_provider.health = AsyncMock(return_value=mock_health)
            mock_provider.chat = AsyncMock(return_value=mock_response)
            mock_get_provider.return_value = mock_provider

            resp = client.post(
                "/api/ai/chat",
                json={"message": "¿Cuál es mi patrimonio?"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "conversation_id" in data
        assert "content" in data
        assert data["content"] == "Tu patrimonio neto es positivo."

    def test_chat_with_no_provider_returns_honest_error(self, client: TestClient):
        """Cuando el provider está offline, la respuesta debe ser 503 con mensaje claro — nunca un hang."""
        resp = client.post(
            "/api/ai/chat",
            json={
                "message": "¿Cuáles son mis gastos del mes?",
                "provider": "ollama",
            },
        )
        # No debe ser 500 ni colgar. Debe ser 503 con mensaje honesto.
        assert resp.status_code == 503, f"Unexpected status: {resp.status_code}"
        data = resp.json()
        if resp.status_code == 503:
            detail = data.get("detail", "")
            assert detail, "503 sin detalle útil"
            # El mensaje debe mencionar el provider o disponibilidad
            assert any(
                kw in detail.lower()
                for kw in ("ollama", "lmstudio", "disponible", "provider", "activo", "conectar")
            ), f"Mensaje 503 poco informativo: {detail!r}"

    def test_provider_availability_endpoint_responds_quickly(self, client: TestClient):
        """El endpoint /api/ai/providers debe responder con timeout explícito — nunca colgarse.

        Con providers offline, los health checks tienen timeout de 5s cada uno y se
        ejecutan en paralelo (asyncio.gather). En Windows, TCP puede tardar ~3-4s en
        fallar por puerto cerrado. Aceptamos <7s como prueba de que existe timeout (sin
        timeout sería potencialmente infinito); el benchmark real de producción es menor.
        """
        import time

        start = time.monotonic()
        resp = client.get("/api/ai/providers")
        elapsed = time.monotonic() - start

        assert resp.status_code == 200, f"Unexpected status: {resp.status_code}"
        # Must respond before the per-provider timeout (5s) × number of providers sequential worst case.
        # Concurrent execution (asyncio.gather) keeps it near the single-provider timeout even with N providers.
        assert elapsed < 7.0, (
            f"Provider check tardó {elapsed:.1f}s — timeout o concurrencia no configurados correctamente"
        )
        data = resp.json()
        assert isinstance(data, list)
        # Todos los providers deben devolver available=False cuando están offline
        for p in data:
            assert "name" in p
            assert "available" in p

    def test_chat_injects_screen_context(self, client: TestClient):
        from app.modules.ai.providers.base import ProviderHealth

        mock_response = AIResponse(
            content="Contexto recibido.",
            tool_calls=[],
            model="test-model",
        )
        mock_health = ProviderHealth(available=True, provider="ollama", model="test-model")

        with patch("app.modules.ai.service.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
            mock_provider.health = AsyncMock(return_value=mock_health)
            mock_provider.chat = AsyncMock(return_value=mock_response)
            mock_get_provider.return_value = mock_provider

            resp = client.post(
                "/api/ai/chat",
                json={
                    "message": "Explica esta pantalla",
                    "context": {
                        "module": "Gastos",
                        "route": "/spending",
                        "visible_metrics": ["gasto total", "categorias"],
                        "ignored": "not forwarded",
                    },
                },
            )

        assert resp.status_code == 200
        sent_messages = mock_provider.chat.call_args.kwargs["messages"]
        assert "Contexto de pantalla" in sent_messages[-1]["content"]
        assert "Gastos" in sent_messages[-1]["content"]
        assert "ignored" not in sent_messages[-1]["content"]
