"""Pydantic schemas for the AI assistant module."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    role: str  # user|system
    content: str


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    context: dict[str, Any] | None = None
    provider: str | None = None
    model: str | None = None
    enable_tools: bool = True


class ToolCallOut(BaseModel):
    name: str
    arguments: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    duration_ms: int | None = None
    status: str = "ok"


class SourceOut(BaseModel):
    type: str
    provider: str | None = None
    observed_at: str | None = None
    quality_score: float | None = None


# AI-1: cifras y acciones DETERMINISTAS extraídas de los resultados de las tools,
# no del texto del LLM. El frontend las pinta con formato numérico local (mismo
# principio que InsightOut: el backend nunca formatea números en copy).
class StructuredFigure(BaseModel):
    label: str
    value: float
    unit: str = ""
    precision: int = 0


class StructuredAction(BaseModel):
    label: str
    target: str
    params: dict[str, Any] = Field(default_factory=dict)


class StructuredPayload(BaseModel):
    key_figures: list[StructuredFigure] = []
    actions: list[StructuredAction] = []


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str | None
    tool_calls: list[ToolCallOut] = []
    sources: list[SourceOut] = []
    quality_score: float | None = None
    provider: str | None = None
    model: str | None = None
    structured: StructuredPayload | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str | None
    tool_calls: list[dict[str, Any]] | None = None
    sources: list[dict[str, Any]] | None = None
    quality_score: float | None = None
    structured: StructuredPayload | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] | None = None


class ConversationCreate(BaseModel):
    title: str | None = None


class ProviderStatus(BaseModel):
    name: str
    available: bool
    model: str | None = None
    error: str | None = None
    latency_ms: int | None = None


class AIStatus(BaseModel):
    enabled: bool
    default_provider: str
    default_model: str
    providers: list[ProviderStatus]


class ToolOut(BaseModel):
    name: str
    description: str
    source_type: str
    returns_sources: bool


# ── AI-3: Centro de Análisis (briefs proactivos) ───────────────────────────────

class BriefGenerateRequest(BaseModel):
    scope: str = "monthly_review"
    period: str | None = None  # YYYY-MM; None = mes actual
    provider: str | None = None
    model: str | None = None


class BriefOut(BaseModel):
    id: str
    scope: str
    period: str
    bundle: dict[str, Any]  # cifras cerradas deterministas (key_figures, signals, actions…)
    narrative: str | None = None  # None si el LLM falló → frontend renderiza el bundle
    data_state: str
    provider: str | None = None
    model: str | None = None
    created_at: str | None = None
