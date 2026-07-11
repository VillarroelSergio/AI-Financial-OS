"""European Central Bank adapter — key interest rate and EUR/USD exchange rate."""
import csv
import io
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    CurrencyRate,
    MacroIndicator,
    ProviderMetadata,
)

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_DFR_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV"
    "?format=csvdata&startPeriod=2024-01-01&detail=dataonly"
)
_MRR_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.MRR_FR.LEV"
    "?format=csvdata&startPeriod=2024-01-01&detail=dataonly"
)
# ECO-2: Euríbor. EMMI lo administra pero el BCE lo publica en su dataset FM (dataflow
# monetario). El daily (freq B) fue discontinuado → solo hay mensual (freq M), verificado
# en vivo 2026-07-06. El catálogo declara frequency: daily; la realidad pública es mensual.
_EURIBOR_3M_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA"
    "?format=csvdata&startPeriod=2024-01&detail=dataonly"
)
_EURIBOR_12M_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA"
    "?format=csvdata&startPeriod=2024-01&detail=dataonly"
)
_ECB_FX_QUOTES = ("USD", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY")

# Tasas de política monetaria del BCE que este adapter sirve, por catalog id.
_RATE_SERIES: dict[str, tuple[str, str]] = {
    "deposit_facility_eurozone": (_DFR_URL, "ECB Deposit Facility Rate"),
    "tipo_bce": (_MRR_URL, "Tipo de interés BCE (MRR)"),
    "euribor_3m": (_EURIBOR_3M_URL, "Euríbor 3 meses (BCE)"),
    "euribor_12m": (_EURIBOR_12M_URL, "Euríbor 12 meses (BCE)"),
}
# Pares forex EUR/x servidos por el BCE (base EUR), por catalog id → divisa cotizada.
_FX_PAIRS: dict[str, str] = {
    "eur_usd": "USD", "eur_gbp": "GBP", "eur_jpy": "JPY",
    "eur_chf": "CHF", "eur_cad": "CAD", "eur_aud": "AUD",
}


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
    # allowlist honesta: 2 tasas de política (DFR, MRR) + pares forex EUR/x.
    # Antes fetch() ignoraba el id y devolvía DFR+7 FX para cualquier indicador →
    # el mismo valor caía bajo varios ids (clon). Ahora se sirve solo lo pedido.
    supported_indicators = {**{k: {} for k in _RATE_SERIES}, **{k: {} for k in _FX_PAIRS}}

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        try:
            if indicator_id in _RATE_SERIES:
                url, name = _RATE_SERIES[indicator_id]
                records, raw = self._fetch_rate(url, name)
            elif indicator_id in _FX_PAIRS:
                records, raw = self._fetch_fx(_FX_PAIRS[indicator_id])
            elif indicator_id is None:
                # Health-check / legacy: DFR + todos los FX de referencia.
                records, raw = self._fetch_rate(_DFR_URL, "ECB Deposit Facility Rate")
                for quote in _ECB_FX_QUOTES:
                    fx_records, _ = self._fetch_fx(quote)
                    records.extend(fx_records)
            else:
                return AdapterResult(
                    provider=self.name, success=False, records=[],
                    error=f"ECB no sirve '{indicator_id}'", latency_ms=0.0,
                    raw_sample=None, metadata=metadata,
                )
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.time() - t0) * 1000, raw_sample=None, metadata=metadata,
            )

        return AdapterResult(
            provider=self.name, success=bool(records), records=records,
            error=None if records else "No data parsed",
            latency_ms=(time.time() - t0) * 1000, raw_sample=raw, metadata=metadata,
        )

    def _fetch_rate(self, url: str, name: str) -> tuple[list, dict | None]:
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        rows = _parse_csv_last_rows(r.text, n=1)
        if not rows:
            return [], {"preview": r.text[:500]}
        row = rows[-1]
        obs_val = row.get("OBS_VALUE", "")
        if not obs_val:
            return [], {"preview": r.text[:500]}
        return [
            MacroIndicator(
                provider=self.name, source=url, retrieved_at=datetime.now(timezone.utc),
                country="EA", region="Eurozone", confidence_score=1.0,
                indicator_id="ECB_RATE", name=name, value=float(obs_val),
                unit="%", period=row.get("TIME_PERIOD", ""), frequency="irregular",
            )
        ], {"preview": r.text[:500]}

    def _fetch_fx(self, quote: str) -> tuple[list, dict | None]:
        fx_url = (
            f"https://data-api.ecb.europa.eu/service/data/EXR/D.{quote}.EUR.SP00.A"
            "?format=csvdata&detail=dataonly&lastNObservations=1"
        )
        r = requests.get(fx_url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        rows = _parse_csv_last_rows(r.text, n=1)
        if not rows:
            return [], None
        row = rows[-1]
        obs_val = row.get("OBS_VALUE", "")
        if not obs_val:
            return [], None
        period = row.get("TIME_PERIOD", "")
        return [
            CurrencyRate(
                provider=self.name, source=fx_url, retrieved_at=datetime.now(timezone.utc),
                country="EA", region="Eurozone", confidence_score=1.0,
                base_currency="EUR", quote_currency=quote, rate=float(obs_val),
                date=datetime.fromisoformat(period).date() if period else None,
                frequency="daily",
            )
        ], None
