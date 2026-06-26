"""Tesoro Público adapter — Spanish government bond yields."""
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MacroIndicator

_PRIMARY_URL = (
    "https://www.tesoro.es/sites/default/files/estadisticas/fondos"
    "/series-historicas-deuda-estado-2024.json"
)
_FALLBACK_URL = (
    "https://www.tesoro.es/sites/default/files/estadisticas/fondos"
    "/emisiones-letras-tesoro.json"
)


class TesoroAdapter(BaseAdapter):
    name = "Tesoro Público"
    category = "macro"
    region = "Spain"
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            r = requests.get(_PRIMARY_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()

        data = None
        used_url = None
        latency_ms = 0.0
        last_error = None

        for url in (_PRIMARY_URL, _FALLBACK_URL):
            try:
                r = requests.get(url, timeout=10)
                latency_ms = (time.time() - t0) * 1000
                r.raise_for_status()
                data = r.json()
                used_url = url
                break
            except Exception as exc:
                last_error = str(exc)

        if data is None:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=last_error or "All Tesoro URLs failed",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        try:
            records = self._parse(data, used_url)
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"Parse error: {exc}",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        raw_sample = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else None)
        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _parse(self, data, source_url: str) -> list:
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []

        # Normalise: accept list or dict with an items/data key
        items = data if isinstance(data, list) else data.get("data", data.get("items", [data]))

        # Take last 3 items
        for item in items[-3:]:
            if not isinstance(item, dict):
                continue
            # Try common field names for yield/tasa and period
            value = (
                item.get("tasa")
                or item.get("rendimiento")
                or item.get("tipo")
                or item.get("yield")
                or item.get("valor")
            )
            period = (
                item.get("fecha")
                or item.get("period")
                or item.get("fecha_emision")
                or "N/A"
            )
            if value is None:
                continue
            records.append(
                MacroIndicator(
                    provider=self.name,
                    source=source_url,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.9,
                    indicator_id="BONO_10Y",
                    name="Bono España 10 años",
                    value=float(value),
                    unit="%",
                    period=str(period),
                    frequency="monthly",
                )
            )
        return records
