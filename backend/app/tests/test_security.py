from fastapi.testclient import TestClient


def test_security_integrity_reports_tables(client: TestClient) -> None:
    response = client.get("/api/security/integrity")
    assert response.status_code == 200
    body = response.json()
    assert body["database_ok"] is True
    assert "transactions" in body["tables"]
    assert "documents" in body["tables"]


def test_security_backup_creates_local_copy(client: TestClient) -> None:
    response = client.post("/api/security/backups")
    assert response.status_code == 201
    body = response.json()
    assert body["filename"].startswith("financial-")
    assert body["size_bytes"] > 0
