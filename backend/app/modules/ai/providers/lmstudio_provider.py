"""LM Studio provider — OpenAI-compatible API."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator

import httpx

from app.modules.ai.providers.base import AIResponse, ProviderHealth, ToolCallResult

logger = logging.getLogger(__name__)


class LMStudioProvider:
    """OpenAI-compatible provider targeting LM Studio (or any /v1 endpoint)."""

    def __init__(self, base_url: str, default_model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model

    @property
    def name(self) -> str:
        return "lmstudio"

    def _model(self, model: str | None) -> str:
        return model or self._default_model

    async def _get_loaded_model(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/models")
                r.raise_for_status()
                models = r.json().get("data", [])
                return models[0]["id"] if models else None
        except Exception:
            return None

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
        payload: dict[str, Any] = {
            "model": self._model(model),
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = self._openai_tools(tools)
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()

        logger.debug("LM Studio raw response keys: %s", list(data.keys()))

        choices = data.get("choices")

        if not choices and payload.get("tools"):
            # Retry without tools — model may not support function calling
            logger.warning("LM Studio rejected tools, retrying without them")
            payload.pop("tools", None)
            payload.pop("tool_choice", None)
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp2 = await client.post(f"{self._base_url}/chat/completions", json=payload)
                resp2.raise_for_status()
                data = resp2.json()
            choices = data.get("choices")

        if not choices:
            error_obj = data.get("error", data)
            error_msg = error_obj.get("message", str(error_obj)) if isinstance(error_obj, dict) else str(error_obj)
            logger.error("LM Studio returned no choices. Full response: %s", data)
            raise RuntimeError(f"LM Studio error: {error_msg}")
        choice = choices[0]
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
            tool_calls.append(ToolCallResult(
                name=fn.get("name", ""),
                arguments=args,
                id=tc.get("id", ""),
            ))

        usage = data.get("usage", {})
        return AIResponse(
            content=content or None,
            tool_calls=tool_calls,
            model=self._model(model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self._model(model),
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
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/models")
                resp.raise_for_status()
                latency = int((time.monotonic() - start) * 1000)
                models = [m["id"] for m in resp.json().get("data", [])]
                return ProviderHealth(
                    available=True,
                    provider=self.name,
                    model=models[0] if models else None,
                    latency_ms=latency,
                )
        except Exception as exc:
            return ProviderHealth(available=False, provider=self.name, error=str(exc))

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/models")
                resp.raise_for_status()
                return [m["id"] for m in resp.json().get("data", [])]
        except Exception:
            return []
