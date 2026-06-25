"""European Central Bank adapter — key interest rate and EUR/USD exchange rate."""
import csv
import io
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.assets import CurrencyRate
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_DFR_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV"
    "?format=csvdata&startPeriod=2024-01-01&detail=dataonly"
)
_ECB_FX_QUOTES = ("USD", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY")


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="ECB",
        id="ecb",
        category="macro",
        region="Eurozone",
        method="api",
        base_url="https://data-api.ecb.europa.eu",
        requires_api_key=False,
        declared_update_frequency="irregular",
        declared_historical_depth_years=30,
        license="ECB Open Data",
        notes="ECB Statistical Data Warehouse (SDW) API",
        capabilities=("macro", "currency", "forex", "historical"),
        priority="primary",
    )


def _parse_csv_last_rows(text: str, n: int = 1) -> list[dict]:
    """Parse ECB csvdata format and return last n data rows as dicts."""
    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader]
    return rows[-n:] if rows else []


class ECBAdapter(BaseAdapter):
    name = "ECB"
    category = "macro"
    region = "Eurozone"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []
        raw_sample: dict | None = None

        try:
            # --- Deposit Facility Rate ---
            r_dfr = requests.get(_DFR_URL, headers=_HEADERS, timeout=10)
            r_dfr.raise_for_status()
            dfr_rows = _parse_csv_last_rows(r_dfr.text, n=1)
            if dfr_rows:
                row = dfr_rows[-1]
                # ECB csvdata: columns include TIME_PERIOD and OBS_VALUE
                period = row.get("TIME_PERIOD", "")
                obs_val = row.get("OBS_VALUE", "")
                raw_sample = {"dfr_preview": r_dfr.text[:500]}
                if obs_val:
                    records.append(
                        MacroIndicator(
                            provider=self.name,
                            source=_DFR_URL,
                            retrieved_at=retrieved_at,
                            country="EA",
                            region="Eurozone",
                            confidence_score=1.0,
                            indicator_id="ECB_DFR",
                            name="ECB Deposit Facility Rate",
                            value=float(obs_val),
                            unit="%",
                            period=period,
                            frequency="irregular",
                        )
                    )

            # --- EUR FX reference rates ---
            for quote in _ECB_FX_QUOTES:
                fx_url = (
                    f"https://data-api.ecb.europa.eu/service/data/EXR/D.{quote}.EUR.SP00.A"
                    "?format=csvdata&detail=dataonly&lastNObservations=1"
                )
                r_fx = requests.get(fx_url, headers=_HEADERS, timeout=10)
                r_fx.raise_for_status()
                fx_rows = _parse_csv_last_rows(r_fx.text, n=1)
                if not fx_rows:
                    continue
                row = fx_rows[-1]
                period = row.get("TIME_PERIOD", "")
                obs_val = row.get("OBS_VALUE", "")
                if not obs_val:
                    continue
                records.append(
                    CurrencyRate(
                        provider=self.name,
                        source=fx_url,
                        retrieved_at=retrieved_at,
                        country="EA",
                        region="Eurozone",
                        confidence_score=1.0,
                        base_currency="EUR",
                        quote_currency=quote,
                        rate=float(obs_val),
                        date=datetime.fromisoformat(period).date() if period else None,
                        frequency="daily",
                    )
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

        latency_ms = (time.time() - t0) * 1000
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else "No data parsed",
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )
