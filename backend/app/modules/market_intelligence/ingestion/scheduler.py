"""ECO-5: planificación por frecuencia.

Un item se re-ingesta solo cuando `last_success_at + intervalo(frequency)` ha vencido.
Los intervalos son algo menores que el periodo nominal para que un tick horario coja el
dato en cuanto sale (una serie mensual no espera 30 días exactos + el desfase del tick).
Sin dependencias nuevas: el runner filtra por los ids que devuelve `due_item_ids`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator

# frequency del catálogo → cada cuánto tiene sentido refetchear.
_FREQ_INTERVAL: dict[str, timedelta] = {
    "daily": timedelta(hours=20),
    "weekly": timedelta(days=6),
    "monthly": timedelta(days=27),
    "quarterly": timedelta(days=88),
    "annual": timedelta(days=360),
    "yearly": timedelta(days=360),
}
# Desconocida/irregular → trátala como diaria (refresco frecuente, barato).
_DEFAULT_INTERVAL = timedelta(hours=20)


def interval_for(frequency: str | None) -> timedelta:
    return _FREQ_INTERVAL.get((frequency or "").lower(), _DEFAULT_INTERVAL)


def is_due(indicator: CatalogIndicator, state: dict | None, now: datetime) -> bool:
    """True si nunca se ingirió con éxito o si venció su intervalo de frecuencia."""
    last_success = state.get("last_success_at") if state else None
    if last_success is None:
        return True
    if last_success.tzinfo is None:  # DuckDB puede devolver naive
        last_success = last_success.replace(tzinfo=timezone.utc)
    return now - last_success >= interval_for(indicator.frequency)


def due_item_ids(indicators: list[CatalogIndicator], state: dict[str, dict],
                 now: datetime | None = None) -> list[str]:
    now = now or datetime.now(timezone.utc)
    return [i.id for i in indicators if is_due(i, state.get(i.id), now)]
