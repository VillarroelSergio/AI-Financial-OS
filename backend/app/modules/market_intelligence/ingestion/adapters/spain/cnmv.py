"""CNMV (Comisión Nacional del Mercado de Valores) adapter — registered entities / hechos relevantes."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, CompanyProfile

_PRIMARY_URL = "https://www.cnmv.es/portal/HR/ResultadoBusquedaHR.aspx?nif=&division=1"
_FALLBACK_URL = "https://www.cnmv.es/portal/Publicaciones/ListadoFondos.aspx"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MarketDataPOC/0.1)"}


class CNMVAdapter(BaseAdapter):
    name = "CNMV"
    category = "companies"
    region = "Spain"
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            r = requests.get(_PRIMARY_URL, timeout=10, headers=_HEADERS)
            return r.status_code not in (403, 404) and r.status_code < 500
        except Exception:
            return False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()

        # Try JSON API first
        try:
            r = requests.get(_PRIMARY_URL, timeout=10, headers=_HEADERS | {"Accept": "application/json"})
            latency_ms = (time.time() - t0) * 1000
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "")
                if "json" in content_type:
                    return self._handle_json(r.json(), latency_ms, metadata)
                # HTML response from primary URL — fall through to partial
                return self._handle_html_partial(r.text, latency_ms, _PRIMARY_URL, metadata)
        except Exception:
            pass

        # Fallback to listing page (HTML)
        try:
            r = requests.get(_FALLBACK_URL, timeout=10, headers=_HEADERS)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            return self._handle_html_partial(r.text, latency_ms, _FALLBACK_URL, metadata)
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

    # ------------------------------------------------------------------
    def _handle_json(self, data, latency_ms: float, metadata) -> AdapterResult:
        retrieved_at = datetime.now(timezone.utc)
        items = data if isinstance(data, list) else data.get("datos", data.get("items", []))
        records: list[CompanyProfile] = []
        for item in items[:5]:
            records.append(
                CompanyProfile(
                    provider=self.name,
                    source=_PRIMARY_URL,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.85,
                    name=item.get("nombre", item.get("denominacion", "Unknown")),
                    symbol=item.get("ticker", item.get("isin", "")),
                    sector=item.get("sector", None),
                )
            )
        raw_sample = items[0] if items else None
        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )

    def _handle_html_partial(self, html: str, latency_ms: float, url: str, metadata) -> AdapterResult:
        """Return a partial/mock CompanyProfile when only HTML is available."""
        retrieved_at = datetime.now(timezone.utc)
        # Confirm the page loaded (has content) and create a representative stub
        if not html or len(html) < 100:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error="Empty HTML response from CNMV",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        stub = CompanyProfile(
            provider=self.name,
            source=url,
            retrieved_at=retrieved_at,
            country="Spain",
            region=self.region,
            confidence_score=0.5,  # Reduced quality — scraped HTML
            name="CNMV — datos parciales (HTML)",
            symbol="CNMV_PARTIAL",
            sector=None,
        )
        return AdapterResult(
            provider=self.name,
            success=True,
            records=[stub],
            error=None,
            latency_ms=latency_ms,
            raw_sample={"html_length": len(html), "url": url},
            metadata=metadata,
        )
