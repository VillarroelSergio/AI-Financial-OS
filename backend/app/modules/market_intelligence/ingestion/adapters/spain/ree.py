"""REE (Red Eléctrica de España) adapter — precio del pool eléctrico.

Contrato estricto ECO-1: allowlist por catalog id, `fetch(indicator_id)` sirve solo
lo pedido. Un único indicador verificado en vivo (2026-07): media mensual del mercado
spot (pool mayorista OMIE), no PVPC — el pool es el dato que la Propuesta cruza con la
categoría de gasto "suministros". Se agrega en el adapter porque la API solo da horario.
"""
import calendar
import time
from datetime import date, datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroIndicator

_ENDPOINT = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
_INDICATOR = "precio_electricidad_spain"


def _prev_month_range(today: date) -> tuple[date, date]:
    """Mes natural completo anterior a `today` → siempre cerrado, valor mensual estable."""
    y, m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


class REEAdapter(BaseAdapter):
    name = "REE"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {_INDICATOR: {}}

    def is_available(self) -> bool:
        try:
            start, end = _prev_month_range(date.today())
            r = requests.get(f"{_ENDPOINT}?start_date={start}T00:00&end_date={start}T01:00&time_trunc=hour",
                             timeout=10, headers={"Accept": "application/json"})
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        series_id = indicator_id or _INDICATOR
        metadata = self._make_metadata(base_url=_ENDPOINT)
        if series_id != _INDICATOR:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"REE no sirve '{indicator_id}'", latency_ms=0.0,
                raw_sample=None, metadata=metadata,
            )

        start, end = _prev_month_range(date.today())
        url = f"{_ENDPOINT}?start_date={start}T00:00&end_date={end}T23:59&time_trunc=hour"
        t0 = time.time()
        try:
            r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.time() - t0) * 1000, raw_sample=None, metadata=metadata,
            )

        try:
            avg = self._spot_monthly_avg(data)
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Parse error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )

        record = MacroIndicator(
            provider=self.name, source=url, retrieved_at=datetime.now(timezone.utc),
            country="Spain", region=self.region, confidence_score=0.95,
            indicator_id=_INDICATOR, name="Precio pool eléctrico España (spot, media mensual)",
            value=avg, unit="€/MWh", period=f"{start.year}-{start.month:02d}", frequency="monthly",
        )
        return AdapterResult(
            provider=self.name, success=True, records=[record], error=None,
            latency_ms=latency_ms, raw_sample={"avg": avg, "period": record.period}, metadata=metadata,
        )

    @staticmethod
    def _spot_monthly_avg(data: dict) -> float:
        for series in data.get("included", []):
            if "spot" in series.get("attributes", {}).get("title", "").lower():
                vals = [v["value"] for v in series["attributes"]["values"] if v.get("value") is not None]
                if not vals:
                    raise ValueError("Serie spot sin valores")
                return round(sum(vals) / len(vals), 2)
        raise ValueError("No se encontró la serie 'Precio mercado spot' en la respuesta REE")
