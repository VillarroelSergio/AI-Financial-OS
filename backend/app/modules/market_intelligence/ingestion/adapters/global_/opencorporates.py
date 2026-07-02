"""OpenCorporates adapter with optional API key semantics."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.config import get_api_key
from app.modules.market_intelligence.ingestion.models import AdapterResult, CompanyProfile

_BASE_URL = "https://api.opencorporates.com/v0.4/companies/search"
_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}


class OpenCorporatesAdapter(BaseAdapter):
    name = "OpenCorporates"
    category = "companies"
    region = "Global"
    requires_api_key = True
    api_key_names = ("OPENCORPORATES",)
    capabilities = ("companies", "corporate_actions")
    priority = "fallback"

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(
            id="opencorporates",
            base_url=_BASE_URL,
            method="api",
            license="freemium",
            declared_update_frequency="daily",
            declared_historical_depth_years=20,
            notes="Company registry search API. Requires OPENCORPORATES_API_KEY for reliable access.",
        )
        api_key = get_api_key("OPENCORPORATES")
        t0 = time.perf_counter()
        try:
            response = requests.get(
                _BASE_URL,
                params={"q": "Apple Inc", "api_token": api_key},
                headers=_HEADERS,
                timeout=10,
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            data = response.json()
            company = ((data.get("results") or {}).get("companies") or [{}])[0].get("company", {})
            record = CompanyProfile(
                provider=self.name,
                source=response.url.replace(api_key or "", "***"),
                retrieved_at=datetime.now(timezone.utc),
                country=company.get("jurisdiction_code", "GLOBAL").upper(),
                region=self.region,
                confidence_score=0.8,
                name=company.get("name", "Apple Inc"),
                sector="",
                industry="",
            )
            return AdapterResult(
                provider=self.name,
                success=bool(company),
                records=[record] if company else [],
                error=None if company else "OpenCorporates returned no company results",
                latency_ms=latency_ms,
                raw_sample={"total_count": (data.get("results") or {}).get("total_count")},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc).replace(api_key or "", "***"),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None,
                metadata=metadata,
            )


Adapter = OpenCorporatesAdapter
