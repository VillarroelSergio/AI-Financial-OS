"""One-shot ECO-3b: copia las tablas mi_* de DuckDB (analytics.duckdb) a SQLite.

Ejecutar con el backend PARADO (DuckDB es mono-escritor). Idempotente por tabla:
vacía la tabla destino antes de copiar, así relanzarlo no duplica.

Uso:  python -m app.modules.market_intelligence.storage.migrate_duckdb_to_sqlite
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.modules.market_intelligence.storage import migrations
from app.modules.market_intelligence.storage.db import get_conn

# Nombres de tabla en el mismo orden del DDL (no dependemos de columnas, se introspectan).
_TABLES = [ddl.split("IF NOT EXISTS", 1)[1].split("(", 1)[0].strip() for ddl in migrations._DDL_STATEMENTS]


def main() -> int:
    import duckdb  # solo aquí: financial_knowledge aún lo usa, pero MI ya no depende de él

    src_path = Path(settings.DUCKDB_PATH)
    if not src_path.exists():
        print(f"No existe {src_path}; nada que migrar (BD nueva ya en SQLite).")
        return 0

    src = duckdb.connect(str(src_path), read_only=True)
    dst = get_conn()  # crea las tablas SQLite si no existen
    total = 0
    for table in _TABLES:
        try:
            cols = [c[0] for c in src.execute(f"DESCRIBE {table}").fetchall()]
        except Exception:
            continue  # la tabla no existía en el DuckDB de origen
        rows = src.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()
        if not rows:
            continue
        dst.execute(f"DELETE FROM {table}")
        placeholders = ", ".join("?" for _ in cols)
        dst.executemany(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            [list(r) for r in rows],  # datetime/date → ISO via adapters de db.py
        )
        total += len(rows)
        print(f"{table}: {len(rows)} filas")
    src.close()
    print(f"Migradas {total} filas a {settings.MI_SQLITE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
