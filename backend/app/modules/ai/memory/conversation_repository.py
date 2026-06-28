"""Conversation persistence — stores messages, tool calls and sources."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai import AIConversation, AIMessage, AIToolCall
from app.core.config import settings


def create_conversation(db: Session, title: str | None = None) -> AIConversation:
    conv = AIConversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, conversation_id: str) -> AIConversation | None:
    return db.query(AIConversation).filter(AIConversation.id == conversation_id).first()


def list_conversations(db: Session, limit: int = 50) -> list[AIConversation]:
    return (
        db.query(AIConversation)
        .order_by(AIConversation.updated_at.desc())
        .limit(limit)
        .all()
    )


def delete_conversation(db: Session, conversation_id: str) -> bool:
    conv = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
    if not conv:
        return False
    db.query(AIToolCall).filter(AIToolCall.conversation_id == conversation_id).delete()
    db.query(AIMessage).filter(AIMessage.conversation_id == conversation_id).delete()
    db.delete(conv)
    db.commit()
    return True


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str | None,
    tool_calls: list[dict] | None = None,
    sources: list[dict] | None = None,
    quality_score: float | None = None,
) -> AIMessage:
    msg = AIMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
        sources_json=json.dumps(sources) if sources else None,
        quality_score=quality_score,
    )
    db.add(msg)
    # Touch conversation updated_at
    db.query(AIConversation).filter(AIConversation.id == conversation_id).update(
        {"updated_at": datetime.now(timezone.utc)}
    )
    db.commit()
    db.refresh(msg)
    return msg


def add_tool_call(
    db: Session,
    conversation_id: str,
    message_id: str | None,
    tool_name: str,
    arguments: dict,
    result: dict,
    sources: list[dict] | None = None,
    duration_ms: int | None = None,
    status: str = "ok",
) -> AIToolCall:
    tc = AIToolCall(
        conversation_id=conversation_id,
        message_id=message_id,
        tool_name=tool_name,
        arguments_json=json.dumps(arguments),
        result_json=json.dumps(result),
        sources_json=json.dumps(sources) if sources else None,
        duration_ms=duration_ms,
        status=status,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def get_messages(db: Session, conversation_id: str) -> list[AIMessage]:
    return (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.asc())
        .all()
    )


def get_messages_as_llm_context(
    db: Session,
    conversation_id: str,
    max_messages: int = 20,
) -> list[dict[str, Any]]:
    """Return last N messages formatted for LLM consumption."""
    msgs = get_messages(db, conversation_id)[-max_messages:]
    result = []
    for m in msgs:
        if m.role in ("system", "user", "assistant"):
            result.append({"role": m.role, "content": m.content or ""})
    return result


def update_conversation_title(db: Session, conversation_id: str, title: str) -> None:
    db.query(AIConversation).filter(AIConversation.id == conversation_id).update({"title": title})
    db.commit()
