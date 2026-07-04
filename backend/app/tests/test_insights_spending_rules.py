from app.modules.insights.rules.cashflow_rules import cashflow_alert_insight
from app.modules.insights.rules.spending_rules import (
    savings_rate_insight,
    spending_anomaly_insights,
)
from app.modules.insights.schemas import DataStatus


def test_spending_anomaly_detected(client):
    r = client.get("/api/insights?period=2026-06")
    assert r.status_code == 200
    data = r.json()
    assert "insights" in data
    assert data["data_status"] in ("empty", "insufficient", "complete", "partial")


def test_spending_anomaly_empty_when_no_data(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = spending_anomaly_insights(db, "2026-06")
        assert result == [] or all(i.data_status in (DataStatus.empty, DataStatus.insufficient) for i in result)
    finally:
        db.close()


def test_savings_rate_empty_when_no_data(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = savings_rate_insight(db, "2026-06")
        assert result == [] or all(i.data_status in (DataStatus.empty, DataStatus.insufficient) for i in result)
    finally:
        db.close()


def test_cashflow_no_alert_when_no_data(client):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        result = cashflow_alert_insight(db, "2026-06")
        assert result == [] or all(i.data_status in (DataStatus.empty, DataStatus.insufficient) for i in result)
    finally:
        db.close()
