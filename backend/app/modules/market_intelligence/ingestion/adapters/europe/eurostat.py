"""Eurostat adapter — EU GDP growth rate (QoQ, EA20)."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp"
    "?format=JSON&lang=EN&freq=Q&unit=CLV_PCH_PRE&na_item=B1GQ&geo=EA20&lastTimePeriod=4"
)
_UNEMPLOYMENT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m"
    "?format=JSON&lang=EN&freq=M&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&geo=EA20&lastTimePeriod=3"
)
_INFLATION_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr"
    "?format=JSON&lang=EN&freq=M&coicop=CP00&geo=EA20&lastTimePeriod=3"
)


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="Eurostat",
        id="eurostat",
        category="macro",
        region="Eurozone",
        method="api",
        base_url="https://ec.europa.eu/eurostat",
        requires_api_key=False,
        declared_update_frequency="quarterly",
        declared_historical_depth_years=30,
        license="Eurostat Open Data",
        notes="Eurostat REST dissemination API",
        capabilities=("macro", "historical"),
        priority="primary",
    )


def _dimension_ids(data: dict) -> list[str]:
    ids = data.get("id")
    if isinstance(ids, list):
        return ids
    dimensions = data.get("dimension", {})
    return [key for key in dimensions if key != "id" and key != "size"]


def _dimension_sizes(data: dict, ids: list[str]) -> list[int]:
    sizes = data.get("size")
    if isinstance(sizes, list) and len(sizes) == len(ids):
        return [int(size) for size in sizes]
    result = []
    for dim_id in ids:
        index = data.get("dimension", {}).get(dim_id, {}).get("category", {}).get("index", {})
        result.append(len(index) or 1)
    return result


def _time_periods(data: dict) -> list[tuple[int, str]]:
    time_category = data.get("dimension", {}).get("time", {}).get("category", {})
    time_index = time_category.get("index", {})
    labels = time_category.get("label", {})
    if time_index:
        return sorted(((int(idx), period) for period, idx in time_index.items()), key=lambda x: x[0])
    return sorted(((int(idx), label) for idx, label in labels.items()), key=lambda x: x[0])


def _value_for_time(data: dict, time_pos: int):
    values = data.get("value", {})
    if not isinstance(values, dict):
        return None
    ids = _dimension_ids(data)
    sizes = _dimension_sizes(data, ids)
    if "time" not in ids:
        return values.get(str(time_pos))
    coords = [0] * len(ids)
    coords[ids.index("time")] = time_pos
    flat_index = 0
    for i, coord in enumerate(coords):
        stride = 1
        for size in sizes[i + 1:]:
            stride *= size
        flat_index += coord * stride
    return values.get(str(flat_index))


def _parse_jsonstat(data: dict, source: str, indicator_id: str, name: str, frequency: str, retrieved_at: datetime) -> list[MacroIndicator]:
    records: list[MacroIndicator] = []
    for time_pos, period in _time_periods(data)[-3:]:
        val = _value_for_time(data, time_pos)
        if val is None:
            continue
        records.append(
            MacroIndicator(
                provider="Eurostat",
                source=source,
                retrieved_at=retrieved_at,
                country="EA",
                region="Eurozone",
                confidence_score=1.0,
                indicator_id=indicator_id,
                name=name,
                value=float(val),
                unit="%",
                period=period,
                frequency=frequency,
            )
        )
    return records


class EurostatAdapter(BaseAdapter):
    name = "Eurostat"
    category = "macro"
    region = "Eurozone"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)

        try:
            records: list[MacroIndicator] = []
            raw_sample = None
            for url, indicator_id, name, frequency in (
                (_GDP_URL, "EU_GDP_GROWTH", "EU GDP Growth QoQ", "quarterly"),
                (_INFLATION_URL, "EU_HICP_INFLATION", "Euro area HICP inflation", "monthly"),
                (_UNEMPLOYMENT_URL, "EU_UNEMPLOYMENT", "Euro area unemployment rate", "monthly"),
            ):
                r = requests.get(url, headers=_HEADERS, timeout=10)
                r.raise_for_status()
                data = r.json()
                raw_sample = raw_sample or {"value_count": len(data.get("value", {})), "preview": str(data)[:500]}
                records.extend(_parse_jsonstat(data, url, indicator_id, name, frequency, retrieved_at))

            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "No data parsed",
                latency_ms=latency_ms,
                raw_sample=raw_sample,
                metadata=metadata,
            )

        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc),
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )
