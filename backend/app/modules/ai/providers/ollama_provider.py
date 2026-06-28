"""Ollama local AI provider."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator

import httpx

from app.modules.ai.providers.base import AIProvider, AIResponse, ProviderHealth, ToolCallResult

logger = logging.getLogger(__name__)

TOOL_CALL_PROMPT = """
When you need to call a tool, respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{"tool_call": {"name": "<tool_name>", "arguments": {<args>}}}

Available tools:
"""


def parse_tool_call(text: str) -> ToolCallResult | None:
    """Extract tool_call from model output — handles JSON, markdown blocks, and inline."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
        if "tool_call" in data:
            tc = data["tool_call"]
            return ToolCallResult(name=tc["name"], arguments=tc.get("arguments", {}))
    except (json.JSONDecodeError, KeyError):
        pass

    # Try finding JSON object in longer text
    start = text.find('{"tool_call"')
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[start : i + 1])
                        if "tool_call" in data:
                            tc = data["tool_call"]
                            return ToolCallResult(name=tc["name"], arguments=tc.get("arguments", {}))
                    except (json.JSONDecodeError, KeyError):
                        break
    return None


_parse_tool_call = parse_tool_call


def _build_tool_system_suffix(tools: list[dict[str, Any]]) -> str:
    lines = [TOOL_CALL_PROMPT]
    for t in tools:
        lines.append(f"- {t['name']}: {t.get('description', '')}")
        schema = t.get("input_schema") or t.get("parameters", {})
        if schema.get("properties"):
            lines.append(f"  Parameters: {json.dumps(schema['properties'])}")
    return "\n".join(lines)


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, default_model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model

    @property
    def name(self) -> str:
        return "ollama"

    def _model(self, model: str | None) -> str:
        return model or self._default_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AIResponse:
        msgs = list(messages)
        if tools:
            # Inject tool instructions into system message
            suffix = _build_tool_system_suffix(tools)
            if msgs and msgs[0]["role"] == "system":
                msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n\n" + suffix}
            else:
                msgs.insert(0, {"role": "system", "content": suffix})

        payload: dict[str, Any] = {
            "model": self._model(model),
            "messages": msgs,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        msg = data.get("message", {})
        content = msg.get("content", "")
        tool_calls: list[ToolCallResult] = []

        # Native Ollama tool_calls field
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append(ToolCallResult(name=fn.get("name", ""), arguments=args))
        elif tools and content:
            parsed = parse_tool_call(content)
            if parsed:
                tool_calls.append(parsed)
                content = None  # content replaced by tool call

        return AIResponse(
            content=content,
            tool_calls=tool_calls,
            model=self._model(model),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            finish_reason="tool_calls" if tool_calls else "stop",
        )

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        msgs = list(messages)
        if tools:
            suffix = _build_tool_system_suffix(tools)
            if msgs and msgs[0]["role"] == "system":
                msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n\n" + suffix}
            else:
                msgs.insert(0, {"role": "system", "content": suffix})

        payload: dict[str, Any] = {
            "model": self._model(model),
            "messages": msgs,
            "stream": True,
            "options": {"num_predict": max_tokens},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue

    async def health(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                latency = int((time.monotonic() - start) * 1000)
                model_available = any(self._default_model in m for m in models)
                return ProviderHealth(
                    available=True,
                    provider=self.name,
                    model=self._default_model if model_available else None,
                    latency_ms=latency,
                    error=None if model_available else f"Model '{self._default_model}' not found. Available: {', '.join(models[:5])}",
                )
        except Exception as exc:
            return ProviderHealth(available=False, provider=self.name, error=str(exc))

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
