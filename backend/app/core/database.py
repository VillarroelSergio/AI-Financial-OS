from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    import app.models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
    _migrate_transactions_scope()


def _migrate_transactions_scope() -> None:
    """Migración ligera (SQLite): columnas de conciliación + backfill una sola vez."""
    with engine.begin() as connection:
        cols = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(transactions)")}
        if not cols:
            return
        if "analytics_scope" in cols:
            # Modelo de carga única: ya no existe el estado 'pending' (idempotente).
            connection.exec_driver_sql(
                "UPDATE transactions SET analytics_scope='personal' "
                "WHERE analytics_scope='pending'"
            )
            return
        connection.exec_driver_sql(
            "ALTER TABLE transactions ADD COLUMN analytics_scope TEXT DEFAULT 'personal'"
        )
        connection.exec_driver_sql(
            "ALTER TABLE transactions ADD COLUMN linked_transaction_id TEXT"
        )
        # Recargas/traspasos Revolut importados antes de las reglas de perfil.
        connection.exec_driver_sql(
            "UPDATE transactions SET type='transfer' WHERE source_name='Revolut' AND ("
            "description LIKE 'Recarga%' OR description LIKE 'Una recarga%' "
            "OR description LIKE 'Savings Vault%' OR description LIKE 'To %' "
            "OR description LIKE 'From %')"
        )
        connection.exec_driver_sql(
            "UPDATE transactions SET analytics_scope='excluded' WHERE type='transfer'"
        )
