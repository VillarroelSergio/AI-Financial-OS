from dataclasses import dataclass
from typing import Iterable

from models.base import AdapterResult


@dataclass
class ComparisonMetric:
    key: str
    providers: list[str]
    values: dict[str, float]
    min_value: float
    max_value: float
    spread_abs: float
    spread_pct: float


def compare_equivalent_values(results: Iterable[AdapterResult]) -> list[ComparisonMetric]:
    grouped: dict[str, dict[str, float]] = {}
    for result in results:
        if not result.success:
            continue
        for record in result.records:
            key = _record_key(record)
            value = _record_value(record)
            if key and value is not None:
                grouped.setdefault(key, {})[result.provider] = value

    metrics: list[ComparisonMetric] = []
    for key, values in grouped.items():
        if len(values) < 2:
            continue
        min_value = min(values.values())
        max_value = max(values.values())
        spread_abs = max_value - min_value
        spread_pct = (spread_abs / min_value * 100) if min_value else 0.0
        metrics.append(
            ComparisonMetric(
                key=key,
                providers=sorted(values),
                values=values,
                min_value=min_value,
                max_value=max_value,
                spread_abs=round(spread_abs, 6),
                spread_pct=round(spread_pct, 4),
            )
        )
    return metrics


def _record_key(record) -> str | None:
    symbol = getattr(record, "symbol", "")
    if symbol:
        return f"symbol:{symbol}:{getattr(record, 'asset_type', '')}"
    indicator_id = getattr(record, "indicator_id", "")
    period = getattr(record, "period", "")
    if indicator_id:
        return f"macro:{indicator_id}:{period}"
    pair = getattr(record, "pair", "")
    if pair:
        return f"currency:{pair}"
    return None


def _record_value(record) -> float | None:
    for attr in ("price", "value", "rate", "amount"):
        value = getattr(record, attr, None)
        if isinstance(value, (int, float)):
            return float(value)
    return None
