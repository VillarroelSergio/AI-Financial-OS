from app.modules.insights.rules.net_worth_rules import net_worth_change_insight
from app.modules.insights.rules.investment_rules import investment_allocation_insight
from app.modules.insights.rules.goal_rules import goal_progress_insights
from app.modules.insights.schemas import DataStatus


def test_net_worth_no_data_returns_empty_or_insufficient(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = net_worth_change_insight(db, "2026-06")
        assert result == [] or all(i.data_status in (DataStatus.empty, DataStatus.insufficient, DataStatus.partial) for i in result)
    finally:
        db.close()


def test_investment_no_holdings_returns_empty(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = investment_allocation_insight(db, "2026-06")
        assert result == [] or all(i.data_status == DataStatus.empty for i in result)
    finally:
        db.close()


def test_goals_no_goals_returns_empty(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = goal_progress_insights(db, "2026-06")
        assert result == []
    finally:
        db.close()
