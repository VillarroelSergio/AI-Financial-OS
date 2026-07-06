"""Eurostat adapter — series macro ES/EA (inflación, paro, PIB, industria, fiscal, confianza)."""
import time
from datetime import datetime, timezone
from typing import NamedTuple

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    MacroIndicator,
    ProviderMetadata,
)

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp"
    "?format=JSON&lang=EN&freq=Q&unit=CLV_PCH_PRE&na_item=B1GQ&geo=EA20&lastTimePeriod=4"
)
_UNEMPLOYMENT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m"
    "?format=JSON&lang=EN&freq=M&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&geo=EA20&lastTimePeriod=3"
)
_INFLATION_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr"
    "?format=JSON&lang=EN&freq=M&coicop=CP00&geo=EA20&lastTimePeriod=3"
)

_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# ECO-2: dataset+filtros+unidad de cada serie verificados contra la API en vivo
# (2026-07-06). La unidad del catálogo se respeta: índices como "index", nivel de PIB
# como "EUR bn" (escalando millones→miles de millones), ratios fiscales como "% PIB".
# Meter una serie con unidad equivocada reintroduce el bug que cerró ECO-1, por eso no
# se declara ninguna sin esa verificación.
class _Series(NamedTuple):
    url: str
    name: str
    frequency: str
    unit: str
    country: str
    scale: float = 1.0


_SERIES: dict[str, _Series] = {
    # Inflación (HICP, tasa anual %) — INE/BCE como primarios, Eurostat cubre ES y EA.
    "ipc_general": _Series(
        f"{_BASE}/prc_hicp_manr?format=JSON&lang=EN&freq=M&coicop=CP00&geo=ES&lastTimePeriod=3",
        "IPC España (HICP)", "monthly", "%", "ES"),
    "ipc_subyacente": _Series(
        f"{_BASE}/prc_hicp_manr?format=JSON&lang=EN&freq=M&coicop=TOT_X_NRG_FOOD&geo=ES&lastTimePeriod=3",
        "IPC subyacente España (HICP core)", "monthly", "%", "ES"),
    "inflation_eurozone": _Series(
        f"{_BASE}/prc_hicp_manr?format=JSON&lang=EN&freq=M&coicop=CP00&geo=EA20&lastTimePeriod=3",
        "HICP inflación Eurozona", "monthly", "%", "EA"),
    # Desempleo (% población activa).
    "desempleo_spain": _Series(
        f"{_BASE}/une_rt_m?format=JSON&lang=EN&freq=M&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&geo=ES&lastTimePeriod=3",
        "Tasa de paro España", "monthly", "%", "ES"),
    "unemployment_eurozone": _Series(
        f"{_BASE}/une_rt_m?format=JSON&lang=EN&freq=M&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&geo=EA20&lastTimePeriod=3",
        "Tasa de paro Eurozona", "monthly", "%", "EA"),
    # PIB Eurozona: nivel a precios corrientes en millones € → EUR bn (÷1000).
    "gdp_eurozone": _Series(
        f"{_BASE}/namq_10_gdp?format=JSON&lang=EN&freq=Q&unit=CP_MEUR&s_adj=SCA&na_item=B1GQ&geo=EA20&lastTimePeriod=3",
        "PIB Eurozona (nivel)", "quarterly", "EUR bn", "EA", 1 / 1000),
    # Producción industrial (índice 2021=100), total industria ex construcción (B-D), SCA.
    "produccion_industrial_spain": _Series(
        f"{_BASE}/sts_inpr_m?format=JSON&lang=EN&freq=M&indic_bt=PRD&nace_r2=B-D&s_adj=SCA&unit=I21&geo=ES&lastTimePeriod=3",
        "Producción industrial España", "monthly", "index", "ES"),
    "industrial_production_eurozone": _Series(
        f"{_BASE}/sts_inpr_m?format=JSON&lang=EN&freq=M&indic_bt=PRD&nace_r2=B-D&s_adj=SCA&unit=I21&geo=EA20&lastTimePeriod=3",
        "Producción industrial Eurozona", "monthly", "index", "EA"),
    # Cuentas de las AAPP trimestrales (% PIB): déficit (B9) y deuda (GD).
    "deficit_spain": _Series(
        f"{_BASE}/gov_10q_ggnfa?format=JSON&lang=EN&freq=Q&unit=PC_GDP&sector=S13&na_item=B9&s_adj=NSA&geo=ES&lastTimePeriod=3",
        "Déficit AAPP España", "quarterly", "% PIB", "ES"),
    "deuda_publica_spain": _Series(
        f"{_BASE}/gov_10q_ggdebt?format=JSON&lang=EN&freq=Q&unit=PC_GDP&sector=S13&na_item=GD&geo=ES&lastTimePeriod=3",
        "Deuda pública España", "quarterly", "% PIB", "ES"),
    # Confianza del consumidor (DG-ECFIN, balance). EA usa el agregado EA21.
    "confianza_consumidor_spain": _Series(
        f"{_BASE}/ei_bsco_m?format=JSON&lang=EN&freq=M&indic=BS-CSMCI&s_adj=SA&unit=BAL&geo=ES&lastTimePeriod=3",
        "Confianza consumidor España", "monthly", "index", "ES"),
    "consumer_confidence_eurozone": _Series(
        f"{_BASE}/ei_bsco_m?format=JSON&lang=EN&freq=M&indic=BS-CSMCI&s_adj=SA&unit=BAL&geo=EA21&lastTimePeriod=3",
        "Confianza consumidor Eurozona", "monthly", "index", "EA"),
}


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="Eurostat",
        id="eurostat",
        category="macro",
        region="Eurozone",
        method="api",
        base_url="https://ec.europa.eu/eurostat",
        requires_api_key=False,
        declared_update_frequency="quarterly",
        declared_historical_depth_years=30,
        license="Eurostat Open Data",
        notes="Eurostat REST dissemination API",
        capabilities=("macro", "historical"),
        priority="primary",
    )


def _dimension_ids(data: dict) -> list[str]:
    ids = data.get("id")
    if isinstance(ids, list):
        return ids
    dimensions = data.get("dimension", {})
    return [key for key in dimensions if key != "id" and key != "size"]


def _dimension_sizes(data: dict, ids: list[str]) -> list[int]:
    sizes = data.get("size")
    if isinstance(sizes, list) and len(sizes) == len(ids):
        return [int(size) for size in sizes]
    result = []
    for dim_id in ids:
        index = data.get("dimension", {}).get(dim_id, {}).get("category", {}).get("index", {})
        result.append(len(index) or 1)
    return result


def _time_periods(data: dict) -> list[tuple[int, str]]:
    time_category = data.get("dimension", {}).get("time", {}).get("category", {})
    time_index = time_category.get("index", {})
    labels = time_category.get("label", {})
    if time_index:
        return sorted(((int(idx), period) for period, idx in time_index.items()), key=lambda x: x[0])
    return sorted(((int(idx), label) for idx, label in labels.items()), key=lambda x: x[0])


def _value_for_time(data: dict, time_pos: int):
    values = data.get("value", {})
    if not isinstance(values, dict):
        return None
    ids = _dimension_ids(data)
    sizes = _dimension_sizes(data, ids)
    if "time" not in ids:
        return values.get(str(time_pos))
    coords = [0] * len(ids)
    coords[ids.index("time")] = time_pos
    flat_index = 0
    for i, coord in enumerate(coords):
        stride = 1
        for size in sizes[i + 1:]:
            stride *= size
        flat_index += coord * stride
    return values.get(str(flat_index))


def _parse_jsonstat(data: dict, source: str, indicator_id: str, name: str, frequency: str,
                    unit: str, country: str, scale: float, retrieved_at: datetime) -> list[MacroIndicator]:
    region = "Spain" if country == "ES" else "Eurozone"
    records: list[MacroIndicator] = []
    for time_pos, period in _time_periods(data)[-3:]:
        val = _value_for_time(data, time_pos)
        if val is None:
            continue
        records.append(
            MacroIndicator(
                provider="Eurostat",
                source=source,
                retrieved_at=retrieved_at,
                country=country,
                region=region,
                confidence_score=1.0,
                indicator_id=indicator_id,
                name=name,
                value=float(val) * scale,
                unit=unit,
                period=period,
                frequency=frequency,
            )
        )
    return records


class EurostatAdapter(BaseAdapter):
    name = "Eurostat"
    category = "macro"
    region = "Eurozone"
    requires_api_key = False
    # allowlist honesta: antes fetch() devolvía el paquete EA20 (GDP+HICP+paro) para
    # cualquier id → clon. Ahora sirve solo la serie pedida (geo ES o EA20).
    supported_indicators = {k: {} for k in _SERIES}

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)

        if indicator_id is not None and indicator_id not in _SERIES:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Eurostat no sirve '{indicator_id}'", latency_ms=0.0,
                raw_sample=None, metadata=metadata,
            )

        if indicator_id is None:
            # Health-check / legacy: paquete EA20 (GDP QoQ + HICP + paro), todo en %.
            targets = (
                (_GDP_URL, "EU_GDP_GROWTH", "EU GDP Growth QoQ", "quarterly", "%", "EA", 1.0),
                (_INFLATION_URL, "EU_HICP_INFLATION", "Euro area HICP inflation", "monthly", "%", "EA", 1.0),
                (_UNEMPLOYMENT_URL, "EU_UNEMPLOYMENT", "Euro area unemployment rate", "monthly", "%", "EA", 1.0),
            )
        else:
            s = _SERIES[indicator_id]
            targets = ((s.url, indicator_id, s.name, s.frequency, s.unit, s.country, s.scale),)

        try:
            records: list[MacroIndicator] = []
            raw_sample = None
            for url, tag, name, frequency, unit, country, scale in targets:
                r = requests.get(url, headers=_HEADERS, timeout=10)
                r.raise_for_status()
                data = r.json()
                raw_sample = raw_sample or {"value_count": len(data.get("value", {})), "preview": str(data)[:500]}
                records.extend(_parse_jsonstat(data, url, tag, name, frequency, unit, country, scale, retrieved_at))

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
