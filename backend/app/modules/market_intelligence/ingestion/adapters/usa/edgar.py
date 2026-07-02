"""SEC EDGAR adapter — Apple Inc company profile and financial facts."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    CompanyProfile,
    ProviderMetadata,
)

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK0000320193.json"
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"

# SIC code -> sector description (partial mapping)
_SIC_SECTORS = {
    "3674": "Semiconductors & Electronic Components",
    "7372": "Prepackaged Software",
    "5045": "Computers & Peripherals (Wholesale)",
    "3571": "Electronic Computers",
    "3669": "Communications Equipment",
}


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="SEC EDGAR",
        id="sec_edgar",
        category="companies",
        region="USA",
        method="api",
        base_url="https://data.sec.gov",
        requires_api_key=False,
        declared_update_frequency="as filed",
        declared_historical_depth_years=25,
        license="Public Domain (SEC)",
        notes="SEC EDGAR XBRL data — no API key required; fair-use rate limits apply",
    )


class EDGARAdapter(BaseAdapter):
    name = "SEC EDGAR"
    category = "companies"
    region = "USA"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)
        raw_sample: dict | None = None

        try:
            r = requests.get(_SUBMISSIONS_URL, headers=_HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()
            raw_text = r.text[:500]
            raw_sample = {"submissions_preview": raw_text}

            company_name = data.get("name", "Apple Inc.")
            sic = str(data.get("sic", "3571"))
            tickers = data.get("tickers", ["AAPL"])
            exchanges = data.get("exchanges", ["Nasdaq"])
            symbol = tickers[0] if tickers else "AAPL"
            exchange = exchanges[0] if exchanges else "Nasdaq"
            sector = _SIC_SECTORS.get(sic, f"SIC {sic}")

            # Represent company as a MarketQuote (placeholder price — EDGAR has no prices)
            profile = CompanyProfile(
                provider=self.name,
                source=_SUBMISSIONS_URL,
                retrieved_at=retrieved_at,
                country="US",
                region="USA",
                confidence_score=1.0,
                symbol=symbol,
                name=company_name,
                sector=sector,
                exchange=exchange,
            )

            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=True,
                records=[profile],
                error=None,
                latency_ms=latency_ms,
                raw_sample={
                    "submissions_preview": raw_text,
                    "sector": sector,
                    "exchange": exchange,
                    "sic": sic,
                },
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
                raw_sample=raw_sample,
                metadata=metadata,
            )
