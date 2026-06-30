from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk

_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9_]{2,}")
_DIMENSIONS = 128
_CHUNK_SIZE = 1200
_CHUNK_OVERLAP = 180


def extract_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix not in {"txt", "md", "csv", "json"}:
        raise ValueError("Formato no soportado. Usa txt, md, csv o json.")
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        raise ValueError("El documento no contiene texto legible.")
    return text


def create_document(
    db: Session,
    *,
    filename: str,
    text: str,
    title: str | None = None,
    mime_type: str = "text/plain",
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> Document:
    document = Document(
        filename=filename,
        title=title or filename,
        mime_type=mime_type,
        text_content=text,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(document)
    db.flush()
    for index, chunk in enumerate(_chunk_text(text)):
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding_json=json.dumps(_embed(chunk)),
            )
        )
    db.commit()
    db.refresh(document)
    return document


def search_documents(
    db: Session,
    *,
    question: str,
    limit: int = 5,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[tuple[Document, DocumentChunk, float]]:
    query_embedding = _embed(question)
    query = db.query(DocumentChunk, Document).join(
        Document, Document.id == DocumentChunk.document_id
    )
    if entity_type:
        query = query.filter(Document.entity_type == entity_type)
    if entity_id:
        query = query.filter(Document.entity_id == entity_id)

    scored: list[tuple[Document, DocumentChunk, float]] = []
    for chunk, document in query.all():
        score = _cosine(query_embedding, json.loads(chunk.embedding_json))
        if score > 0:
            scored.append((document, chunk, score))
    scored.sort(key=lambda item: item[2], reverse=True)
    return scored[:limit]


def answer_question(results: list[tuple[Document, DocumentChunk, float]], question: str) -> str:
    if not results:
        return "No hay evidencia suficiente en los documentos locales para responder."
    best_fragments = " ".join(chunk.content for _, chunk, _ in results[:3])
    terms = [t for t, _ in Counter(_tokens(question)).most_common(8)]
    sentences = re.split(r"(?<=[.!?])\s+", best_fragments)
    selected = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip() and any(term in sentence.lower() for term in terms)
    ][:4]
    if not selected:
        selected = [results[0][1].content[:500].strip()]
    return " ".join(selected)


def _chunk_text(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    chunks: list[str] = []
    start = 0
    while start < len(compact):
        chunks.append(compact[start : start + _CHUNK_SIZE])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _embed(text: str) -> list[float]:
    vector = [0.0] * _DIMENSIONS
    for token in _tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % _DIMENSIONS
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
