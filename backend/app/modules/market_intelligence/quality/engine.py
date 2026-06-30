"""QualityEngine — calcula el quality score de un CatalogFetchResult."""
from __future__ import annotations

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.checks import (
    WEIGHTS,
    check_completeness,
    check_freshness,
    check_outlier,
    check_provider_reliability,
    check_validity,
)
from app.modules.market_intelligence.quality.schemas import CheckResult, QualityResult


class QualityEngine:
    def score(self, result: CatalogFetchResult, indicator: CatalogIndicator) -> QualityResult:
        if not result.adapter_result.success:
            return QualityResult(
                final_score=0.0,
                checks=[CheckResult("overall", "fail", 0.0, "Adapter fetch failed")],
            )

        checks = [
            check_freshness(result, indicator),
            check_completeness(result, indicator),
            check_validity(result, indicator),
            check_outlier(result, indicator),
            check_provider_reliability(result, indicator),
        ]

        final_score = sum(
            WEIGHTS[c.name] * c.score
            for c in checks
            if c.name in WEIGHTS
        )

        return QualityResult(final_score=round(final_score, 4), checks=checks)
