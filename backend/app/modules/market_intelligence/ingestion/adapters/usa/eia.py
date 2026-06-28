"""EIA adapter - WTI spot price from the v2 API."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.config import get_api_key
from app.modules.market_intelligence.ingestion.models import Commodity
from app.modules.market_intelligence.ingestion.models import AdapterResult

_BASE_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"


class EIAAdapter(BaseAdapter):
    name = "EIA"
    category = "macro"
    region = "USA"
    requires_api_key = True
    api_key_names = ("EIA",)
    capabilities = ("macro", "commodities", "energy", "historical")
    priority = "secondary"

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("EIA")
        metadata = self._make_metadata(
            id="eia",
            base_url=_BASE_URL,
            method="api",
            license="open",
            declared_update_frequency="daily",
            declared_historical_depth_years=30,
            notes="US Energy Information Administration API.",
        )
        t0 = time.perf_counter()
        params = {
            "api_key": api_key,
            "frequency": "daily",
            "data[0]": "value",
            "facets[series][]": "RWTC",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 1,
        }
        try:
            response = requests.get(_BASE_URL, params=params, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            item = data["response"]["data"][0]
            record = Commodity(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=datetime.now(timezone.utc),
                country="US",
                region=self.region,
                confidence_score=1.0,
                symbol="WTI",
                name="WTI Crude Oil Spot Price",
                price=float(item["value"]),
                unit=item.get("units", "USD/bbl"),
                currency="USD",
            )
            return AdapterResult(
                provider=self.name,
                success=True,
                records=[record],
                error=None,
                latency_ms=latency_ms,
                raw_sample={"period": item.get("period"), "series": item.get("series")},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=_redact_api_key(str(exc), api_key),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None,
                metadata=metadata,
            )


def _redact_api_key(value: str, api_key: str | None) -> str:
    return value.replace(api_key, "***") if api_key else value


Adapter = EIAAdapter
