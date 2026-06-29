from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    title: str
    mime_type: str
    entity_type: str | None
    entity_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    title: str | None = None
    filename: str = "manual-note.txt"
    text: str = Field(min_length=1, max_length=1_000_000)
    entity_type: str | None = None
    entity_id: str | None = None


class DocumentSource(BaseModel):
    document_id: str
    title: str
    filename: str
    chunk_index: int
    score: float
    excerpt: str


class RagQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    entity_type: str | None = None
    entity_id: str | None = None


class RagAnswer(BaseModel):
    answer: str
    sources: list[DocumentSource]
