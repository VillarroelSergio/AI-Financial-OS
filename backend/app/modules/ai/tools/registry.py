"""Central tool registry — all AI-callable tools are registered here."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

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
            return {"error": f"Unknown tool: {name}", "status": "error"}
        try:
            result = await tool.handler(db=db, **arguments)
            return result
        except Exception as exc:
            logger.exception("Tool %s failed: %s", name, exc)
            return {"error": str(exc), "status": "error"}


tool_registry = ToolRegistry()
