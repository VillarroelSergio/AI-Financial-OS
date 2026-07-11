from app.modules.security import service


def test_create_backup_keeps_last_20(tmp_path, monkeypatch):
    db_file = tmp_path / "financial.db"
    db_file.write_bytes(b"fake sqlite")
    monkeypatch.setattr(service, "database_path", lambda url=None: db_file)

    backups = tmp_path / "backups"
    backups.mkdir()
    # 25 backups previos con timestamps distintos (nombre ordena por fecha).
    for i in range(25):
        (backups / f"financial-2026{i + 1:02d}01T000000Z.db").write_bytes(b"x")

    result = service.create_backup()
    assert result["filename"].startswith("financial-")

    assert len(service.list_backups()) <= 20
