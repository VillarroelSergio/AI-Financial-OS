"""INE (Instituto Nacional de Estadística) adapter — IPC General España."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroIndicator

_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC206449?nult=3"


class INEAdapter(BaseAdapter):
    name = "INE"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {"ipc_general": {}}

    def is_available(self) -> bool:
        try:
            r = requests.head(_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = self._make_metadata(base_url=_URL)
        t0 = time.time()
        try:
            r = requests.get(_URL, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
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

        try:
            records = self._parse(data)
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

        raw_items = data.get("Data", [])
        raw_sample = raw_items[0] if raw_items else None
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
    def _parse(self, data: dict) -> list:
        retrieved_at = datetime.now(timezone.utc)
        items = data.get("Data", [])
        records: list[MacroIndicator] = []
        for item in items:
            anyo = item.get("Anyo", "")
            periodo = item.get("Periodo", "")
            valor = item.get("Valor")
            if valor is None:
                continue
            period = f"{anyo}-{periodo}"
            records.append(
                MacroIndicator(
                    provider=self.name,
                    source=_URL,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.95,
                    indicator_id="IPC_GENERAL",
                    name="IPC General España",
                    value=float(valor),
                    unit="%",
                    period=period,
                    frequency="monthly",
                )
            )
        return records
