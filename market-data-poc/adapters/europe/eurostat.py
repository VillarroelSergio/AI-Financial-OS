"""Eurostat adapter — EU GDP growth rate (QoQ, EA20)."""
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp"
    "?format=JSON&lang=EN&freq=Q&unit=CLV_PCH_PRE&na_item=B1GQ&geo=EA20&lastTimePeriod=4"
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
    )


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
            r = requests.get(_GDP_URL, headers=_HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()

            values: dict = data.get("value", {})
            time_category = (
                data.get("dimension", {})
                    .get("time", {})
                    .get("category", {})
            )
            time_labels: dict = time_category.get("label", {})
            time_index: dict = time_category.get("index", {})

            # time_labels: {"0": "2023-Q1", "1": "2023-Q2", ...}
            # values:      {"0": 0.3, "1": -0.1, ...}
            if time_index:
                indexed_periods = sorted(
                    ((str(idx), period) for period, idx in time_index.items()),
                    key=lambda x: int(x[0]),
                )
            else:
                indexed_periods = sorted(time_labels.items(), key=lambda x: int(x[0]))
            records: list[MacroIndicator] = []

            for idx, period in indexed_periods[-3:]:
                val = values.get(idx)
                if val is None:
                    continue
                records.append(
                    MacroIndicator(
                        provider=self.name,
                        source=_GDP_URL,
                        retrieved_at=retrieved_at,
                        country="EA",
                        region="Eurozone",
                        confidence_score=1.0,
                        indicator_id="EU_GDP_GROWTH",
                        name="EU GDP Growth QoQ",
                        value=float(val),
                        unit="%",
                        period=period,
                        frequency="quarterly",
                    )
                )

            latency_ms = (time.time() - t0) * 1000
            raw_sample = {"value_count": len(values), "preview": str(data)[:500]}
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
