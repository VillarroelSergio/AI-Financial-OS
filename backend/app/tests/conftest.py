import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import database as db_module
from app.core.database import get_db
from app.main import app


@pytest.fixture
def client():
    # Create an isolated temp SQLite file for each test
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{tmp_path}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Patch the module-level engine so create_tables() and SessionLocal use it
    original_engine = db_module.engine
    original_session_local = db_module.SessionLocal

    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = db_module.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Restore original engine/session
    app.dependency_overrides.clear()
    db_module.engine = original_engine
    db_module.SessionLocal = original_session_local

    test_engine.dispose()
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
