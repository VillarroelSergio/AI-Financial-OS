"""One-shot: purga histórica de observaciones macro/bonos mal categorizadas.

Antes corría en cada arranque (startup._run_once). Con el bug de clonación (P1)
cortado en origen (allowlists honestas en los adapters), ya no hace falta en el
hot-path: se ejecuta una sola vez para limpiar datos viejos.

Uso:  python -m app.modules.market_intelligence.storage.purge_clones
Hace backup del .duckdb antes de tocar nada.
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
    else:
        print(f"Aviso: no existe {db_path}.")

    purged = repository.purge_mismatched_macro_observations()
    print(f"Purgadas {purged} filas mal categorizadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
