from sqlalchemy import inspect


def test_investment_tables_are_created(client):
    from app.core.database import engine
    tables = inspect(engine).get_table_names()
    assert "investment_assets" in tables
    assert "holdings" in tables
    assert "investment_operations" in tables


def test_assets_crud(client):
    r = client.post("/api/investments/assets", json={
        "name": "Apple Inc.", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    })
    assert r.status_code == 201
    asset = r.json()
    assert asset["name"] == "Apple Inc."
    asset_id = asset["id"]

    r = client.get("/api/investments/assets")
    assert r.status_code == 200
    assert any(a["id"] == asset_id for a in r.json())

    r = client.patch(f"/api/investments/assets/{asset_id}", json={"sector": "Technology"})
    assert r.status_code == 200
    assert r.json()["sector"] == "Technology"

    r = client.delete(f"/api/investments/assets/{asset_id}")
    assert r.status_code == 204

    r = client.get("/api/investments/assets")
    assert all(a["id"] != asset_id for a in r.json())


def test_asset_not_found_returns_404(client):
    r = client.patch("/api/investments/assets/nonexistent", json={"sector": "X"})
    assert r.status_code == 404
