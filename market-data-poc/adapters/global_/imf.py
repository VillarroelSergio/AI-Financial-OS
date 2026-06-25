"""IMF adapter — GDP growth forecasts via DataMapper API."""
import time
import requests
from datetime import datetime, timezone

from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator
from adapters.base import BaseAdapter

_URL = "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/ESP/USA/DEU?periods=2023,2024,2025"

_COUNTRY_MAP = {
    "ESP": "ES",
    "USA": "US",
    "DEU": "DE",
}


class IMFAdapter(BaseAdapter):
    name = "IMF"
    category = "macro"
    region = "Global"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_URL, method="api", license="IMF Data")
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
            country_data = data["values"]["NGDP_RPCH"]  # {country: {year: value}}
            retrieved_at = datetime.now(timezone.utc)
            records = []
            for imf_code, year_values in country_data.items():
                iso = _COUNTRY_MAP.get(imf_code, imf_code)
                for year, value in year_values.items():
                    if value is None:
                        continue
                    records.append(
                        MacroIndicator(
                            provider=self.name,
                            source=_URL,
                            retrieved_at=retrieved_at,
                            country=iso,
                            region=self.region,
                            confidence_score=0.95,
                            indicator_id=f"IMF_GDP_GROWTH_{imf_code}",
                            name=f"GDP Growth Forecast ({imf_code})",
                            value=float(value),
                            unit="%",
                            period=str(year),
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
            raw_sample={"countries": list(country_data.keys())},
            metadata=metadata,
        )
