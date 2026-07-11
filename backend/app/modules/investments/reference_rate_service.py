"""Ingesta y lookup del tipo de facilidad de depósito del BCE (INV-2).

Cachea el histórico completo en `ReferenceRateObservation` (SQLite de la app) desde
ECB SDMX; si falla, FRED (serie `ECBDFR`). Ambos son CSV público sin API key.
El motor de intereses (INV-4) lee vía `get_rate_on`, que funciona offline una vez
ingestado.

Decimal siempre; nunca float en los valores de tipo.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.investment import ReferenceRateObservation

logger = logging.getLogger("investments.reference_rate")

ECB_DFR = "ECB_DFR"

_HEADERS = {"User-Agent": "FinancialAgent/0.1 contact@example.com"}
# Serie de la facilidad de depósito del BCE (nivel), publicada solo en cambios.
_ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV"
    "?format=csvdata&startPeriod=1999-01-01&detail=dataonly"
)
# Fallback FRED: misma serie, diaria.
_FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBDFR"


def _to_decimal(raw: str | None) -> Decimal | None:
    if not raw or raw.strip() in (".", ""):
        return None
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, ValueError):
        return None


def _to_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None


def _parse_ecb(text: str) -> dict[date, Decimal]:
    """ECB csvdata: columnas TIME_PERIOD + OBS_VALUE."""
    out: dict[date, Decimal] = {}
    for row in csv.DictReader(io.StringIO(text)):
        d = _to_date(row.get("TIME_PERIOD"))
        v = _to_decimal(row.get("OBS_VALUE"))
        if d is not None and v is not None:
            out[d] = v
    return out


def _parse_fred(text: str) -> dict[date, Decimal]:
    """FRED fredgraph.csv: columnas DATE + ECBDFR (o VALUE)."""
    out: dict[date, Decimal] = {}
    reader = csv.DictReader(io.StringIO(text))
    fields = [f for f in (reader.fieldnames or []) if f and f.upper() != "DATE"]
    col = "ECBDFR" if "ECBDFR" in fields else ("VALUE" if "VALUE" in fields else (fields[0] if fields else ""))
    for row in reader:
        d = _to_date(row.get("DATE"))
        v = _to_decimal(row.get(col))
        if d is not None and v is not None:
            out[d] = v
    return out


def _fetch_series() -> tuple[dict[date, Decimal], str]:
    """Devuelve (observaciones, fuente). ECB primero, FRED de fallback."""
    try:
        r = requests.get(_ECB_URL, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        obs = _parse_ecb(r.text)
        if obs:
            return obs, "ecb"
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de red cae al fallback
        logger.warning("ECB DFR fetch failed, trying FRED: %s", exc)
    r = requests.get(_FRED_URL, headers=_HEADERS, timeout=15)
    r.raise_for_status()
    return _parse_fred(r.text), "fred"


def ingest_deposit_facility_history(db: Session, rate_id: str = ECB_DFR) -> int:
    """Descarga el histórico del DFR y hace upsert. Devuelve nº de filas nuevas/actualizadas."""
    observations, source = _fetch_series()
    if not observations:
        logger.warning("No DFR observations parsed from any provider")
        return 0

    existing = {
        row.effective_date: row
        for row in db.execute(
            select(ReferenceRateObservation).where(ReferenceRateObservation.rate_id == rate_id)
        ).scalars()
    }
    now = datetime.now(timezone.utc)
    changed = 0
    for eff_date, rate in observations.items():
        current = existing.get(eff_date)
        if current is None:
            db.add(ReferenceRateObservation(
                rate_id=rate_id, effective_date=eff_date, rate=rate,
                source=source, retrieved_at=now,
            ))
            changed += 1
        elif current.rate != rate:
            current.rate = rate
            current.source = source
            current.retrieved_at = now
            changed += 1
    db.commit()
    logger.info("DFR ingest: %d rows changed (source=%s)", changed, source)
    return changed


def ensure_deposit_facility_history(db: Session, rate_id: str = ECB_DFR) -> None:
    """Ingesta perezosa: si el cache está vacío, descarga el histórico del DFR.
    Silenciosa ante fallos de red (el motor usa 0 si no hay dato)."""
    if db.query(ReferenceRateObservation).filter(ReferenceRateObservation.rate_id == rate_id).count() > 0:
        return
    try:
        ingest_deposit_facility_history(db, rate_id)
    except Exception:  # noqa: BLE001 — sin red, se sigue con lo que haya (vacío)
        logger.warning("lazy DFR ingest failed", exc_info=True)


def get_rate_on(db: Session, on_date: date, rate_id: str = ECB_DFR) -> Decimal | None:
    """Tipo vigente en `on_date`: la observación más reciente con effective_date <= on_date."""
    row = db.execute(
        select(ReferenceRateObservation)
        .where(
            ReferenceRateObservation.rate_id == rate_id,
            ReferenceRateObservation.effective_date <= on_date,
        )
        .order_by(ReferenceRateObservation.effective_date.desc())
        .limit(1)
    ).scalars().first()
    return row.rate if row is not None else None
