"""Banco de España adapter — indicadores macro de España.

Fuentes usadas (en orden de fiabilidad probada):
  - FRED fredgraph (sin API key): Spain 10Y yield, CPI, Unemployment
  - ECB data-api: tipo de refinanciación (MRR) como proxy de tipos BDE
  - BDE CSV portal: fallback para agregados monetarios (tiende a devolver HTML)

Euribor 3M/12M no disponible sin clave FRED API — el endpoint SDMX de BDE
(sdmx.bde.es) no existe y ECB data-api no publica Euribor en su serie pública.
"""
import csv as _csv
import io
import time
import requests
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult
from app.modules.market_intelligence.ingestion.models import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}
_ECB_BASE = "https://data-api.ecb.europa.eu/service/data"

# FRED fredgraph (no API key necesaria) — series de España confirmadas
_FRED_SERIES: dict[str, dict] = {
    "spain_10y": {
        "id": "IRLTLT01ESM156N",
        "name": "Bono Español 10Y",
        "unit": "%",
        "country": "ES",
        "frequency": "monthly",
    },
    "spain_cpi": {
        "id": "FPCPITOTLZGESP",
        "name": "IPC General España (anual)",
        "unit": "%",
        "country": "ES",
        "frequency": "annual",
    },
    "spain_unemployment": {
        "id": "LRHUTTTTESM156S",
        "name": "Tasa de Desempleo España",
        "unit": "%",
        "country": "ES",
        "frequency": "monthly",
    },
}

# ECB Key rates disponibles en data-api.ecb.europa.eu
_ECB_RATES: dict[str, dict] = {
    "ecb_mrr": {
        "flow": "FM",
        "key": "B.U2.EUR.4F.KR.MRR_FR.LEV",
        "name": "Tipo de Refinanciación BCE",
        "unit": "%",
        "country": "EU",
        "frequency": "irregular",
    },
}

# BDE CSV — fallback, generalmente devuelve HTML pero puede funcionar
_BDE_CSV_URLS = [
    "https://www.bde.es/webbde/es/estadis/infoest/Series/si_1_1.csv",
]


class BDEAdapter(BaseAdapter):
    name = "Banco de España"
    provider_id = "bde"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {k: {} for k in {**_FRED_SERIES, **_ECB_RATES}}

    def is_available(self) -> bool:
        try:
            r = requests.head(
                "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01ESM156N",
                headers=_HEADERS, timeout=8,
            )
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        if indicator_id and indicator_id in _FRED_SERIES:
            return self._fetch_fred(indicator_id)
        if indicator_id and indicator_id in _ECB_RATES:
            return self._fetch_ecb_rate(indicator_id)
        if indicator_id:
            return self._not_supported(indicator_id)
        return self._fetch_all()

    def _fetch_fred(self, indicator_id: str) -> AdapterResult:
        series = _FRED_SERIES[indicator_id]
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series['id']}"
        metadata = self._make_metadata(base_url=url, method="csv")
        t0 = time.time()
        try:
            r = requests.get(url, headers=_HEADERS, timeout=12)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            if r.text.strip().startswith("<"):
                raise ValueError("Got HTML instead of CSV")
            records = self._parse_fred_csv(r.text, indicator_id, series)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"FRED error for {indicator_id}: {exc}",
                latency_ms=latency_ms, raw_sample=None, metadata=metadata,
            )
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else f"No observations for {indicator_id}",
            latency_ms=latency_ms,
            raw_sample=None,
            metadata=metadata,
        )

    def _fetch_ecb_rate(self, indicator_id: str) -> AdapterResult:
        series = _ECB_RATES[indicator_id]
        url = (
            f"{_ECB_BASE}/{series['flow']}/{series['key']}"
            "?format=csvdata&detail=dataonly&lastNObservations=3"
        )
        metadata = self._make_metadata(base_url=url, method="api")
        t0 = time.time()
        try:
            r = requests.get(url, headers=_HEADERS, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            records = self._parse_ecb_csv(r.text, indicator_id, series)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"ECB error for {indicator_id}: {exc}",
                latency_ms=latency_ms, raw_sample=None, metadata=metadata,
            )
        return AdapterResult(
            provider=self.name, success=bool(records), records=records,
            error=None if records else f"No ECB data for {indicator_id}",
            latency_ms=latency_ms, raw_sample=None, metadata=metadata,
        )

    def _fetch_all(self) -> AdapterResult:
        metadata = self._make_metadata(base_url="https://fred.stlouisfed.org", method="csv")
        t0 = time.time()
        all_records: list[MacroIndicator] = []
        errors: list[str] = []

        for ind_id in _FRED_SERIES:
            res = self._fetch_fred(ind_id)
            if res.success:
                all_records.extend(res.records)
            else:
                errors.append(res.error or ind_id)

        for ind_id in _ECB_RATES:
            res = self._fetch_ecb_rate(ind_id)
            if res.success:
                all_records.extend(res.records)
            else:
                errors.append(res.error or ind_id)

        # BDE CSV fallback
        csv_recs, csv_err = self._try_bde_csv()
        all_records.extend(csv_recs)
        if csv_err:
            errors.append(csv_err)

        latency_ms = (time.time() - t0) * 1000
        return AdapterResult(
            provider=self.name,
            success=bool(all_records),
            records=all_records,
            error=("; ".join(errors) if not all_records and errors else None),
            latency_ms=latency_ms,
            raw_sample=None,
            metadata=metadata,
        )

    def _parse_fred_csv(self, text: str, indicator_id: str, series: dict) -> list[MacroIndicator]:
        retrieved_at = datetime.now(timezone.utc)
        reader = _csv.DictReader(io.StringIO(text))
        records: list[MacroIndicator] = []
        rows = list(reader)
        # Últimas 6 observaciones (excluir '.' que significa dato no disponible)
        for row in rows[-6:]:
            date_str = row.get("observation_date", row.get("DATE", "")).strip()
            val_str = row.get(series["id"], "").strip()
            if not val_str or val_str == ".":
                continue
            try:
                value = float(val_str)
            except ValueError:
                continue
            records.append(MacroIndicator(
                provider=self.name,
                source=f"https://fred.stlouisfed.org/series/{series['id']}",
                retrieved_at=retrieved_at,
                country=series["country"],
                region=self.region,
                confidence_score=0.96,
                indicator_id=indicator_id,
                name=series["name"],
                value=value,
                unit=series["unit"],
                period=date_str,
                frequency=series["frequency"],
            ))
        return records

    def _parse_ecb_csv(self, text: str, indicator_id: str, series: dict) -> list[MacroIndicator]:
        retrieved_at = datetime.now(timezone.utc)
        reader = _csv.DictReader(io.StringIO(text))
        records: list[MacroIndicator] = []
        for row in reader:
            period = row.get("TIME_PERIOD", "").strip()
            obs_val = row.get("OBS_VALUE", "").strip()
            if not obs_val or not period:
                continue
            try:
                value = float(obs_val)
            except ValueError:
                continue
            records.append(MacroIndicator(
                provider=self.name,
                source=f"{_ECB_BASE}/{series['flow']}/{series['key']}",
                retrieved_at=retrieved_at,
                country=series["country"],
                region=self.region,
                confidence_score=0.98,
                indicator_id=indicator_id,
                name=series["name"],
                value=value,
                unit=series["unit"],
                period=period,
                frequency=series["frequency"],
            ))
        return records

    def _try_bde_csv(self) -> tuple[list[MacroIndicator], str | None]:
        for url in _BDE_CSV_URLS:
            try:
                r = requests.get(url, headers=_HEADERS, timeout=10)
                if r.status_code != 200:
                    continue
                text = r.text
                if text.strip().startswith("<") or "<!DOCTYPE" in text[:200]:
                    return [], "BDE CSV devuelve HTML (portal sin acceso directo)"
                records = _parse_bde_csv_rows(text, url, self.name, self.region)
                if records:
                    return records, None
            except Exception as exc:
                return [], str(exc)
        return [], "BDE CSV no accesible"

    def _not_supported(self, indicator_id: str) -> AdapterResult:
        metadata = self._make_metadata(base_url="", method="csv")
        return AdapterResult(
            provider=self.name, success=False, records=[],
            error=f"BDE adapter no soporta '{indicator_id}' (sin endpoint disponible)",
            latency_ms=0.0, raw_sample=None, metadata=metadata,
        )


def _parse_bde_csv_rows(raw_text: str, url: str, provider: str, region: str) -> list[MacroIndicator]:
    retrieved_at = datetime.now(timezone.utc)
    lines = raw_text.splitlines()
    header_line = None
    data_lines = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if header_line is None and (";" in s or ",") and not s[0].isdigit():
            header_line = s
            continue
        if s[0].isdigit() or (len(s) > 4 and s[1:5].isdigit()):
            data_lines.append(s)
    if not data_lines:
        return []
    delimiter = ";" if (header_line or "").count(";") >= (header_line or "").count(",") else ","
    rows = list(_csv.reader(data_lines[-5:], delimiter=delimiter))
    headers = list(_csv.reader([header_line], delimiter=delimiter))[0] if header_line else []
    records: list[MacroIndicator] = []
    for row in rows:
        if len(row) < 2:
            continue
        period = row[0].strip()
        for idx, cell in enumerate(row[1:], start=1):
            try:
                value = float(cell.strip().replace(",", "."))
            except (ValueError, IndexError):
                continue
            label = headers[idx] if idx < len(headers) else f"Serie {idx}"
            ind_id, name, unit = _classify_bde_label(label)
            records.append(MacroIndicator(
                provider=provider, source=url,
                retrieved_at=retrieved_at, country="ES", region=region,
                confidence_score=0.85,
                indicator_id=ind_id, name=name,
                value=value, unit=unit, period=period, frequency="monthly",
            ))
    return records


def _classify_bde_label(label: str) -> tuple[str, str, str]:
    ll = label.lower()
    if "euribor" in ll:
        return "ES_EURIBOR", label or "Euribor", "%"
    if "bce" in ll or "facilidad" in ll or "intervenci" in ll:
        return "ECB_RATE", label or "Tipo BCE", "%"
    if "ipc" in ll or "inflaci" in ll:
        return "ES_INFLATION", label or "Inflacion", "%"
    if "m1" in ll or "m2" in ll or "m3" in ll:
        return "ES_MONEY_SUPPLY", label or "Indicador monetario", ""
    return "BDE_SERIES", label or "Banco de Espana series", ""
