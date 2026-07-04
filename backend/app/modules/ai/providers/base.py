"""Abstract base for all AI providers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol


@dataclass
class ToolCallResult:
    name: str
    arguments: dict[str, Any]
    id: str = ""  # tool_call_id for OpenAI-compatible round-tripping


@dataclass
class AIResponse:
    content: str | None
    tool_calls: list[ToolCallResult] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"


@dataclass
class ProviderHealth:
    available: bool
    provider: str
    model: str | None = None
    error: str | None = None
    latency_ms: int | None = None


class AIProvider(Protocol):
    """Structural interface implemented by OllamaProvider and LMStudioProvider."""

    @property
    def name(self) -> str: ...

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AIResponse: ...

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]: ...

    async def health(self) -> ProviderHealth: ...

    async def list_models(self) -> list[str]: ...
