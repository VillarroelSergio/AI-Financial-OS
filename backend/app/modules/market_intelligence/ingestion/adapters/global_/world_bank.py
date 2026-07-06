"""World Bank adapter — Spain GDP (NY.GDP.MKTP.CN, moneda local = EUR)."""
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroIndicator

# NY.GDP.MKTP.CN = PIB en moneda local (EUR para España). El catálogo declara
# unit "EUR bn", así que se escala a miles de millones antes de persistir.
_URL = "https://api.worldbank.org/v2/country/ES/indicator/NY.GDP.MKTP.CN?format=json&mrv=5"


class WorldBankAdapter(BaseAdapter):
    name = "World Bank"
    category = "macro"
    region = "Global"
    requires_api_key = False
    # Solo sirve PIB España (NY.GDP.MKTP.CN, nivel EUR bn). Estaba como fallback de
    # gdp_usa y otros → devolvía PIB España para todos (clon). allowlist honesta.
    supported_indicators = {"pib_spain": {}}

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_URL, method="api", license="CC BY 4.0")
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
            entries = data[1]  # list of {date, value, country.value}
            retrieved_at = datetime.now(timezone.utc)
            records = []
            for entry in entries:
                if entry.get("value") is None:
                    continue
                records.append(
                    MacroIndicator(
                        provider=self.name,
                        source=_URL,
                        retrieved_at=retrieved_at,
                        country="ES",
                        region=self.region,
                        confidence_score=1.0,
                        indicator_id="WB_ESP_GDP",
                        name="Spain GDP (World Bank)",
                        value=round(float(entry["value"]) / 1e9, 2),
                        unit="EUR bn",
                        period=str(entry["date"]),
                        frequency="annual",
                    )
                )
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

        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample={"sample": entries[0] if entries else {}},
            metadata=metadata,
        )
