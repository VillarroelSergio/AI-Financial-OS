"""Job de retención (ECO-5): poda observaciones más antiguas que la `retention` del catálogo.

Pensado para correr periódicamente (cron/tarea mensual) o a mano. Idempotente. Hace backup
del .duckdb antes de tocar nada.

Uso:  python -m app.modules.market_intelligence.storage.retention
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.modules.market_intelligence.storage import repository


def main() -> int:
    db_path = Path(settings.MI_SQLITE_PATH)
    if db_path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = db_path.with_suffix(db_path.suffix + f".bak-{stamp}")
        shutil.copy2(db_path, backup)
        print(f"Backup: {backup}")

    deleted = repository.apply_retention()
    print(f"Retención aplicada: macro/normalized={deleted['macro_rows']}, "
          f"precios={deleted['price_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
