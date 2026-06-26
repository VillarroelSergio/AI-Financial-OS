"""Banco de España adapter — SDMX para series clave, CSV legacy como fallback."""
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_SDMX_BASE = "https://sdmx.bde.es/service/data"
_SDMX_HEADERS = {
    "Accept": "application/vnd.sdmx.data+json;version=1.0",
    "User-Agent": "MarketDataPOC/0.1 contact@example.com",
}
_PRIMARY_URL = "https://www.bde.es/webbde/es/estadis/infoest/Series/si_1_1.csv"
_FALLBACK_URL = (
    "https://www.bde.es/f/webbde/SES/Secciones/Publicaciones/InformesBoletinesRevistas"
    "/BoletinEstadistico/25/T01/Fich/be_1-1.csv"
)

# Códigos SDMX BDE — verificar en https://sdmx.bde.es/service/dataflow
_SDMX_SERIES = {
    "euribor_3m": {
        "flow": "TIPO",
        "key": "M.IT.MIR.14.A.2500.EUR.2250.N",
        "indicator_id": "EURIBOR_3M",
        "name": "Euribor 3 meses",
        "unit": "%",
        "frequency": "monthly",
    },
    "euribor_12m": {
        "flow": "TIPO",
        "key": "M.IT.MIR.14.A.2500.EUR.2253.N",
        "indicator_id": "EURIBOR_12M",
        "name": "Euribor 12 meses",
        "unit": "%",
        "frequency": "monthly",
    },
    "spain_10y": {
        "flow": "BONO",
        "key": "M.ES.GVT.10Y",
        "indicator_id": "SPAIN_10Y",
        "name": "Bono Español 10Y",
        "unit": "%",
        "frequency": "monthly",
    },
}


class BDEAdapter(BaseAdapter):
    name = "Banco de España"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {k: v for k, v in _SDMX_SERIES.items()}

    def is_available(self) -> bool:
        try:
            r = requests.head(_PRIMARY_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        if indicator_id and indicator_id in _SDMX_SERIES:
            return self._fetch_sdmx(indicator_id)
        return self._fetch_legacy()

    def _fetch_sdmx(self, indicator_id: str) -> AdapterResult:
        series = _SDMX_SERIES[indicator_id]
        url = f"{_SDMX_BASE}/{series['flow']}/{series['key']}?lastNObservations=12"
        metadata = self._make_metadata(base_url=url, method="sdmx")
        t0 = time.time()
        try:
            r = requests.get(url, headers=_SDMX_HEADERS, timeout=15)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            records = self._parse_sdmx(r.json(), series)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"SDMX error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else "No SDMX observations parsed",
            latency_ms=latency_ms,
            raw_sample=None,
            metadata=metadata,
        )

    def _parse_sdmx(self, data: dict, series: dict) -> list[MacroIndicator]:
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []
        try:
            dataset = data["dataSets"][0]
            series_data = dataset["series"]
            dimensions = data["structure"]["dimensions"]["observation"][0]["values"]
            for _series_key, series_obj in series_data.items():
                for obs_key, obs_values in series_obj["observations"].items():
                    idx = int(obs_key)
                    value = obs_values[0]
                    if value is None:
                        continue
                    period = dimensions[idx]["id"] if idx < len(dimensions) else str(idx)
                    records.append(MacroIndicator(
                        provider=self.name,
                        source=f"{_SDMX_BASE}/{series['flow']}/{series['key']}",
                        retrieved_at=retrieved_at,
                        country="Spain",
                        region=self.region,
                        confidence_score=0.95,
                        indicator_id=series["indicator_id"],
                        name=series["name"],
                        value=float(value),
                        unit=series["unit"],
                        period=period,
                        frequency=series["frequency"],
                    ))
        except (KeyError, IndexError, TypeError):
            pass
        return records

    def _fetch_legacy(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()
        try:
            response = self._get_csv(t0)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=str(exc), latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        raw_text, latency_ms, used_url = response
        metadata = self._make_metadata(base_url=used_url)
        try:
            records = self._parse_csv(raw_text)
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Parse error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        raw_sample = {"raw_preview": raw_text[:500]} if raw_text else None
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else "No BDE data parsed",
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )

    def _get_csv(self, t0: float):
        for url in (_PRIMARY_URL, _FALLBACK_URL):
            try:
                r = requests.get(url, timeout=10)
                latency_ms = (time.time() - t0) * 1000
                r.raise_for_status()
                return r.text, latency_ms, url
            except Exception:
                pass
        raise RuntimeError("Both BDE CSV URLs failed")

    def _parse_csv(self, raw_text: str) -> list:
        import csv
        retrieved_at = datetime.now(timezone.utc)
        lines = raw_text.splitlines()
        header = None
        data_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if header is None and (";" in stripped or "," in stripped) and not stripped[0].isdigit():
                header = stripped
                continue
            first_char = stripped[0]
            if first_char.isdigit() or (len(stripped) > 4 and stripped[1:5].isdigit()):
                data_lines.append(stripped)
        delimiter = ";" if (header or "").count(";") >= (header or "").count(",") else ","
        rows = list(csv.reader(data_lines[-5:], delimiter=delimiter))
        if not rows:
            rows = list(csv.reader(data_lines[-3:], delimiter=","))
            delimiter = ","
        headers = list(csv.reader([header], delimiter=delimiter))[0] if header else []
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
                indicator_id, name, unit = _classify_bde_series(label)
                records.append(MacroIndicator(
                    provider=self.name, source=_PRIMARY_URL,
                    retrieved_at=retrieved_at, country="Spain", region=self.region,
                    confidence_score=0.9 if headers else 0.75,
                    indicator_id=indicator_id, name=name,
                    value=value, unit=unit, period=period, frequency="monthly",
                ))
        return records


def _classify_bde_series(label: str) -> tuple[str, str, str]:
    label_lower = label.lower()
    if "euribor" in label_lower:
        return "ES_EURIBOR", label or "Euribor", "%"
    if "bce" in label_lower or "facilidad" in label_lower or "intervencion" in label_lower:
        return "ECB_RATE", label or "Tipo BCE", "%"
    if "ipc" in label_lower or "inflaci" in label_lower:
        return "ES_INFLATION", label or "Inflacion", "%"
    if "m1" in label_lower or "m2" in label_lower or "m3" in label_lower:
        return "ES_MONEY_SUPPLY", label or "Indicador monetario", ""
    return "BDE_SERIES", label or "Banco de Espana series", ""
