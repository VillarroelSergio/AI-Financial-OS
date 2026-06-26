"""Funciones de check individuales para el Quality Engine."""
from __future__ import annotations
import math
from datetime import datetime, timezone

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import CheckResult

# Pesos de cada check en el score final
WEIGHTS = {
    "freshness": 0.30,
    "completeness": 0.20,
    "validity": 0.25,
    "outlier": 0.15,
    "provider_reliability": 0.10,
}

# Ventana máxima de frescura por frecuencia (horas)
_FRESHNESS_WINDOWS: dict[str, int] = {
    "realtime": 1,
    "daily": 26,
    "weekly": 8 * 24,
    "monthly": 35 * 24,
    "quarterly": 95 * 24,
    "yearly": 370 * 24,
}


def check_freshness(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    retrieved_at = result.adapter_result.records[0].retrieved_at if result.adapter_result.records else None
    if retrieved_at is None:
        return CheckResult("freshness", "fail", 0.0, "No retrieved_at available")

    now = datetime.now(timezone.utc)
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    age_hours = (now - retrieved_at).total_seconds() / 3600
    max_hours = _FRESHNESS_WINDOWS.get(indicator.frequency, 26)

    if age_hours <= max_hours:
        return CheckResult("freshness", "pass", 1.0, f"Age {age_hours:.1f}h <= {max_hours}h")
    elif age_hours <= max_hours * 2:
        return CheckResult("freshness", "warn", 0.5, f"Age {age_hours:.1f}h > {max_hours}h")
    else:
        return CheckResult("freshness", "fail", 0.0, f"Age {age_hours:.1f}h far exceeds {max_hours}h")


def check_completeness(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    if not result.adapter_result.records:
        return CheckResult("completeness", "fail", 0.0, "No records returned")
    record = result.adapter_result.records[0]
    required = ["provider", "source", "retrieved_at", "country", "region"]
    missing = [f for f in required if not getattr(record, f, None)]
    if not missing:
        return CheckResult("completeness", "pass", 1.0, "All required fields present")
    score = max(0.0, 1.0 - len(missing) * 0.2)
    return CheckResult("completeness", "warn", score, f"Missing: {missing}")


def check_validity(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    if not result.adapter_result.records:
        return CheckResult("validity", "fail", 0.0, "No records")
    record = result.adapter_result.records[0]
    value = getattr(record, "value", None) or getattr(record, "rate", None) or getattr(record, "price", None)
    if value is None:
        return CheckResult("validity", "warn", 0.6, "Numeric value field is None")
    if isinstance(value, float) and math.isnan(value):
        return CheckResult("validity", "fail", 0.0, "Value is NaN")
    if value < 0 and indicator.category not in ("macro",):
        return CheckResult("validity", "warn", 0.7, f"Unexpected negative value: {value}")
    return CheckResult("validity", "pass", 1.0, f"Value {value} looks valid")


def check_outlier(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    return CheckResult("outlier", "pass", 1.0, "Outlier check skipped (no history yet)")


def check_provider_reliability(result: CatalogFetchResult, indicator: CatalogIndicator) -> CheckResult:
    return CheckResult("provider_reliability", "pass", 0.8, "Reliability check: no history, using default 0.8")
