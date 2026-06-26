def _quote(category: str = "indices_eu") -> dict:
    return {"symbol": "^IBEX", "name": "IBEX 35", "category": category, "price": 12843.5, "change_pct": 0.73, "currency": "EUR", "sparkline": [12750.0, 12843.5], "last_updated": "2026-06-24T10:00:00Z", "market_open": True, "change_absolute": 93.08, "freshness_status": "live", "source": "test", "is_fallback": False, "is_stale": False, "warning": None, "confidence_score": 1.0}


def test_market_quotes_route_serializes_current_service(client, monkeypatch):
    monkeypatch.setattr(
        "app.modules.investments.market_data.routes.get_quotes",
        lambda category=None: [_quote(category=category or "indices_eu")],
    )
    response = client.get("/api/markets/quotes?category=indices_eu")
    assert response.status_code == 200
    quote = response.json()[0]
    assert quote["symbol"] == "^IBEX"
    assert quote["category"] == "indices_eu"
    assert quote["price"] == 12843.5
    assert quote["sparkline"] == [12750.0, 12843.5]


def test_market_refresh_conflict(client, monkeypatch):
    monkeypatch.setattr(
        "app.modules.investments.market_data.routes.refresh_quotes",
        lambda category=None: None,
    )
    response = client.post("/api/markets/quotes/refresh")
    assert response.status_code == 409
