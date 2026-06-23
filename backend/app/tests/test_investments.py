from sqlalchemy import inspect


def test_investment_tables_are_created(client):
    from app.core.database import engine
    tables = inspect(engine).get_table_names()
    assert "investment_assets" in tables
    assert "holdings" in tables
    assert "investment_operations" in tables
