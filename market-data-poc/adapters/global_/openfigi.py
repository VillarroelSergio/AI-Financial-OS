"""OpenFIGI adapter - map a ticker to FIGI metadata."""
import time
from datetime import datetime, timezone

import requests

from adapters.base import BaseAdapter
from config.settings import get_api_key
from models.base import AdapterResult
from models.company import CompanyProfile

_BASE_URL = "https://api.openfigi.com/v3/mapping"


class OpenFIGIAdapter(BaseAdapter):
    name = "OpenFIGI"
    category = "companies"
    region = "Global"
    requires_api_key = False
    api_key_names = ("OPENFIGI",)
    capabilities = ("stocks", "etf", "funds", "isin")
    priority = "secondary"

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("OPENFIGI")
        metadata = self._make_metadata(
            id="openfigi",
            base_url=_BASE_URL,
            method="api",
            license="open",
            declared_update_frequency="daily",
            declared_historical_depth_years=0,
            notes="Instrument identifier mapping.",
        )
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-OPENFIGI-APIKEY"] = api_key
        payload = [{"idType": "TICKER", "idValue": "AAPL", "exchCode": "US"}]
        t0 = time.perf_counter()
        try:
            response = requests.post(_BASE_URL, json=payload, headers=headers, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            item = data[0]["data"][0]
            record = CompanyProfile(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=datetime.now(timezone.utc),
                country=item.get("marketSector", "US"),
                region=self.region,
                confidence_score=0.9,
                symbol=item.get("ticker", "AAPL"),
                name=item.get("name", ""),
                exchange=item.get("exchCode", ""),
            )
            return AdapterResult(
                provider=self.name,
                success=True,
                records=[record],
                error=None,
                latency_ms=latency_ms,
                raw_sample={"figi": item.get("figi"), "securityType": item.get("securityType")},
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


Adapter = OpenFIGIAdapter
