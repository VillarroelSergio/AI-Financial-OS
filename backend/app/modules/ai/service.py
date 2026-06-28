"""AI assistant service — orchestrates providers, tools and memory."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.ai.memory import conversation_repository as conv_repo
from app.modules.ai.prompts.system_prompt import get_system_prompt
from app.modules.ai.providers import AIProvider, AIResponse, OllamaProvider, LMStudioProvider
from app.modules.ai.schemas import ChatResponse, ConversationOut, ToolCallOut, SourceOut
from app.modules.ai.tools.registry import tool_registry

logger = logging.getLogger(__name__)

# ── Provider registry ─────────────────────────────────────────────────────────

_providers: dict[str, AIProvider] = {}


def _init_providers() -> None:
    _providers["ollama"] = OllamaProvider(
        base_url=settings.OLLAMA_BASE_URL,
        default_model=settings.AI_DEFAULT_MODEL,
    )
    _providers["lmstudio"] = LMStudioProvider(
        base_url=settings.LMSTUDIO_BASE_URL,
        default_model=settings.AI_DEFAULT_MODEL,
    )


_init_providers()


def get_provider(name: str | None = None) -> AIProvider:
    key = name or settings.AI_DEFAULT_PROVIDER
    if key not in _providers:
        raise ValueError(f"Unknown provider: {key}. Available: {list(_providers)}")
    return _providers[key]


def list_providers() -> list[str]:
    return list(_providers.keys())


# ── Chat orchestration ────────────────────────────────────────────────────────

_MAX_TOOL_ROUNDS = 5


async def chat(
    db: Session,
    message: str,
    conversation_id: str | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    enable_tools: bool = True,
) -> ChatResponse:
    if not settings.AI_ASSISTANT_ENABLED:
        raise RuntimeError("AI Assistant is disabled (AI_ASSISTANT_ENABLED=false)")

    # Ensure conversation
    if conversation_id:
        conv = conv_repo.get_conversation(db, conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")
    else:
        conv = conv_repo.create_conversation(db, title=_extract_title(message))
        conversation_id = conv.id

    # Persist user message
    user_msg = conv_repo.add_message(db, conversation_id, "user", message)

    # Build LLM context
    history = conv_repo.get_messages_as_llm_context(db, conversation_id)
    system_prompt = get_system_prompt()
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}] + history

    provider = get_provider(provider_name)
    tools = tool_registry.llm_schemas() if enable_tools else []

    all_tool_calls: list[ToolCallOut] = []
    all_sources: list[dict] = []
    final_content: str | None = None
    overall_quality: float | None = None

    # Agentic loop: call → execute tools → re-call until no more tool calls or limit
    for _round in range(_MAX_TOOL_ROUNDS):
        response: AIResponse = await provider.chat(
            messages=messages,
            tools=tools if enable_tools else None,
            model=model,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )

        if not response.tool_calls:
            final_content = response.content
            break

        # Execute tool calls
        tool_results_for_llm: list[dict] = []
        for tc in response.tool_calls:
            start = time.monotonic()
            result = await tool_registry.execute(tc.name, tc.arguments, db=db)
            duration = int((time.monotonic() - start) * 1000)

            status = "error" if "error" in result else result.get("status", "ok")
            if status == "not_available":
                status = "not_available"
            elif status != "error":
                status = "ok"

            sources = result.pop("sources", []) or []
            quality = result.pop("quality_score", None)
            if quality is not None:
                overall_quality = min(overall_quality, quality) if overall_quality is not None else quality

            tool_call_out = ToolCallOut(
                name=tc.name,
                arguments=tc.arguments,
                result=result,
                duration_ms=duration,
                status=status,
            )
            all_tool_calls.append(tool_call_out)
            all_sources.extend(sources)

            conv_repo.add_tool_call(
                db,
                conversation_id=conversation_id,
                message_id=user_msg.id,
                tool_name=tc.name,
                arguments=tc.arguments,
                result=result,
                sources=sources,
                duration_ms=duration,
                status=status,
            )

            # Format tool result for re-injection
            tool_results_for_llm.append({
                "role": "tool",
                "name": tc.name,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        # Append assistant + tool results to history for next round
        messages.append({"role": "assistant", "content": response.content or ""})
        messages.extend(tool_results_for_llm)

    else:
        # Hit round limit — use last content or synthesize
        final_content = response.content  # type: ignore[possibly-undefined]

    # Deduplicate sources
    seen_sources: set[str] = set()
    unique_sources = []
    for s in all_sources:
        key = json.dumps(s, sort_keys=True)
        if key not in seen_sources:
            seen_sources.add(key)
            unique_sources.append(s)

    # Persist assistant reply
    assistant_msg = conv_repo.add_message(
        db,
        conversation_id,
        "assistant",
        final_content,
        tool_calls=[tc.model_dump() for tc in all_tool_calls],
        sources=unique_sources,
        quality_score=overall_quality,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_msg.id,
        content=final_content,
        tool_calls=all_tool_calls,
        sources=[SourceOut(**s) for s in unique_sources if _valid_source(s)],
        quality_score=overall_quality,
        provider=provider.name,
        model=model or settings.AI_DEFAULT_MODEL,
    )


def _extract_title(message: str) -> str:
    words = message.strip().split()
    return " ".join(words[:8]) + ("..." if len(words) > 8 else "")


def _valid_source(s: dict) -> bool:
    return isinstance(s, dict) and "type" in s
