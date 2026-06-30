from app.modules.insights.scoring import compute_priority, compute_confidence, sort_and_limit
from app.modules.insights.schemas import InsightOut, InsightType, InsightSeverity, DataStatus
from datetime import datetime, timezone


def _make_insight(severity, data_status, impact_score=50.0, freshness="current"):
    return InsightOut(
        id="test",
        type=InsightType.data_quality,
        severity=InsightSeverity(severity),
        title="Test",
        summary="Test",
        period="2026-06",
        impact_area="spending",
        confidence=compute_confidence(data_status),
        priority=compute_priority(severity, data_status, impact_score, freshness),
        data_status=DataStatus(data_status),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def test_critical_has_higher_priority_than_info():
    critical = compute_priority("critical", "complete", 80.0, "current")
    info = compute_priority("info", "complete", 80.0, "current")
    assert critical > info


def test_complete_confidence_higher_than_empty():
    assert compute_confidence("complete") > compute_confidence("empty")


def test_sort_and_limit():
    insights = [
        _make_insight("info", "complete", 50.0),
        _make_insight("critical", "complete", 80.0),
        _make_insight("warning", "complete", 60.0),
    ]
    result = sort_and_limit(insights, limit=2)
    assert len(result) == 2
    assert result[0].severity == InsightSeverity.critical


def test_priority_normalized_0_to_100():
    p = compute_priority("warning", "partial", 60.0, "current")
    assert 0 <= p <= 100
