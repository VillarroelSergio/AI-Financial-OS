from __future__ import annotations
from app.modules.insights.constants import SEVERITY_SCORES, CONFIDENCE_SCORES, FRESHNESS_SCORES
from app.modules.insights.schemas import InsightOut


def compute_confidence(data_status: str) -> float:
    return float(CONFIDENCE_SCORES.get(data_status, 30)) / 100.0


def compute_priority(
    severity: str,
    data_status: str,
    impact_score: float,
    freshness: str = "current",
) -> float:
    severity_s = float(SEVERITY_SCORES.get(severity, 50))
    confidence_s = float(CONFIDENCE_SCORES.get(data_status, 30))
    freshness_s = float(FRESHNESS_SCORES.get(freshness, 80))
    raw = (
        severity_s * 0.35
        + impact_score * 0.35
        + confidence_s * 0.20
        + freshness_s * 0.10
    )
    return round(min(100.0, max(0.0, raw)), 2)


def sort_and_limit(insights: list[InsightOut], limit: int) -> list[InsightOut]:
    return sorted(insights, key=lambda i: i.priority, reverse=True)[:limit]
