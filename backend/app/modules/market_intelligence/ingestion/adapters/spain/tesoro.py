"""Tesoro Público adapter — resultados de subastas (Letras, Bonos, Obligaciones).

Contrato estricto ECO-1: allowlist por catalog id, `fetch(indicator_id)` sirve solo lo
pedido. La fuente JSON histórica del Tesoro fue retirada (404); solo publica resultados
como HTML, así que esto **scrapea** la tabla oficial (excepción explícita a "scraping fuera
de alcance", aprobada para ECO-2b). El servidor sirve una cadena TLS incompleta (falta el
intermedio) → `verify=False`.
ponytail: verify=False obligado por el cert roto del Tesoro; revisar si algún día arreglan la cadena.

Letras: plazos fijos 3/6/9/12M → ids deterministas. Bonos/Obligaciones: el plazo rota por
subasta, así que se sirve la ÚLTIMA subasta (fecha máxima) como un único id, con el plazo en
el nombre. El tramo largo estable ya está cubierto por el bono 10Y de mercado secundario.
"""
import re
import time
from datetime import datetime, timezone

import requests
import urllib3

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import AdapterResult, MacroIndicator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BASE = "https://www.tesoro.es/deuda-publica/subastas/resultado-ultimas-subastas"
_LETRAS, _BONOS, _OBLIG = f"{_BASE}/letras-del-tesoro", f"{_BASE}/bonos-del-estado", f"{_BASE}/obligaciones-del-estado"

# id de catálogo → (url, selector). Para Letras el selector es el nº de meses; para
# Bonos/Obligaciones None = "última subasta" (columna con fecha máxima).
_SPEC: dict[str, tuple[str, int | None]] = {
    "letras_3m": (_LETRAS, 3),
    "letras_6m": (_LETRAS, 6),
    "letras_9m": (_LETRAS, 9),
    "letras_12m": (_LETRAS, 12),
    "bono_estado_subasta": (_BONOS, None),
    "obligacion_estado_subasta": (_OBLIG, None),
}
_NAMES = {
    "letras_3m": "Letras del Tesoro 3M", "letras_6m": "Letras del Tesoro 6M",
    "letras_9m": "Letras del Tesoro 9M", "letras_12m": "Letras del Tesoro 12M",
    "bono_estado_subasta": "Bono del Estado (última subasta)",
    "obligacion_estado_subasta": "Obligación del Estado (última subasta)",
}


class TesoroAdapter(BaseAdapter):
    name = "Tesoro Público"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {k: {} for k in _SPEC}

    def is_available(self) -> bool:
        try:
            return requests.get(_LETRAS, timeout=10, verify=False).status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        series_id = indicator_id or "letras_12m"
        spec = _SPEC.get(series_id)
        metadata = self._make_metadata(base_url=_BASE)
        if spec is None:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Tesoro no sirve '{indicator_id}'", latency_ms=0.0,
                raw_sample=None, metadata=metadata,
            )
        url, months = spec
        t0 = time.time()
        try:
            r = requests.get(url, timeout=20, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[], error=str(exc),
                latency_ms=(time.time() - t0) * 1000, raw_sample=None, metadata=metadata,
            )
        try:
            col = _select_column(r.content, months)
            record = MacroIndicator(
                provider=self.name, source=url, retrieved_at=datetime.now(timezone.utc),
                country="Spain", region=self.region, confidence_score=0.95,
                indicator_id=series_id,
                name=f"{_NAMES[series_id]} · {col['plazo']}" if months is None else _NAMES[series_id],
                value=col["marginal"], unit="%", period=col["period"], frequency="monthly",
            )
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Parse error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        return AdapterResult(
            provider=self.name, success=True, records=[record], error=None,
            latency_ms=latency_ms, raw_sample={"plazo": col["plazo"], "marginal": col["marginal"]},
            metadata=metadata,
        )


def _select_column(html_bytes: bytes, months: int | None) -> dict:
    """Parsea la tabla de resultados y devuelve la columna pedida.

    months=N → la columna cuyo Plazo son N MESES (Letras). None → la subasta más reciente
    (Fecha subasta máxima), para Bonos/Obligaciones de plazo rotativo.
    """
    # utf-8 con errors='replace': la fuente corrompe la Ñ de "AÑOS", pero no dependemos del
    # texto acentuado (el label del plazo se reconstruye desde el entero + MES/AÑO).
    text = html_bytes.decode("utf-8", errors="replace")
    table = re.search(r"<table.*?</table>", text, re.S)
    if not table:
        raise ValueError("Sin tabla de resultados")
    rows: dict[str, list[str]] = {}
    for tr in re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if cells:
            rows[cells[0]] = cells[1:]
    plazos = rows.get("Plazo") or []
    fechas = rows.get("Fecha subasta") or []
    marg_key = next((k for k in rows if "marginal" in k.lower() and "nterior" not in k.lower()), None)
    marginals = rows.get(marg_key, []) if marg_key else []
    if not plazos or not marginals:
        raise ValueError("Faltan filas Plazo/marginal")

    if months is not None:
        idx = next((i for i, p in enumerate(plazos) if _plazo_months(p) == months), None)
        if idx is None:
            raise ValueError(f"Plazo {months}M no presente en la subasta")
    else:
        idx = max(range(len(fechas)), key=lambda i: _fecha_key(fechas[i])) if fechas else 0

    return {
        "plazo": _plazo_label(plazos[idx]),
        "marginal": float(marginals[idx].replace(".", "").replace(",", ".")),
        "period": _fecha_to_period(fechas[idx]) if idx < len(fechas) else "",
    }


def _plazo_label(plazo: str) -> str:
    """Reconstruye el label limpio (ASCII) desde el entero + MES/AÑO, evitando la Ñ corrupta."""
    m = re.search(r"(\d+)", plazo)
    n = m.group(1) if m else "?"
    return f"{n} meses" if "MES" in plazo.upper() else f"{n} años"


def _plazo_months(plazo: str) -> int | None:
    m = re.search(r"(\d+)", plazo)
    if not m:
        return None
    n = int(m.group(1))
    return n if "MES" in plazo.upper() else n * 12  # años → meses


def _fecha_key(f: str) -> tuple:
    try:
        d, m, y = f.split("/")
        return (int(y), int(m), int(d))
    except Exception:
        return (0, 0, 0)


def _fecha_to_period(f: str) -> str:
    y, m, _ = _fecha_key(f)
    return f"{y}-{m:02d}" if y else ""
