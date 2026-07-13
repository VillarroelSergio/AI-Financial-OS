"""AI-3 D1: auto-generación del brief mensual al arrancar (+ cierre de mes).

Al abrir la app aseguramos el `monthly_review` del mes en curso y del mes recién
cerrado, para que el Centro de Análisis no muestre "aún no hay análisis" en la
primera visita. Es mejora progresiva: en background (nunca bloquea el arranque),
idempotente (si el brief ya existe no se toca), y sólo si hay datos y el provider
LLM está vivo — así no persistimos una narrativa determinista que luego se quede
congelada aunque el usuario encienda el LLM después (para eso está el botón manual).

El "hook de cierre de mes" es implícito: la primera apertura del mes nuevo genera
el brief del mes anterior (que aún no existía). La app de escritorio se abre a
menudo, así que no hace falta un scheduler.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from threading import Thread

from app.core.config import settings
from app.modules.ai import analysis

logger = logging.getLogger("ai.startup")

_SCOPE = "monthly_review"


def _prev_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:7])
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


async def _ensure_brief(period: str) -> None:
    """Genera el brief del período si no existe, hay datos y el LLM está vivo."""
    from app.core import database as db_module
    from app.modules.ai.service import get_provider

    db = db_module.SessionLocal()
    try:
        if analysis.get_brief(db, _SCOPE, period):
            return  # idempotente: ya generado (posible narrativa LLM), no tocar
        if analysis.build_bundle(db, _SCOPE, period)["data_state"] == "empty":
            return  # nada que narrar
        health = await get_provider().health()
        if not health.available:
            return  # sin LLM: que lo genere el botón / el próximo arranque
        await analysis.generate_brief(db, _SCOPE, period)
        logger.info("brief mensual auto-generado: %s", period)
    finally:
        db.close()


async def _run() -> None:
    if not settings.AI_ASSISTANT_ENABLED:
        return
    current = datetime.now(timezone.utc).strftime("%Y-%m")
    for period in (current, _prev_period(current)):
        try:
            await _ensure_brief(period)
        except Exception as exc:  # best-effort: nunca debe tumbar el arranque
            logger.warning("auto-brief %s falló: %s", period, exc)


def launch_startup_brief() -> None:
    """Dispara la auto-generación en un hilo daemon (no bloquea el lifespan)."""
    Thread(target=lambda: asyncio.run(_run()), daemon=True).start()


if __name__ == "__main__":
    # Self-check de la lógica pura de períodos (lo demás necesita DB + LLM).
    assert _prev_period("2026-07") == "2026-06"
    assert _prev_period("2026-01") == "2025-12"
    assert _prev_period("2026-12") == "2026-11"
    print("ai.startup self-check ok")
