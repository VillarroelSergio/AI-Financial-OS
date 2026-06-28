"""Bureau of Labor Statistics adapter — US unemployment rate."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_BLS_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000"


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="BLS",
        id="bls",
        category="macro",
        region="USA",
        method="api",
        base_url="https://api.bls.gov",
        requires_api_key=False,
        declared_update_frequency="monthly",
        declared_historical_depth_years=10,
        license="Public Domain (US Bureau of Labor Statistics)",
        notes="BLS public API v1 — limited to 10 years without API key",
    )


class BLSAdapter(BaseAdapter):
    name = "BLS"
    category = "macro"
    region = "USA"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)

        try:
            r = requests.get(_BLS_URL, headers=_HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()

            raw_sample = {"preview": str(data)[:500]}

            status = data.get("status", "")
            if status != "REQUEST_SUCCEEDED":
                raise ValueError(f"BLS API returned status: {status}")

            series_data = (
                data.get("Results", {})
                    .get("series", [{}])[0]
                    .get("data", [])
            )

            records: list[MacroIndicator] = []
            for item in series_data[:3]:
                year = item.get("year", "")
                period = item.get("period", "")   # e.g. "M01" for January
                period_name = item.get("periodName", period)
                val_str = item.get("value", "")
                try:
                    value = float(val_str)
                except (ValueError, TypeError):
                    continue
                period_label = f"{year}-{period_name}"
                records.append(
                    MacroIndicator(
                        provider=self.name,
                        source=_BLS_URL,
                        retrieved_at=retrieved_at,
                        country="US",
                        region="USA",
                        confidence_score=1.0,
                        indicator_id="BLS_UNEMPLOYMENT",
                        name="US Unemployment Rate (BLS)",
                        value=value,
                        unit="%",
                        period=period_label,
                        frequency="monthly",
                    )
                )

            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "No data in response",
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
