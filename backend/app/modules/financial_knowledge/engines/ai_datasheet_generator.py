"""AI Datasheet Generator — genera datasheet compacto para consumo de IA local."""
from __future__ import annotations
import json
import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from app.modules.financial_knowledge.models import (
    AIDatasheet, EconomicIndicatorInsight, FinancialSignal,
    MarketRegime, PersonalImpact, Severity,
)
from app.modules.market_intelligence.storage import repository as mi_repo

logger = logging.getLogger("financial_knowledge.ai_datasheet_generator")

_MAX_INSIGHTS = 10
_MAX_SIGNALS = 15
_MAX_IMPACTS = 8
_MAX_NEWS = 5


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _severity_rank(s: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(s, 0)


def _insight_to_dict(insight: EconomicIndicatorInsight) -> dict:
    return {
        "indicator_id": insight.indicator_id,
        "name": insight.name,
        "category": insight.category,
        "country": insight.country,
        "value": round(insight.value, 4),
        "unit": insight.unit,
        "period": insight.period,
        "trend": insight.trend.value,
        "severity": insight.severity.value,
        "interpretation": insight.interpretation,
        "quality_score": round(insight.quality_score, 2),
        "target_value": insight.target_value,
        "distance_to_target": round(insight.distance_to_target, 4) if insight.distance_to_target else None,
    }


def _signal_to_dict(signal: FinancialSignal) -> dict:
    return {
        "signal_type": signal.signal_type,
        "name": signal.name,
        "category": signal.category,
        "description": signal.description,
        "direction": signal.direction.value,
        "severity": signal.severity.value,
        "confidence_score": round(signal.confidence_score, 2),
        "quality_score": round(signal.quality_score, 2),
        "affected_assets": signal.affected_assets,
        "affected_user_domains": signal.affected_user_domains,
        "rule_id": signal.rule_id,
    }


def _regime_to_dict(regime: MarketRegime) -> dict:
    return {
        "risk_level": regime.risk_level.value,
        "inflation_regime": regime.inflation_regime.value,
        "rates_regime": regime.rates_regime.value,
        "growth_regime": regime.growth_regime.value,
        "market_trend": regime.market_trend.value,
        "confidence_score": round(regime.confidence_score, 2),
        "explanation": regime.explanation,
        "signals_used": regime.signals_used,
    }


def _impact_to_dict(impact: PersonalImpact) -> dict:
    return {
        "impact_type": impact.impact_type,
        "user_domain": impact.user_domain,
        "title": impact.title,
        "description": impact.description,
        "severity": impact.severity.value,
        "confidence_score": round(impact.confidence_score, 2),
        "estimated_monthly_impact": impact.estimated_monthly_impact,
        "estimated_portfolio_impact": impact.estimated_portfolio_impact,
        "currency": impact.currency,
        "related_goals": impact.related_goals,
    }


def _compute_overall_quality(
    insights: list[EconomicIndicatorInsight],
    signals: list[FinancialSignal],
    regime: Optional[MarketRegime],
) -> float:
    scores = [i.quality_score for i in insights] + [s.quality_score for s in signals]
    if regime:
        scores.append(regime.confidence_score)
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 3)


def generate_datasheet(
    insights: list[EconomicIndicatorInsight],
    signals: list[FinancialSignal],
    regime: Optional[MarketRegime],
    impacts: list[PersonalImpact],
) -> AIDatasheet:
    """Genera el AI Datasheet compacto con toda la información estructurada."""
    now = _now()

    # Priorizar por severidad
    top_insights = sorted(
        insights,
        key=lambda i: (_severity_rank(i.severity.value), i.quality_score),
        reverse=True,
    )[:_MAX_INSIGHTS]

    top_signals = sorted(
        signals,
        key=lambda s: (_severity_rank(s.severity.value), s.confidence_score),
        reverse=True,
    )[:_MAX_SIGNALS]

    top_impacts = sorted(
        impacts,
        key=lambda i: _severity_rank(i.severity.value),
        reverse=True,
    )[:_MAX_IMPACTS]

    # Noticias recientes de MI
    news_rows = mi_repo.get_latest_news(limit=_MAX_NEWS)
    news_context = [
        {
            "title": n.get("title", ""),
            "published_at": str(n.get("published_at", "")),
            "source_name": n.get("source_name", ""),
            "category": n.get("category", ""),
            "related_asset": n.get("related_asset", ""),
        }
        for n in news_rows
    ]

    # Advertencias
    warnings: list[str] = []
    if not insights:
        warnings.append("No hay insights de indicadores económicos disponibles")
    if not signals:
        warnings.append("No hay señales financieras activas")
    if regime is None:
        warnings.append("No se pudo determinar el régimen de mercado")
    low_quality = [s for s in signals if s.quality_score < 0.5]
    if low_quality:
        warnings.append(f"{len(low_quality)} señales con calidad de datos baja")

    # Fuentes
    sources = list({i.source_provider for i in insights if i.source_provider} |
                   {s.rule_id for s in signals if s.rule_id})

    quality = _compute_overall_quality(insights, signals, regime)

    datasheet = AIDatasheet(
        generated_at=now,
        quality_score=quality,
        market_regime=_regime_to_dict(regime) if regime else None,
        macro_insights=[_insight_to_dict(i) for i in top_insights],
        financial_signals=[_signal_to_dict(s) for s in top_signals],
        personal_impacts=[_impact_to_dict(i) for i in top_impacts],
        portfolio_context={},  # placeholder — se expande con datos reales en futuras versiones
        news_context=news_context,
        warnings=warnings,
        sources=sources,
    )

    logger.info(
        "AIDatasheetGenerator: quality=%.2f, %d insights, %d signals, %d impacts",
        quality, len(top_insights), len(top_signals), len(top_impacts),
    )
    return datasheet


def datasheet_to_json(datasheet: AIDatasheet) -> str:
    """Serializa el datasheet a JSON compacto."""
    d = {
        "generated_at": datasheet.generated_at.isoformat(),
        "quality_score": datasheet.quality_score,
        "market_regime": datasheet.market_regime,
        "macro_insights": datasheet.macro_insights,
        "financial_signals": datasheet.financial_signals,
        "personal_impacts": datasheet.personal_impacts,
        "portfolio_context": datasheet.portfolio_context,
        "news_context": datasheet.news_context,
        "warnings": datasheet.warnings,
        "sources": datasheet.sources,
    }
    return json.dumps(d, ensure_ascii=False, default=str)
