# 24 - Document Intelligence / RAG

La Fase 9 permite consultar documentacion financiera local sin subir datos a servicios externos.

## Capacidades

- Alta manual de documentos de texto.
- Subida local de `txt`, `md`, `csv` y `json`.
- Extraccion de texto UTF-8 local.
- Troceado de contenido y embeddings locales deterministas.
- Busqueda semantica local por similitud coseno.
- Preguntas sobre documentos con fuentes y fragmentos usados.
- Vinculo opcional entre documentos y entidades financieras mediante `entity_type` y `entity_id`.

## API

- `GET /api/rag/documents`
- `POST /api/rag/documents`
- `POST /api/rag/documents/upload`
- `POST /api/rag/query`

## Modelo de datos

- `documents`: metadatos, texto extraido y vinculo opcional a entidad.
- `document_chunks`: fragmentos y embedding JSON local.

La primera version no usa servicios externos ni modelos de embeddings descargables. PDF e imagenes quedan fuera hasta incorporar OCR local.
