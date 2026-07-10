from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Session, "after_commit")
def _invalidate_insights_cache(_session: Session) -> None:
    """D4: cualquier escritura (tx, cuentas, holdings, presupuestos, snapshots…)
    invalida la caché de insights desde un único punto. Las lecturas no hacen
    commit, así que no la tocan."""
    from app.modules.insights import cache
    cache.invalidate()


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
    _migrate_investment_domain()  # antes de create_all: recrea tablas nuevas con esquema de spec
    Base.metadata.create_all(bind=engine)
    _migrate_transactions_scope()
    _migrate_household_bills_batch()
    _migrate_account_liability()


def _migrate_account_liability() -> None:
    """D6: pasivo explícito en cuentas. Hipotecas → is_liability=1 por defecto."""
    with engine.begin() as connection:
        cols = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(accounts)")}
        if not cols or "is_liability" in cols:
            return
        connection.exec_driver_sql(
            "ALTER TABLE accounts ADD COLUMN is_liability BOOLEAN DEFAULT 0"
        )
        connection.exec_driver_sql(
            "UPDATE accounts SET is_liability=1 WHERE type='mortgage'"
        )


def _migrate_investment_domain() -> None:
    """INV-2/4: si las tablas nuevas existen con esquema previo (pre-spec), se recrean.
    Son tablas nuevas de este ciclo, sin datos productivos → drop seguro."""
    expected_col = {
        "savings_account_configs": "account_id",   # antes: holding_id
        "fund_valuation_snapshots": "market_value",  # antes: value
    }
    with engine.begin() as connection:
        for table, col in expected_col.items():
            cols = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}
            if cols and col not in cols:
                connection.exec_driver_sql(f"DROP TABLE {table}")
        # Nº participaciones + valor liquidativo (opcionales) para el peso de fondos.
        fund_cols = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(fund_valuation_snapshots)")}
        if fund_cols and "units" not in fund_cols:
            connection.exec_driver_sql("ALTER TABLE fund_valuation_snapshots ADD COLUMN units NUMERIC")
        if fund_cols and "nav" not in fund_cols:
            connection.exec_driver_sql("ALTER TABLE fund_valuation_snapshots ADD COLUMN nav NUMERIC")


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


def _migrate_household_bills_batch() -> None:
    """Enlaza facturas detectadas con su importación para poder revertirlas."""
    with engine.begin() as connection:
        cols = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(household_bills)")}
        if cols and "import_batch_id" not in cols:
            connection.exec_driver_sql(
                "ALTER TABLE household_bills ADD COLUMN import_batch_id TEXT"
            )
