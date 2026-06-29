from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.modules.rag.schemas import (
    DocumentCreate,
    DocumentOut,
    DocumentSource,
    RagAnswer,
    RagQuestion,
)
from app.modules.rag.service import (
    answer_question,
    create_document,
    extract_text,
    search_documents,
)

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create_text_document(payload: DocumentCreate, db: Session = Depends(get_db)) -> Document:
    return create_document(
        db,
        filename=payload.filename,
        title=payload.title,
        text=payload.text,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    entity_type: str | None = Form(default=None),
    entity_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> Document:
    content = await file.read()
    if len(content) > 5_000_000:
        raise HTTPException(status_code=413, detail="Documento demasiado grande")
    try:
        text = extract_text(file.filename or "document.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return create_document(
        db,
        filename=file.filename or "document.txt",
        title=title,
        text=text,
        mime_type=file.content_type or "text/plain",
        entity_type=entity_type,
        entity_id=entity_id,
    )


@router.post("/query", response_model=RagAnswer)
def query_documents(payload: RagQuestion, db: Session = Depends(get_db)) -> RagAnswer:
    results = search_documents(
        db,
        question=payload.question,
        limit=payload.limit,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )
    sources = [
        DocumentSource(
            document_id=document.id,
            title=document.title,
            filename=document.filename,
            chunk_index=chunk.chunk_index,
            score=round(score, 4),
            excerpt=chunk.content[:300],
        )
        for document, chunk, score in results
    ]
    return RagAnswer(answer=answer_question(results, payload.question), sources=sources)
