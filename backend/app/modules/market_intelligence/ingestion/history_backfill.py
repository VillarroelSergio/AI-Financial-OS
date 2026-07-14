"""MKT-6/8: backfill de histórico EOD multi-proveedor (índices/commodities vía Yahoo,
cripto vía CoinGecko, forex vía Frankfurter/BCE).

Un único punto de entrada para el CLI manual y para el arranque automático (startup.py).
Idempotente: `persist_historical_prices` hace DELETE+INSERT por (item, symbol, date).
"""
from __future__ import annotations

import logging

from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.history")

# forex: los pares se derivan del catalog_id (`eur_usd` → EUR→USD). Este set fija los que
# el snapshot de divisas expone hoy.
# ponytail: lista fija; si el catálogo de forex crece, leerla de mi_currency_rates.
_FOREX_IDS = ["eur_usd", "eur_gbp", "eur_jpy", "eur_chf", "eur_cad", "eur_aud", "usd_jpy", "gbp_usd"]


def _fetchers() -> dict[str, tuple[str, str, callable]]:
    """catalog_id → (provider_id, family, fetch_fn). Import perezoso para no cargar
    adapters (ni requests) hasta que se necesiten."""
    from app.modules.market_intelligence.ingestion.adapters.global_.coingecko import (
        _COINS,
        fetch_crypto_history,
    )
    from app.modules.market_intelligence.ingestion.adapters.global_.frankfurter import (
        fetch_forex_history,
    )
    from app.modules.market_intelligence.ingestion.adapters.global_.stooq import (
        _SOURCES,
        fetch_stooq_history,
    )

    out: dict[str, tuple[str, str, callable]] = {}
    for cid, src in _SOURCES.items():
        family = "commodities" if src.get("asset_type") == "commodity" else "indices"
        out[cid] = ("yahoo", family, fetch_stooq_history)
    for cid in _COINS:
        out[cid] = ("coingecko", "crypto", fetch_crypto_history)
    for cid in _FOREX_IDS:
        out[cid] = ("frankfurter", "forex", fetch_forex_history)
    return out


def backfill_all(
    years: int = 5,
    families: set[str] | None = None,
    only_missing: bool = False,
    min_rows: int = 20,
    on_result=None,
) -> int:
    """Backfillea histórico para todos los instrumentos (o solo `families`).

    only_missing: salta los que ya tienen >= min_rows filas (arranque barato en reinicios).
    on_result: callback opcional (cid, ok, detail) para feedback en el CLI.
    """
    fetchers = _fetchers()
    counts = repository.historical_counts() if only_missing else {}
    total = 0
    for cid, (provider, family, fn) in fetchers.items():
        if families and family not in families:
            continue
        if only_missing and counts.get(cid, 0) >= min_rows:
            continue
        try:
            n = repository.persist_historical_prices(cid, provider, fn(cid, years=years))
            total += n
            logger.info("history backfill %s: %d filas", cid, n)
            if on_result:
                on_result(cid, True, f"{n} filas")
        except Exception as exc:  # un proveedor caído no debe frenar el resto
            logger.warning("history backfill %s falló: %s", cid, exc)
            if on_result:
                on_result(cid, False, str(exc))
    return total
