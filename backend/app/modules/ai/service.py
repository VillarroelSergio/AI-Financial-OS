"""AI assistant service — orchestrates providers, tools and memory."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.ai.memory import conversation_repository as conv_repo
from app.modules.ai.prompts.system_prompt import get_system_prompt
from app.modules.ai.providers import AIProvider, AIResponse, LMStudioProvider, OllamaProvider
from app.modules.ai.schemas import ChatResponse, SourceOut, ToolCallOut
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
    context: dict[str, Any] | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    enable_tools: bool = True,
) -> ChatResponse:
    if not settings.AI_ASSISTANT_ENABLED:
        raise RuntimeError("AI Assistant is disabled (AI_ASSISTANT_ENABLED=false)")

    # Ensure conversation
    new_conversation = False
    if conversation_id:
        conv = conv_repo.get_conversation(db, conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")
    else:
        conv = conv_repo.create_conversation(db, title=_extract_title(message))
        conversation_id = conv.id
        new_conversation = True

    contextual_message = _with_screen_context(message, context)

    # Persist user message
    user_msg = conv_repo.add_message(db, conversation_id, "user", message)

    # Build LLM context
    history = conv_repo.get_messages_as_llm_context(db, conversation_id)
    system_prompt = get_system_prompt()
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}] + history
    if context:
        messages[-1] = {"role": "user", "content": contextual_message}

    provider = get_provider(provider_name)

    # Fast availability check before entering the agentic loop.
    # health() has a 5-second timeout internally, so this won't block long.
    try:
        health = await provider.health()
        if not health.available:
            error_detail = health.error or "provider offline"
            raise RuntimeError(
                f"El asistente IA no está disponible ({provider.name}): {error_detail}. "
                "Asegúrate de que Ollama o LMStudio está en ejecución."
            )
    except (httpx.TransportError, httpx.TimeoutException) as exc:
        raise RuntimeError(
            f"No se puede conectar con el provider '{provider.name}'. "
            f"Comprueba que el servicio está activo. Detalle: {exc}"
        ) from exc

    tools = tool_registry.llm_schemas() if enable_tools else []

    all_tool_calls: list[ToolCallOut] = []
    all_sources: list[dict] = []
    final_content: str | None = None
    overall_quality: float | None = None
    seen_call_signatures: set[str] = set()

    # Agentic loop: call → execute tools → re-call until no more tool calls or limit
    for _round in range(_MAX_TOOL_ROUNDS):
        try:
            response: AIResponse = await provider.chat(
                messages=messages,
                tools=tools if enable_tools else None,
                model=model,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise RuntimeError(
                f"El provider '{provider.name}' no respondió a tiempo. "
                f"Comprueba que el modelo está cargado y el servicio está activo. Detalle: {exc}"
            ) from exc

        if not response.tool_calls:
            final_content = response.content
            break

        # Detect repeated tool calls — break early to avoid infinite same-call cycle
        call_sigs = frozenset(
            f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}"
            for tc in response.tool_calls
        )
        if call_sigs & seen_call_signatures:
            logger.warning("Tool call loop detected (repeated: %s) — forcing synthesis", call_sigs & seen_call_signatures)
            messages.append({
                "role": "user",
                "content": "Ya tienes todos los datos necesarios. Responde ahora en texto claro y conciso sin más llamadas a herramientas.",
            })
            try:
                synth: AIResponse = await provider.chat(
                    messages=messages, tools=None, model=model, max_tokens=settings.AI_MAX_OUTPUT_TOKENS
                )
                final_content = synth.content or ""
            except Exception:
                final_content = ""
            break
        seen_call_signatures |= call_sigs

        # Execute tool calls
        tool_results_for_llm: list[dict] = []
        for i, tc in enumerate(response.tool_calls):
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

            # Include tool_call_id so OpenAI-compatible models associate results with calls
            call_id = tc.id or f"call_{_round}_{i}"
            tool_results_for_llm.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": tc.name,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        # Re-inject assistant message WITH tool_calls array (required by OpenAI-compatible APIs)
        assistant_tool_calls_fmt = [
            {
                "id": tc.id or f"call_{_round}_{i}",
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            }
            for i, tc in enumerate(response.tool_calls)
        ]
        messages.append({
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": assistant_tool_calls_fmt,
        })
        messages.extend(tool_results_for_llm)

    else:
        # Exhausted rounds — force one text-only synthesis call instead of returning empty
        messages.append({
            "role": "user",
            "content": "Con los datos que has obtenido, responde al usuario en texto claro y conciso. No hagas más llamadas a herramientas.",
        })
        try:
            synth_final: AIResponse = await provider.chat(
                messages=messages, tools=None, model=model, max_tokens=settings.AI_MAX_OUTPUT_TOKENS
            )
            final_content = synth_final.content or "He analizado tus datos financieros. Reformula tu pregunta para obtener más detalle."
        except Exception:
            final_content = "He ejecutado el análisis pero no pude generar una respuesta. Inténtalo de nuevo."

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

    # Auto-título: un saludo trivial ("hola") produce títulos repetidos e inútiles;
    # en ese caso el primer intercambio completo da mejor contexto.
    if new_conversation and len(message.strip().split()) < 3 and final_content:
        conv_repo.update_conversation_title(db, conversation_id, _extract_title(final_content))

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


def _with_screen_context(message: str, context: dict[str, Any] | None) -> str:
    if not context:
        return message
    safe_context = {
        key: value
        for key, value in context.items()
        if key in {"module", "route", "period", "visible_metrics", "data_status", "selected_entity", "suggested_action"}
    }
    return (
        "Contexto de pantalla de AI Financial OS. "
        "Usalo solo para orientar la respuesta; no inventes cifras y valida datos con tools si necesitas valores. "
        f"Contexto: {json.dumps(safe_context, ensure_ascii=False, default=str)}\n\n"
        f"Pregunta del usuario: {message}"
    )


def _valid_source(s: dict) -> bool:
    return isinstance(s, dict) and "type" in s
