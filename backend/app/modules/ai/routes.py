"""AI assistant API endpoints."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.ai import service as ai_service
from app.modules.ai.memory import conversation_repository as conv_repo
from app.modules.ai.schemas import (
    AIStatus,
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

@router.get("/status", response_model=AIStatus)
async def get_status() -> AIStatus:
    provider_names = ai_service.list_providers()
    statuses = []
    for name in provider_names:
        try:
            provider = ai_service.get_provider(name)
            health = await provider.health()
            statuses.append(ProviderStatus(
                name=name,
                available=health.available,
                model=health.model,
                error=health.error,
                latency_ms=health.latency_ms,
            ))
        except Exception as exc:
            statuses.append(ProviderStatus(name=name, available=False, error=str(exc)))

    return AIStatus(
        enabled=settings.AI_ASSISTANT_ENABLED,
        default_provider=settings.AI_DEFAULT_PROVIDER,
        default_model=settings.AI_DEFAULT_MODEL,
        providers=statuses,
    )


@router.get("/providers", response_model=list[ProviderStatus])
async def list_providers() -> list[ProviderStatus]:
    result = []
    for name in ai_service.list_providers():
        try:
            provider = ai_service.get_provider(name)
            health = await provider.health()
            result.append(ProviderStatus(
                name=name,
                available=health.available,
                model=health.model,
                error=health.error,
                latency_ms=health.latency_ms,
            ))
        except Exception as exc:
            result.append(ProviderStatus(name=name, available=False, error=str(exc)))
    return result


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
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_calls=json.loads(m.tool_calls_json) if m.tool_calls_json else None,
                sources=json.loads(m.sources_json) if m.sources_json else None,
                quality_score=m.quality_score,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)) -> None:
    deleted = conv_repo.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
