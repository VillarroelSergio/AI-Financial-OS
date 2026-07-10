import asyncio


def test_get_balance_sheet_tool_returns_dict(client):
    from app.core.database import SessionLocal
    from app.modules.ai.tools.registry import tool_registry
    db = SessionLocal()
    try:
        tool = tool_registry.get("get_balance_sheet")
        assert tool is not None, "get_balance_sheet tool must be registered"
        result = asyncio.run(tool.handler(db=db, month="2026-06"))
        assert "net_worth" in result
        assert "assets" in result and isinstance(result["assets"], list)
        assert "liabilities" in result and isinstance(result["liabilities"], list)
        assert result["quality_score"] == 1.0
    finally:
        db.close()


def test_get_balance_sheet_invalid_month(client):
    from app.core.database import SessionLocal
    from app.modules.ai.tools.registry import tool_registry
    db = SessionLocal()
    try:
        tool = tool_registry.get("get_balance_sheet")
        result = asyncio.run(tool.handler(db=db, month="invalid"))
        assert "error" in result
    finally:
        db.close()
