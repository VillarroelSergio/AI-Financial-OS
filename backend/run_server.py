"""Entry de producción del backend — usado por PyInstaller (financial-backend.exe).

En modo empaquetado (sys.frozen) los datos del usuario viven en
%APPDATA%\\FinancialAgent\\ y se inyectan vía variables de entorno ANTES de
importar `app`, porque `app.core.config.Settings` se instancia en import.

En desarrollo (`python run_server.py`) no toca nada: usa ./data como siempre.
"""
from __future__ import annotations

import multiprocessing
import os
import sys
from pathlib import Path

PORT = int(os.environ.get("BACKEND_PORT", "8010"))


def _configure_production_env() -> None:
    data_dir = Path(os.environ.get("FINOS_DATA_DIR") or Path(os.environ["APPDATA"]) / "FinancialAgent")
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{(data_dir / 'financial.db').as_posix()}")
    os.environ.setdefault("DUCKDB_PATH", str(data_dir / "analytics.duckdb"))


def main() -> None:
    if getattr(sys, "frozen", False):
        _configure_production_env()

    import uvicorn

    from app.main import app

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
