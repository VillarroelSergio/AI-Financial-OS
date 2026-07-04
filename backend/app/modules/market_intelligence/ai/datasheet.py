"""Generador de AI Datasheet.

La IA local SOLO consume el output de generate_ai_datasheet().
Nunca llama a providers ni a APIs externas.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.modules.market_intelligence.api import service
from app.modules.market_intelligence.api.schemas import AiDatasheetOut
from app.modules.market_intelligence.storage import repository

logger = logging.getLogger("market_intelligence.ai")


def generate_ai_datasheet(scope: str = "daily") -> AiDatasheetOut:
    """Genera el JSON compacto de contexto de mercado para la IA local."""
    generated_at = datetime.now(timezone.utc).isoformat()

    macro_snapshot = service.get_macro_snapshot()
    forex_snapshot = service.get_forex_snapshot()
    bond_snapshot = service.get_bond_snapshot()
    news_snapshot = service.get_news_snapshot(limit=10)

    # Construir macro dict jerárquico
    macro = {
        "spain": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.spain},
        "eurozone": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.eurozone},
        "usa": {dp.catalog_item_id: {"value": dp.value, "period": dp.period, "provider": dp.provider_id, "quality_score": dp.quality_score} for dp in macro_snapshot.usa},
    }

    # Forex dict
    forex = {
        f"{r.base_currency}_{r.quote_currency}": {"rate": r.rate, "date": r.date, "provider": r.provider_id, "quality_score": r.quality_score}
        for r in forex_snapshot.rates
        if r.base_currency and r.quote_currency
    }

    # Bonds dict
    bonds = {
        f"{b.country}_{b.maturity}": {"yield": b.yield_value, "date": b.date, "provider": b.provider_id, "quality_score": b.quality_score}
        for b in bond_snapshot.yields
        if b.country and b.maturity
    }

    # News list
    news = [
        {"title": n.title, "category": n.category, "published_at": n.published_at, "source": n.source_name}
        for n in news_snapshot.items
    ]

    # Warnings
    warnings = macro_snapshot.warnings + forex_snapshot.warnings + bond_snapshot.warnings

    # Quality score = media de todos los quality scores
    all_scores = (
        [dp.quality_score for dp in macro_snapshot.spain + macro_snapshot.eurozone + macro_snapshot.usa]
        + [r.quality_score for r in forex_snapshot.rates]
        + [b.quality_score for b in bond_snapshot.yields]
    )
    quality_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0

    # Sources
    sources = list({
        dp.provider_id for dp in macro_snapshot.spain + macro_snapshot.eurozone + macro_snapshot.usa
        if dp.provider_id
    })

    datasheet = AiDatasheetOut(
        generated_at=generated_at,
        quality_score=quality_score,
        scope=scope,
        macro=macro,
        markets={},
        forex=forex,
        bonds=bonds,
        news=news,
        sources=sources,
        warnings=warnings,
    )

    # Persistir en DuckDB
    try:
        repository.save_ai_datasheet(
            scope=scope,
            datasheet_json=json.dumps(datasheet.model_dump()),
            quality_score=quality_score,
        )
    except Exception as exc:
        logger.warning("Could not persist AI datasheet: %s", exc)

    return datasheet
