"""Financial Modeling Prep adapter — AAPL company profile."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import AdapterResult
from app.modules.market_intelligence.ingestion.models import CompanyProfile
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.config import get_api_key

_BASE_URL = "https://financialmodelingprep.com/stable/profile"


class FMPAdapter(BaseAdapter):
    name = "Financial Modeling Prep"
    category = "companies"
    region = "Global"
    requires_api_key = True
    api_key_names = ("FMP", "FINANCIAL_MODELING_PREP")

    def fetch(self) -> AdapterResult:
        api_key = get_api_key("FMP") or get_api_key("FINANCIAL_MODELING_PREP")
        metadata = self._make_metadata(base_url=_BASE_URL, method="api", license="FMP")
        t0 = time.time()
        try:
            r = requests.get(_BASE_URL, params={"symbol": "AAPL", "apikey": api_key}, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=_redact_api_key(str(exc), api_key),
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        try:
            item = data[0]
            retrieved_at = datetime.now(timezone.utc)
            record = CompanyProfile(
                provider=self.name,
                source=_BASE_URL,
                retrieved_at=retrieved_at,
                country="US",
                region=self.region,
                confidence_score=1.0,
                symbol=item["symbol"],
                name=item["companyName"],
                sector=item.get("sector", ""),
                industry=item.get("industry", ""),
                market_cap=float(item.get("marketCap") or item.get("mktCap") or 0),
                exchange=item.get("exchange") or item.get("exchangeShortName", ""),
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"Parse error: {exc}",
                latency_ms=latency_ms,
                raw_sample={"raw": data},
                metadata=metadata,
            )

        return AdapterResult(
            provider=self.name,
            success=True,
            records=[record],
            error=None,
            latency_ms=latency_ms,
            raw_sample={"symbol": item["symbol"], "name": item["companyName"]},
            metadata=metadata,
        )


def _redact_api_key(value: str, api_key: str | None) -> str:
    return value.replace(api_key, "***") if api_key else value
