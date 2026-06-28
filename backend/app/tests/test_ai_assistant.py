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
        assert result["ok"] is True
        assert result["tool"] == "my_tool"
        assert result["data"]["value"] == 42
        assert result["quality_score"] == 1.0

    def test_execute_unknown_tool(self):
        import asyncio
        registry = ToolRegistry()
        result = asyncio.run(registry.execute("nonexistent", {}))
        assert result["ok"] is False
        assert "error" in result
        assert result["quality_score"] == 0

    def test_execute_exception_returns_envelope(self):
        import asyncio
        registry = ToolRegistry()

        async def handler(db=None, **kwargs):
            raise RuntimeError("boom")

        registry.register(ToolDefinition("bad_tool", "desc", {}, handler))
        result = asyncio.run(registry.execute("bad_tool", {}))
        assert result["ok"] is False
        assert result["tool"] == "bad_tool"
        assert result["data"] is None
        assert result["sources"] == []


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

        provider = LMStudioProvider("http://localhost:19999", "test-model")
        health = asyncio.run(provider.health())
        assert health.available is False

    def test_bare_base_url_normalizes_to_v1(self):
        from app.modules.ai.providers.lmstudio_provider import LMStudioProvider

        provider = LMStudioProvider("http://127.0.0.1:1234", "test-model")
        assert provider._base_url == "http://127.0.0.1:1234/v1"

    def test_default_model_falls_back_to_loaded_model(self):
        import asyncio

        from app.modules.ai.providers.lmstudio_provider import LMStudioProvider

        provider = LMStudioProvider("http://localhost:1234", "missing-model")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"data": [{"id": "qwen/qwen3.5-9b"}]}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            selected = asyncio.run(provider._model(None))

        assert selected == "qwen/qwen3.5-9b"


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

    def test_lmstudio_manual_tool_call_parser(self):
        import asyncio

        from app.modules.ai.providers.lmstudio_provider import LMStudioProvider

        provider = LMStudioProvider("http://localhost:1234", "test-model")
        models_response = MagicMock()
        models_response.raise_for_status = MagicMock()
        models_response.json.return_value = {"data": [{"id": "test-model"}]}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '```json\n{"tool_call": {"name": "get_macro_snapshot", "arguments": {}}}\n```',
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 6},
        }

        with (
            patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=models_response),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response),
        ):
            response = asyncio.run(provider.chat(
                messages=[{"role": "user", "content": "macro"}],
                tools=[{"name": "get_macro_snapshot", "description": "macro", "input_schema": {"type": "object", "properties": {}}}],
            ))

        assert response.tool_calls[0].name == "get_macro_snapshot"
        assert response.content is None


class TestAiToolsContracts:
    def test_no_legacy_imports_in_ai_tools(self):
        from pathlib import Path

        tools_dir = Path(__file__).resolve().parents[1] / "modules" / "ai" / "tools"
        source = "\n".join(path.read_text(encoding="utf-8") for path in tools_dir.glob("*.py"))
        assert "app.modules.economic_data" not in source
        assert "app.modules.investments.market_data" not in source

    def test_market_tools_registered_with_current_layers(self):
        import app.modules.ai.tools.knowledge_tools  # noqa: F401
        import app.modules.ai.tools.market_tools  # noqa: F401
        from app.modules.ai.tools.registry import tool_registry

        by_name = {tool.name: tool for tool in tool_registry.list_all()}
        assert by_name["get_macro_snapshot"].source_type == "market_intelligence"
        assert by_name["get_market_snapshot"].source_type == "market_intelligence"
        assert by_name["get_forex_snapshot"].source_type == "market_intelligence"
        assert by_name["get_bond_snapshot"].source_type == "market_intelligence"
        assert by_name["get_provider_quality"].source_type == "market_intelligence"
        assert by_name["get_market_regime"].source_type == "financial_knowledge"
        assert by_name["get_ai_datasheet"].source_type == "financial_knowledge"

    def test_envelope_helper_shape(self):
        from app.modules.ai.tools.envelope import ok, source

        result = ok(
            "get_macro_snapshot",
            {"value": 1},
            sources=[source(source_type="market_indicator", provider="FRED", quality_score=0.94)],
        )
        assert result["ok"] is True
        assert result["tool"] == "get_macro_snapshot"
        assert result["data"] == {"value": 1}
        assert result["sources"][0]["provider"] == "FRED"
        assert result["quality_score"] == 0.94
        assert result["warnings"] == []


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
        mock_response = AIResponse(
            content="Tu patrimonio neto es positivo.",
            tool_calls=[],
            model="test-model",
        )

        with patch(
            "app.modules.ai.service.get_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
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
