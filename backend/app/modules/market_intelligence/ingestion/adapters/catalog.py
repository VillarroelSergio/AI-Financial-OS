"""PublicDatasetAdapter — adapter para datasets públicos.

Adaptado de market-data-poc/adapters/catalog.py.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroSeries, MarketNews

_HEADERS = {"User-Agent": "AIFinancialOS/0.1 contact@example.com"}


class PublicDatasetAdapter(BaseAdapter):
    name = ""
    provider_id = ""
    category = "macro"
    region = "Global"
    base_url = ""
    notes = ""
    capabilities = ()
    priority = "fallback"
    method = "api"
    license = "open"
    update_frequency = "unknown"
    historical_depth_years = 0

    def is_available(self) -> bool:
        if not self.base_url:
            return False
        try:
            response = requests.get(self.base_url, headers=_HEADERS, timeout=10)
            return response.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = self._make_metadata(
            id=self.provider_id,
            base_url=self.base_url,
            method=self.method,
            license=self.license,
            notes=self.notes,
            declared_update_frequency=self.update_frequency,
            declared_historical_depth_years=self.historical_depth_years,
        )
        t0 = time.perf_counter()
        try:
            response = requests.get(self.base_url, headers=_HEADERS, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            response.raise_for_status()
            record = self._record(response)
            return AdapterResult(
                provider=self.name, success=True, records=[record],
                error=None, latency_ms=latency_ms,
                raw_sample={"status_code": response.status_code, "preview": response.text[:500]},
                metadata=metadata,
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.perf_counter() - t0) * 1000,
                raw_sample=None, metadata=metadata,
            )

    def _record(self, response):
        retrieved_at = datetime.now(timezone.utc)
        if self.category == "news":
            return MarketNews(
                provider=self.name, source=self.base_url, retrieved_at=retrieved_at,
                country="GLOBAL", region=self.region, confidence_score=0.6,
                title=f"{self.name} public feed reachable", url=self.base_url,
                source_name=self.name,
            )
        return MacroSeries(
            provider=self.name, source=self.base_url, retrieved_at=retrieved_at,
            country=self.region if self.region in ("Spain", "USA") else "GLOBAL",
            region=self.region, confidence_score=0.7,
            series_id=self.provider_id, name=self.name,
            frequency=self.update_frequency, observations=[],
        )
