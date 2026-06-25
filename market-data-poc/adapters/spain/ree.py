"""REE (Red Eléctrica de España) adapter — electricity market prices."""
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_URL = (
    "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
    "?start_date=2024-01-01T00:00&end_date=2024-01-02T23:59&time_trunc=hour"
)


class REEAdapter(BaseAdapter):
    name = "REE"
    category = "macro"
    region = "Spain"
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            r = requests.head(_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_URL)
        t0 = time.time()
        try:
            r = requests.get(_URL, timeout=10, headers={"Accept": "application/json"})
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

        # raw_sample: first value entry
        raw_sample = None
        try:
            raw_sample = data["included"][0]["attributes"]["values"][0]
        except (KeyError, IndexError, TypeError):
            pass

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
        # Shape: data["included"][0]["attributes"]["values"] = [{value, datetime, percentage}, ...]
        included = data.get("included", [])
        if not included:
            raise ValueError("No 'included' key in REE response")

        values = included[0].get("attributes", {}).get("values", [])
        if not values:
            raise ValueError("No values in REE included[0].attributes.values")

        # Return last 3 hourly records
        records: list[MacroIndicator] = []
        for entry in values[-3:]:
            value = entry.get("value")
            dt_str = entry.get("datetime", "")
            percentage = entry.get("percentage")
            if value is None:
                continue
            records.append(
                MacroIndicator(
                    provider=self.name,
                    source=_URL,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.95,
                    indicator_id="PRECIO_ELECTRICIDAD",
                    name="Precio mercado eléctrico España",
                    value=float(value),
                    unit="€/MWh",
                    period=dt_str,
                    frequency="hourly",
                )
            )
        return records
