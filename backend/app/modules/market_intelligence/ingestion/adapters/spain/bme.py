"""BME (Bolsas y Mercados Españoles) adapter — IBEX 35."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MarketQuote

_PRIMARY_URL = (
    "https://www.bolsasymercados.es/bme-exchange/es/Indices/Renta-Variable"
    "/Indices-Tiempo-Real/IBEX-35/ES0SI0000005"
)
_FALLBACK_URL = "https://www.bolsasymercados.es/bme-exchange/en/Indices/Historical"
_OPEN_DATA_URL = (
    "https://www.bolsasymercados.es/esp/Indices/Renta-Variable/Composicion-IBEX-35"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FinancialAgentPOC/1.0; +https://github.com/FinancialAgent)"
    )
}


class BMEAdapter(BaseAdapter):
    name = "BME"
    category = "markets"
    region = "Spain"
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            r = requests.get(_PRIMARY_URL, timeout=10, headers=_HEADERS)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()

        for url in (_PRIMARY_URL, _FALLBACK_URL, _OPEN_DATA_URL):
            try:
                r = requests.get(url, timeout=10, headers=_HEADERS)
                latency_ms = (time.time() - t0) * 1000
                if r.status_code != 200:
                    continue
                content_type = r.headers.get("Content-Type", "")
                if "json" in content_type:
                    return self._handle_json(r.json(), latency_ms, url, metadata)
                # HTML — partial result
                return self._handle_html_partial(r.text, latency_ms, url, metadata)
            except Exception:
                continue

        latency_ms = (time.time() - t0) * 1000
        return AdapterResult(
            provider=self.name,
            success=False,
            records=[],
            error="All BME URLs failed or returned non-200",
            latency_ms=latency_ms,
            raw_sample=None,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _handle_json(self, data, latency_ms: float, url: str, metadata) -> AdapterResult:
        retrieved_at = datetime.now(timezone.utc)
        # Try to extract a price value from common BME JSON shapes
        value = None
        if isinstance(data, dict):
            value = (
                data.get("ultimo")
                or data.get("last")
                or data.get("price")
                or data.get("valor")
            )
        record = MarketQuote(
            provider=self.name,
            source=url,
            retrieved_at=retrieved_at,
            country="Spain",
            region=self.region,
            confidence_score=0.8,
            symbol="IBEX",
            name="IBEX 35",
            asset_type="index",
            price=float(value) if value is not None else None,
            currency="EUR",
        )
        return AdapterResult(
            provider=self.name,
            success=True,
            records=[record],
            error=None,
            latency_ms=latency_ms,
            raw_sample=data if isinstance(data, dict) else (data[0] if data else None),
            metadata=metadata,
        )

    def _handle_html_partial(self, html: str, latency_ms: float, url: str, metadata) -> AdapterResult:
        retrieved_at = datetime.now(timezone.utc)
        if not html or len(html) < 100:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error="Empty HTML response from BME",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        # Try a quick regex scan for a numeric price in the HTML
        import re
        price = None
        match = re.search(r'["\s>](\d{1,5}[.,]\d{2,3})["\s<]', html)
        if match:
            try:
                price = float(match.group(1).replace(",", "."))
            except ValueError:
                price = None
        if price is None:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error="BME HTML response did not expose an index price",
                latency_ms=latency_ms,
                raw_sample={"html_length": len(html), "url": url},
                metadata=metadata,
            )

        record = MarketQuote(
            provider=self.name,
            source=url,
            retrieved_at=retrieved_at,
            country="Spain",
            region=self.region,
            confidence_score=0.3,  # Only HTML available
            symbol="IBEX",
            name="IBEX 35",
            asset_type="index",
            price=price,
            currency="EUR",
        )
        return AdapterResult(
            provider=self.name,
            success=True,
            records=[record],
            error=None,
            latency_ms=latency_ms,
            raw_sample={"html_length": len(html), "url": url, "price_extracted": price},
            metadata=metadata,
        )
