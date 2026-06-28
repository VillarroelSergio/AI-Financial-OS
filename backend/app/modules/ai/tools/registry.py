"""Central tool registry — all AI-callable tools are registered here."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Awaitable[dict[str, Any]]]
    returns_sources: bool = True
    required_permissions: list[str] = field(default_factory=list)
    source_type: str = "internal"

    def to_llm_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_all(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def llm_schemas(self) -> list[dict[str, Any]]:
        return [t.to_llm_schema() for t in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        db: Any = None,
    ) -> dict[str, Any]:
        tool = self.get(name)
        if tool is None:
            return _error_envelope(name, f"Unknown tool: {name}")
        try:
            result = await tool.handler(db=db, **arguments)
            return _normalize_result(name, result)
        except Exception as exc:
            logger.exception("Tool %s failed: %s", name, exc)
            return _error_envelope(name, str(exc))


tool_registry = ToolRegistry()


def _error_envelope(name: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": name,
        "data": None,
        "sources": [],
        "quality_score": 0,
        "warnings": [error],
        "error": error,
    }


def _normalize_result(name: str, result: dict[str, Any]) -> dict[str, Any]:
    if {"ok", "tool", "data", "sources", "quality_score", "warnings"}.issubset(result):
        return result
    if "error" in result or result.get("status") == "error":
        return _error_envelope(name, str(result.get("error") or "tool failed"))
    sources = result.get("sources", []) or []
    quality = result.get("quality_score", 1.0)
    data = {k: v for k, v in result.items() if k not in {"sources", "quality_score", "warnings"}}
    return {
        "ok": True,
        "tool": name,
        "data": data,
        "sources": sources,
        "quality_score": quality,
        "warnings": result.get("warnings", []) or [],
    }
