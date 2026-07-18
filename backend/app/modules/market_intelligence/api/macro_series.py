"""ECO-4: lectura macro unificada — única fuente para service/impact/personal_economy.

Sustituye a `_macro_year_ago` (impact.py) y `_latest_and_year_ago` (personal_economy.py),
que duplicaban la lógica de "valor de hace 12 meses" con regex defensivos distintos. Todo
acceso pasa por el repository; los `period` ya vienen canónicos de ECO-3 (YYYY-MM / YYYY-Qn
/ YYYY), así que aquí no hay parcheo defensivo: se compara periodo con periodo.
"""
from __future__ import annotations

import re

from app.modules.market_intelligence.storage import repository

_Q = re.compile(r"^(\d{4})-Q([1-4])$")
_YM = re.compile(r"^(\d{4})-(\d{2})$")
_Y = re.compile(r"^(\d{4})$")

# Suficiente para 12 meses (13+ mensuales) o 4 trimestres con holgura.
_MAX_POINTS = 60


def _year_ago_period(period: str) -> str | None:
    """Periodo canónico un año antes: 2026-05→2025-05, 2026-Q1→2025-Q1, 2026→2025."""
    p = period.strip()
    m = _Q.match(p)
    if m:
        return f"{int(m.group(1)) - 1}-Q{m.group(2)}"
    m = _YM.match(p)
    if m:
        return f"{int(m.group(1)) - 1}-{m.group(2)}"
    m = _Y.match(p)
    if m:
        return str(int(m.group(1)) - 1)
    return None


def _points(indicator_id: str) -> list[tuple[str, float]]:
    try:
        return repository.get_macro_history(max_points=_MAX_POINTS).get(indicator_id, [])
    except Exception:
        return []


def latest(indicator_id: str) -> float | None:
    """Último valor observado (mayor periodo)."""
    points = _points(indicator_id)
    return points[-1][1] if points else None


def history(indicator_id: str, limit: int | None = None) -> list[tuple[str, float]]:
    """Histórico canónico, limitado a las observaciones más recientes si se solicita."""
    points = _points(indicator_id)
    return points[-limit:] if limit is not None else points


def value_year_ago(indicator_id: str) -> float | None:
    """Valor ~12 meses atrás: la observación más reciente con periodo <= (último − 1 año).

    Los periodos de un mismo indicador comparten formato (frecuencia fija), así que la
    comparación lexicográfica entre periodos canónicos es correcta.
    """
    points = _points(indicator_id)
    if len(points) < 2:
        return None
    target = _year_ago_period(points[-1][0])
    if target is None:
        return None
    value = None
    for period, v in points:
        if period <= target:
            value = v
    return value


def change_12m(indicator_id: str) -> float | None:
    """Variación % interanual (último vs hace 12 meses). None si falta alguno o base 0."""
    points = _points(indicator_id)
    if len(points) < 2:
        return None
    current = points[-1][1]
    base = value_year_ago(indicator_id)
    if base in (None, 0):
        return None
    return (current - base) / abs(base) * 100
