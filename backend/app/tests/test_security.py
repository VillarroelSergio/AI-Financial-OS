import logging

from fastapi.testclient import TestClient

from app.modules.security import routes


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


def test_security_backup_hides_missing_database_details(
    client: TestClient, monkeypatch, caplog
) -> None:
    internal_path = "/srv/private-data/financial.db"

    def missing_database(_: str | None) -> dict:
        raise FileNotFoundError(f"Database not found: {internal_path}")

    monkeypatch.setattr(routes, "create_backup", missing_database)

    with caplog.at_level(logging.ERROR, logger="app.modules.security.routes"):
        response = client.post("/api/security/backups")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No se encontró la base de datos para crear la copia de seguridad."
    }
    assert internal_path not in response.text
    assert internal_path in caplog.text
