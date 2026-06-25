from models.base import AdapterResult
from models.evaluation import ProviderEvaluation

# Scoring weights (must sum to 1.0)
_WEIGHTS = {
    "data_quality": 0.25,
    "reliability": 0.20,
    "coverage_breadth": 0.15,
    "geo_coverage": 0.10,
    "historical_depth": 0.10,
    "update_frequency": 0.10,
    "latency_score": 0.05,
    "integration_complexity": 0.03,
    "legal_risk": 0.02,  # inverted: lower risk -> higher contribution
}


def score_adapter(result: AdapterResult) -> ProviderEvaluation:
    """Compute a ProviderEvaluation from an AdapterResult."""

    reliability = _score_reliability(result)
    latency_score = _score_latency(result.latency_ms)
    data_quality = _score_data_quality(result)
    historical_depth = _score_historical_depth(
        result.metadata.declared_historical_depth_years
    )
    update_frequency = _score_update_frequency(result.metadata.declared_update_frequency)
    coverage_breadth = _score_coverage_breadth(result)
    geo_coverage = _score_geo_coverage(result.metadata.region)
    integration_complexity = _score_integration_complexity(result.metadata.method)
    legal_risk = _score_legal_risk(result.metadata.license, result.metadata.method)

    # Weighted total — legal_risk is inverted (0=safe contributes positively)
    score_total = (
        data_quality * _WEIGHTS["data_quality"]
        + reliability * _WEIGHTS["reliability"]
        + coverage_breadth * _WEIGHTS["coverage_breadth"]
        + geo_coverage * _WEIGHTS["geo_coverage"]
        + historical_depth * _WEIGHTS["historical_depth"]
        + update_frequency * _WEIGHTS["update_frequency"]
        + latency_score * _WEIGHTS["latency_score"]
        + integration_complexity * _WEIGHTS["integration_complexity"]
        + (100 - legal_risk) * _WEIGHTS["legal_risk"]
    )

    recommendation = _recommend(score_total)

    return ProviderEvaluation(
        provider=result.provider,
        score_total=round(score_total, 2),
        data_quality=round(data_quality, 2),
        reliability=round(reliability, 2),
        coverage_breadth=round(coverage_breadth, 2),
        geo_coverage=round(geo_coverage, 2),
        historical_depth=round(historical_depth, 2),
        update_frequency=round(update_frequency, 2),
        latency_score=round(latency_score, 2),
        integration_complexity=round(integration_complexity, 2),
        legal_risk=round(legal_risk, 2),
        recommendation=recommendation,
        adapter_result=result,
    )


def _score_reliability(result: AdapterResult) -> float:
    return 100.0 if result.success else 0.0


def _score_latency(latency_ms: float) -> float:
    if latency_ms < 500:
        return 100.0
    if latency_ms < 1000:
        return 80.0
    if latency_ms < 2000:
        return 60.0
    if latency_ms < 5000:
        return 40.0
    return 0.0


def _score_data_quality(result: AdapterResult) -> float:
    if not result.success or not result.records:
        return 0.0
    avg_confidence = sum(
        getattr(r, "confidence_score", 1.0) for r in result.records
    ) / len(result.records)
    return round(avg_confidence * 100, 2)


def _score_historical_depth(years: int) -> float:
    if years <= 0:
        return 0.0
    if years < 1:
        return 10.0
    if years < 5:
        return 20.0
    if years < 10:
        return 40.0
    if years < 20:
        return 60.0
    if years < 30:
        return 80.0
    return 100.0


def _score_update_frequency(freq: str) -> float:
    mapping = {
        "realtime": 100.0,
        "daily": 80.0,
        "weekly": 60.0,
        "monthly": 40.0,
        "yearly": 20.0,
        "unknown": 0.0,
    }
    return mapping.get(freq.lower(), 0.0)


def _score_coverage_breadth(result: AdapterResult) -> float:
    """Simple proxy: more records -> broader coverage, capped at 100."""
    if not result.success or not result.records:
        return 0.0
    count = len(result.records)
    if count >= 20:
        return 100.0
    if count >= 10:
        return 80.0
    if count >= 5:
        return 60.0
    if count >= 1:
        return 40.0
    return 0.0


def _score_geo_coverage(region: str) -> float:
    region_lower = region.lower()
    if region_lower in ("global", "worldwide"):
        return 100.0
    if region_lower in ("eurozone", "europe", "usa"):
        return 70.0
    return 40.0


def _score_integration_complexity(method: str) -> float:
    mapping = {
        "api": 100.0,
        "csv": 60.0,
        "rss": 60.0,
        "scraping": 20.0,
    }
    return mapping.get(method.lower(), 60.0)


def _score_legal_risk(license_: str, method: str) -> float:
    if method.lower() == "scraping":
        return 100.0
    if license_.lower() == "open":
        return 0.0
    if license_.lower() == "freemium":
        return 50.0
    return 75.0


def _recommend(score: float) -> str:
    if score >= 75:
        return "principal"
    if score >= 50:
        return "secundario"
    if score >= 30:
        return "fallback"
    return "descartado"
