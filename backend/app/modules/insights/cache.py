"""Caché en memoria de proceso para los insights calculados (D4, TTL 1h).

Cachea el resultado caro (`_all_insights` por mes). El filtrado/orden posterior
es barato y no se cachea. Invalidación explícita en refresh, dismiss y cualquier
mutación de datos que altere las señales.
ponytail: dict + timestamp basta; migrar a Redis solo si hay varios procesos.
"""
from __future__ import annotations

import time
from typing import TypeVar

TTL_SECONDS = 3600  # 1 hora

_store: dict[str, tuple[float, object]] = {}

T = TypeVar("T")


def get(key: str) -> object | None:
    entry = _store.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > TTL_SECONDS:
        _store.pop(key, None)
        return None
    return value


def set(key: str, value: T) -> T:
    _store[key] = (time.monotonic(), value)
    return value


def invalidate(key: str | None = None) -> None:
    """Sin argumento borra todo (mutación transversal); con clave, solo ese mes."""
    if key is None:
        _store.clear()
    else:
        _store.pop(key, None)
