import asyncio


def test_get_insights_summary_tool_returns_dict(client):
    from app.core.database import SessionLocal
    from app.modules.ai.tools.registry import tool_registry
    db = SessionLocal()
    try:
        tool = tool_registry.get("get_insights_summary")
        assert tool is not None, "get_insights_summary tool must be registered"
        result = asyncio.run(tool.handler(db=db, period="2026-06", limit=5))
        assert "insights" in result
        assert "data_status" in result
        assert "summary" in result
        assert isinstance(result["insights"], list)
    finally:
        db.close()


def test_get_insights_summary_invalid_period(client):
    from app.core.database import SessionLocal
    from app.modules.ai.tools.registry import tool_registry
    db = SessionLocal()
    try:
        tool = tool_registry.get("get_insights_summary")
        result = asyncio.run(tool.handler(db=db, period="invalid", limit=5))
        assert "error" in result
    finally:
        db.close()
