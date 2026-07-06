"""One-shot: canoniza los `period` históricos a YYYY-MM / YYYY-Qn / YYYY.

ECO-3: desde ahora el repository valida `period` en escritura (`normalize_period`).
Este script arregla los datos escritos ANTES de esa validación (FRED con fechas sueltas,
etc.). Idempotente: correrlo dos veces no cambia nada la segunda vez.

Uso:  python -m app.modules.market_intelligence.storage.normalize_periods
Hace backup del .duckdb antes de tocar nada.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.duckdb import is_in_memory
from app.modules.market_intelligence.storage import repository


def main() -> int:
    db_path = Path(settings.DUCKDB_PATH)
    if db_path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = db_path.with_suffix(db_path.suffix + f".bak-{stamp}")
        shutil.copy2(db_path, backup)
        print(f"Backup: {backup}")
    else:
        print(f"Aviso: no existe {db_path} (se creará en memoria).")

    if is_in_memory():
        print("ERROR: DuckDB en memoria (otro proceso tiene el lock). Cierra el "
              "backend y reintenta — nada se normalizó de forma persistente.")
        return 1

    changed = repository.normalize_stored_periods()
    print(f"Periodos normalizados: macro={changed['macro_observations']}, "
          f"normalized={changed['normalized_records']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
