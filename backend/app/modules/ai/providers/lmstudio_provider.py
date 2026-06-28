"""LM Studio provider — OpenAI-compatible API."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator

import httpx

from app.modules.ai.providers.base import AIProvider, AIResponse, ProviderHealth, ToolCallResult
from app.modules.ai.providers.ollama_provider import _build_tool_system_suffix, parse_tool_call

logger = logging.getLogger(__name__)


class LMStudioProvider(AIProvider):
    """OpenAI-compatible provider targeting LM Studio (or any /v1 endpoint)."""

    def __init__(self, base_url: str, default_model: str) -> None:
        self._base_url = self._normalize_base_url(base_url)
        self._default_model = default_model
        self._models_cache: list[str] | None = None

    @property
    def name(self) -> str:
        return "lmstudio"

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        clean = base_url.rstrip("/")
        return clean if clean.endswith("/v1") else f"{clean}/v1"

    async def _models(self) -> list[str]:
        if self._models_cache is not None:
            return self._models_cache
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self._base_url}/models")
            resp.raise_for_status()
            self._models_cache = [m["id"] for m in resp.json().get("data", []) if m.get("id")]
            return self._models_cache

    async def _model(self, model: str | None) -> str:
        if model:
            return model
        models = await self._models()
        if self._default_model in models:
            return self._default_model
        if models:
            return models[0]
        return self._default_model

    def _openai_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or t.get("parameters") or {"type": "object", "properties": {}},
                },
            }
            for t in tools
        ]

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AIResponse:
        resolved_model = await self._model(model)
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = self._openai_tools(tools)
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(f"{self._base_url}/chat/completions", json=payload)
            except httpx.HTTPError:
                raise
            if resp.status_code >= 400 and tools:
                fallback = dict(payload)
                fallback.pop("tools", None)
                fallback.pop("tool_choice", None)
                fallback["messages"] = self._messages_with_manual_tools(messages, tools)
                resp = await client.post(f"{self._base_url}/chat/completions", json=fallback)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        msg = choice["message"]
        content = msg.get("content") or ""
        tool_calls: list[ToolCallResult] = []

        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(ToolCallResult(name=fn.get("name", ""), arguments=args))
        if tools and not tool_calls and content:
            parsed = parse_tool_call(content)
            if parsed:
                tool_calls.append(parsed)
                content = ""
        finish_reason = choice.get("finish_reason", "stop")
        if not content and not tool_calls and finish_reason == "length":
            content = (
                "LM Studio devolvio solo razonamiento interno y agoto el limite de tokens "
                "antes de generar respuesta. Aumenta AI_MAX_OUTPUT_TOKENS o usa un modelo sin reasoning."
            )

        usage = data.get("usage", {})
        return AIResponse(
            content=content or None,
            tool_calls=tool_calls,
            model=resolved_model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=finish_reason,
        )

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        resolved_model = await self._model(model)
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self._base_url}/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:]
                    if raw.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        delta = chunk["choices"][0].get("delta", {}).get("content") or ""
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def health(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            models = await self._models()
            latency = int((time.monotonic() - start) * 1000)
            selected = self._default_model if self._default_model in models else (models[0] if models else None)
            return ProviderHealth(
                available=bool(selected),
                provider=self.name,
                model=selected,
                latency_ms=latency,
                error=None if selected else "No models loaded in LM Studio",
            )
        except Exception as exc:
            return ProviderHealth(available=False, provider=self.name, error=str(exc))

    async def list_models(self) -> list[str]:
        try:
            return await self._models()
        except Exception:
            return []

    def _messages_with_manual_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        suffix = _build_tool_system_suffix(tools)
        msgs = list(messages)
        if msgs and msgs[0]["role"] == "system":
            msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n\n" + suffix}
        else:
            msgs.insert(0, {"role": "system", "content": suffix})
        return msgs
