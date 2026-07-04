"""Economic Indicator Engine — convierte datos macro crudos en insights interpretables."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from app.modules.financial_knowledge._shared import now as _now
from app.modules.financial_knowledge._shared import uid as _uid
from app.modules.financial_knowledge.models import (
    EconomicIndicatorInsight,
    Severity,
    Trend,
)
from app.modules.market_intelligence.storage import repository as mi_repo

logger = logging.getLogger("financial_knowledge.economic_indicator_engine")

_RULES_PATH = Path(__file__).parent.parent / "rules" / "macro_rules.yaml"

# Mapeo catalog_item_id → subcategoría interpretable
_CATALOG_SUBCATEGORY: dict[str, str] = {
    # Inflation
    "es_cpi": "inflation", "us_cpi": "inflation", "eu_cpi": "inflation",
    "es_core_cpi": "core_inflation", "us_core_cpi": "core_inflation",
    # GDP
    "es_gdp": "gdp", "us_gdp": "gdp", "eu_gdp": "gdp",
    # Unemployment
    "es_unemployment": "unemployment", "us_unemployment": "unemployment", "eu_unemployment": "unemployment",
    # Interest rates
    "ecb_rate": "interest_rates", "fed_rate": "interest_rates",
    # Euribor
    "euribor_12m": "euribor", "euribor_3m": "euribor",
    # Industrial production
    "es_industrial_production": "industrial_production", "eu_industrial_production": "industrial_production",
    # Consumer confidence
    "eu_consumer_confidence": "consumer_confidence", "us_consumer_confidence": "consumer_confidence",
}

# Metas conocidas por subcategoría
_TARGETS: dict[str, float] = {
    "inflation": 2.0,
    "core_inflation": 2.0,
    "unemployment": 4.0,  # target aproximado
}


def _load_rules() -> dict:
    if _RULES_PATH.exists():
        return yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8")) or {}
    return {}


def _compute_trend(value: float, previous: Optional[float]) -> Trend:
    if previous is None:
        return Trend.UNKNOWN
    diff = value - previous
    if abs(diff) < 0.05:
        return Trend.STABLE
    return Trend.RISING if diff > 0 else Trend.FALLING


def _compute_severity_inflation(value: float, rules: dict) -> Severity:
    rule = rules.get("inflation_above_target", {})
    critical = rule.get("critical_threshold", 5.0)
    warning = rule.get("warning_threshold", 2.5)
    target = rule.get("target", 2.0)
    if value >= critical:
        return Severity.CRITICAL
    if value >= warning:
        return Severity.MEDIUM
    if value > target:
        return Severity.LOW
    return Severity.LOW


def _compute_severity_generic(subcategory: str, value: float, trend: Trend) -> Severity:
    if subcategory == "unemployment" and value > 15.0:
        return Severity.HIGH
    if subcategory == "unemployment" and value > 10.0:
        return Severity.MEDIUM
    if trend in (Trend.RISING, Trend.FALLING):
        return Severity.LOW
    return Severity.LOW


def _interpret(subcategory: str, value: float, trend: Trend, target: Optional[float]) -> str:
    parts = []
    if subcategory == "inflation":
        if target and value > target:
            parts.append(f"Inflación del {value:.1f}% por encima del objetivo del {target:.1f}%")
        else:
            parts.append(f"Inflación del {value:.1f}%")
        if trend == Trend.RISING:
            parts.append("con tendencia alcista")
        elif trend == Trend.FALLING:
            parts.append("con tendencia bajista")
    elif subcategory == "unemployment":
        parts.append(f"Desempleo del {value:.1f}%")
        if trend == Trend.RISING:
            parts.append("— mercado laboral deteriorándose")
    elif subcategory in ("interest_rates", "euribor"):
        parts.append(f"Tipo al {value:.2f}%")
        if trend == Trend.RISING:
            parts.append("en tendencia alcista (presión sobre hipotecas)")
        elif trend == Trend.FALLING:
            parts.append("en tendencia bajista")
    elif subcategory == "gdp":
        parts.append(f"PIB: {value:.1f}%")
        if trend == Trend.FALLING:
            parts.append("— señal de desaceleración económica")
    else:
        parts.append(f"Valor: {value}")
        if trend != Trend.UNKNOWN:
            parts.append(f"tendencia {trend.value}")
    return ", ".join(parts) if parts else f"{subcategory}: {value}"


def compute_insights(macro_rows: Optional[list[dict]] = None) -> list[EconomicIndicatorInsight]:
    """Genera insights desde datos macro de Market Intelligence."""
    rules = _load_rules()
    if macro_rows is None:
        macro_rows = mi_repo.get_latest_macro_all()

    insights: list[EconomicIndicatorInsight] = []
    seen_catalogs: set[str] = set()

    for row in macro_rows:
        cid = row.get("catalog_item_id", "")
        if cid in seen_catalogs:
            continue
        seen_catalogs.add(cid)

        subcategory = _CATALOG_SUBCATEGORY.get(cid, "other")
        value = row.get("value")
        if value is None:
            continue

        target = _TARGETS.get(subcategory)
        trend = _compute_trend(value, None)  # sin histórico en este pase inicial

        if subcategory == "inflation":
            severity = _compute_severity_inflation(value, rules)
        else:
            severity = _compute_severity_generic(subcategory, value, trend)

        distance = (value - target) if target is not None else None
        interpretation = _interpret(subcategory, value, trend, target)

        insight = EconomicIndicatorInsight(
            id=_uid(),
            indicator_id=row.get("indicator_id", cid),
            catalog_item_id=cid,
            name=cid.replace("_", " ").title(),
            category=subcategory,
            country=row.get("country", ""),
            value=float(value),
            unit=row.get("unit", "%"),
            period=str(row.get("period", "")),
            trend=trend,
            severity=severity,
            quality_score=float(row.get("quality_score", 1.0)),
            computed_at=_now(),
            source_provider=row.get("provider_id"),
            target_value=target,
            distance_to_target=distance,
            interpretation=interpretation,
        )
        insights.append(insight)

    logger.info("EconomicIndicatorEngine: %d insights generados", len(insights))
    return insights
