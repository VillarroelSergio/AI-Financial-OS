"""AI assistant API endpoints."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.ai import analysis as ai_analysis
from app.modules.ai import service as ai_service
from app.modules.ai.memory import conversation_repository as conv_repo
from app.modules.ai.schemas import (
    AIStatus,
    BriefGenerateRequest,
    BriefOut,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationOut,
    MessageOut,
    ProviderStatus,
    ToolOut,
)
from app.modules.ai.tools.registry import tool_registry

router = APIRouter()


# ── Status & providers ────────────────────────────────────────────────────────

async def _check_provider_health(name: str) -> ProviderStatus:
    """Run a single provider health check, returning ProviderStatus regardless of outcome."""
    try:
        provider = ai_service.get_provider(name)
        health = await provider.health()
        return ProviderStatus(
            name=name,
            available=health.available,
            model=health.model,
            error=health.error,
            latency_ms=health.latency_ms,
        )
    except Exception as exc:
        return ProviderStatus(name=name, available=False, error=str(exc))


@router.get("/status", response_model=AIStatus)
async def get_status() -> AIStatus:
    provider_names = ai_service.list_providers()
    # Run all health checks concurrently so N offline providers don't multiply latency
    statuses = await asyncio.gather(
        *(_check_provider_health(name) for name in provider_names)
    )
    return AIStatus(
        enabled=settings.AI_ASSISTANT_ENABLED,
        default_provider=settings.AI_DEFAULT_PROVIDER,
        default_model=settings.AI_DEFAULT_MODEL,
        providers=list(statuses),
    )


@router.get("/providers", response_model=list[ProviderStatus])
async def list_providers() -> list[ProviderStatus]:
    provider_names = ai_service.list_providers()
    # Run all health checks concurrently — avoids sequential timeout stacking
    return list(
        await asyncio.gather(
            *(_check_provider_health(name) for name in provider_names)
        )
    )


# ── Tools ─────────────────────────────────────────────────────────────────────

@router.get("/tools", response_model=list[ToolOut])
def list_tools() -> list[ToolOut]:
    return [
        ToolOut(
            name=t.name,
            description=t.description,
            source_type=t.source_type,
            returns_sources=t.returns_sources,
        )
        for t in tool_registry.list_all()
    ]


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if not settings.AI_ASSISTANT_ENABLED:
        raise HTTPException(status_code=503, detail="AI Assistant is disabled")
    try:
        return await ai_service.chat(
            db=db,
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            provider_name=request.provider,
            model=request.model,
            enable_tools=request.enable_tools,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI error: {exc}")


# ── Analysis Center (AI-3: briefs proactivos) ─────────────────────────────────

@router.post("/briefs", response_model=BriefOut)
async def generate_brief(request: BriefGenerateRequest, db: Session = Depends(get_db)) -> BriefOut:
    if not settings.AI_ASSISTANT_ENABLED:
        raise HTTPException(status_code=503, detail="AI Assistant is disabled")
    try:
        brief = await ai_analysis.generate_brief(
            db=db,
            scope=request.scope,
            period=request.period,
            provider_name=request.provider,
            model=request.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return BriefOut(**brief)


@router.get("/briefs", response_model=list[BriefOut])
def list_briefs(limit: int = 20, db: Session = Depends(get_db)) -> list[BriefOut]:
    return [BriefOut(**b) for b in ai_analysis.list_briefs(db, limit=limit)]


@router.get("/briefs/{scope}/{period}", response_model=BriefOut)
def get_brief(scope: str, period: str, db: Session = Depends(get_db)) -> BriefOut:
    brief = ai_analysis.get_brief(db, scope, period)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return BriefOut(**brief)


# ── Conversations ─────────────────────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> ConversationOut:
    conv = conv_repo.create_conversation(db, title=payload.title)
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        summary=conv.summary,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationOut]:
    convs = conv_repo.list_conversations(db)
    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            summary=c.summary,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in convs
    ]


def _message_out(m) -> MessageOut:
    tool_calls = json.loads(m.tool_calls_json) if m.tool_calls_json else None
    # AI-1: regenera structured determinista de los tool_calls guardados (no se
    # persiste columna nueva) para que las chips reaparezcan al recargar el chat.
    structured = ai_service._harvest_structured(tool_calls) if tool_calls else None
    return MessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        tool_calls=tool_calls,
        sources=json.loads(m.sources_json) if m.sources_json else None,
        quality_score=m.quality_score,
        structured=structured,
        created_at=m.created_at,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> ConversationOut:
    conv = conv_repo.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = conv_repo.get_messages(db, conversation_id)
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        summary=conv.summary,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[_message_out(m) for m in messages],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)) -> None:
    deleted = conv_repo.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
