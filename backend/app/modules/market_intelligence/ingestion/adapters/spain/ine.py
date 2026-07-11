"""INE (Instituto Nacional de Estadística) adapter — API Tempus3.

Sirve solo series verificadas en vivo (cod + Nombre + valor plausible) contra la
API Tempus3, keyed por catalog id. Igual que Eurostat: no se declara ninguna serie
sin verificación, porque una unidad equivocada reintroduce el bug de ECO-1.
"""
import time
from datetime import datetime, timezone
from typing import NamedTuple

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroIndicator

_BASE = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE"


class _Series(NamedTuple):
    cod: str      # código de serie Tempus3
    name: str
    unit: str
    frequency: str
    scale: float = 1.0   # multiplicador aplicado al Valor crudo (p.ej. millones€ → EUR bn)


# Verificado en vivo contra Tempus3 (2026-07-06): cod + Nombre + valor plausible.
#   IPC (variación ANUAL, no mensual → titular YoY, coherente con el HICP de Eurostat):
#     IPC290750 general (3.2%), IPC290754 alimentación, IPC290762 vivienda/energía (1.4%),
#     IPC290774 transporte, IPC290794 restaurantes/hoteles. Tabla 76125.
#   EPA86913 → "Tasa de paro. Ambos sexos. Total Nacional. Total." (11.76%, trimestral)
#   CNTR6597 → "PIB pm. Dato base. Precios corrientes. CVEC." (437288 millones€ → ÷1000 = EUR bn)
_SERIES: dict[str, _Series] = {
    "ipc_general": _Series("IPC290750", "IPC General España (variación anual)", "%", "monthly"),
    "ipc_alimentacion": _Series("IPC290754", "IPC Alimentos y bebidas", "%", "monthly"),
    "ipc_vivienda": _Series("IPC290762", "IPC Vivienda, agua, electricidad y gas", "%", "monthly"),
    "ipc_transporte": _Series("IPC290774", "IPC Transporte", "%", "monthly"),
    "ipc_restauracion": _Series("IPC290794", "IPC Restaurantes y hoteles", "%", "monthly"),
    "desempleo_spain": _Series("EPA86913", "Tasa de paro España (EPA)", "%", "quarterly"),
    "pib_spain": _Series("CNTR6597", "PIB España (precios corrientes, CVEC)", "EUR bn", "quarterly", 1 / 1000),
    # Vivienda: IPV general nacional, variación anual (IPV948, 12.9%, trimestral, tabla 76201).
    "ipv_spain": _Series("IPV948", "Precio de la vivienda (IPV, variación anual)", "%", "quarterly"),
    # Laboral: coste laboral total por trabajador, total economía B-S (ETCL68, €3.382, trimestral).
    "coste_laboral_spain": _Series("ETCL68", "Coste laboral por trabajador", "€", "quarterly"),
    # Coyuntura: comercio al por menor, índice general, variación anual (ICM3431, 5.1%, mensual).
    "comercio_minorista_spain": _Series("ICM3431", "Comercio minorista (variación anual)", "%", "monthly"),
    # Hipotecas: proxy "fincas urbanas" (INE no expone serie 'viviendas' limpia). Nacional mensual.
    #   HPT34724 número (50.280/mes); HPT34671 importe en miles€ → ×1e-6 = EUR bn (10.33/mes).
    "hipotecas_numero_spain": _Series("HPT34724", "Hipotecas urbanas (número)", "hipotecas", "monthly"),
    "hipotecas_importe_spain": _Series("HPT34671", "Hipotecas urbanas (importe)", "EUR bn", "monthly", 1e-6),
}

_PING_URL = f"{_BASE}/IPC290750?nult=1"


def _period_label(item: dict, frequency: str) -> str:
    # El código FK_Periodo trimestral no es consistente entre operaciones INE, así que
    # derivamos el periodo del campo `Fecha` (epoch ms, inequívoco). +12h absorbe el
    # desfase medianoche-Madrid/UTC (Fecha viene a las 00:00 local → -1..2h en UTC).
    # ponytail: nudge de 12h en vez de zoneinfo; basta para un offset de ±2h.
    fecha = item.get("Fecha")
    if fecha is not None:
        try:
            dt = datetime.fromtimestamp(int(fecha) / 1000 + 43200, tz=timezone.utc)
            if frequency == "quarterly":
                # canónico YYYY-Qn (ECO-3): con "Q", no "T" — normalize_period/_year_ago lo exigen.
                return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
            if frequency == "monthly":
                return f"{dt.year}-{dt.month:02d}"
            return str(dt.year)
        except (TypeError, ValueError, OSError, OverflowError):
            pass
    return f"{item.get('Anyo', '')}-{item.get('FK_Periodo', '')}"


class INEAdapter(BaseAdapter):
    name = "INE"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {k: {} for k in _SERIES}

    def is_available(self) -> bool:
        try:
            r = requests.head(_PING_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        # indicator_id None → health-check: usa la serie por defecto (IPC).
        series_id = indicator_id or "ipc_general"
        series = _SERIES.get(series_id)
        if series is None:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"INE no sirve '{indicator_id}'", latency_ms=0.0,
                raw_sample=None, metadata=self._make_metadata(base_url=_BASE),
            )

        url = f"{_BASE}/{series.cod}?nult=3"
        metadata = self._make_metadata(base_url=url)
        t0 = time.time()
        try:
            r = requests.get(url, timeout=10)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.time() - t0) * 1000, raw_sample=None, metadata=metadata,
            )

        try:
            records = self._parse(data, series_id, series, url)
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Parse error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )

        raw_items = data.get("Data", [])
        return AdapterResult(
            provider=self.name, success=bool(records), records=records,
            error=None if records else "No data parsed", latency_ms=latency_ms,
            raw_sample=raw_items[-1] if raw_items else None, metadata=metadata,
        )

    def _parse(self, data: dict, indicator_id: str, series: _Series, source: str) -> list:
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []
        for item in data.get("Data", []):
            valor = item.get("Valor")
            if valor is None:
                continue
            records.append(
                MacroIndicator(
                    provider=self.name,
                    source=source,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.95,
                    indicator_id=indicator_id,
                    name=series.name,
                    value=float(valor) * series.scale,
                    unit=series.unit,
                    period=_period_label(item, series.frequency),
                    frequency=series.frequency,
                )
            )
        return records
