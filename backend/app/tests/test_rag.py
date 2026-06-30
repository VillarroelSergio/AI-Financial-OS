from fastapi.testclient import TestClient


def test_rag_creates_and_queries_local_document(client: TestClient) -> None:
    created = client.post(
        "/api/rag/documents",
        json={
            "filename": "hipoteca.txt",
            "title": "Hipoteca",
            "text": "La cuota de la hipoteca vence el dia 5. El importe mensual es 850 euros.",
            "entity_type": "account",
            "entity_id": "mortgage-1",
        },
    )
    assert created.status_code == 201
    document = created.json()
    assert document["title"] == "Hipoteca"

    response = client.post(
        "/api/rag/query",
        json={"question": "Que importe tiene la cuota de la hipoteca?", "limit": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert "850" in body["answer"]
    assert body["sources"][0]["document_id"] == document["id"]


def test_rag_upload_rejects_unsupported_format(client: TestClient) -> None:
    response = client.post(
        "/api/rag/documents/upload",
        files={"file": ("extracto.pdf", b"%PDF", "application/pdf")},
    )
    assert response.status_code == 400
