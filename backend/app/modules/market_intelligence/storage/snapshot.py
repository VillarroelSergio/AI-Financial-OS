"""Generador de market snapshot JSON desde DuckDB."""
from __future__ import annotations

from datetime import datetime, timezone

from app.modules.market_intelligence.storage import repository


def generate_snapshot() -> dict:
    """Genera snapshot completo del estado de mercado desde DuckDB."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "macro": repository.get_latest_macro_all(),
        "quotes": repository.get_latest_quotes(),
        "forex": repository.get_latest_forex(),
        "bonds": repository.get_latest_bonds(),
        "news": repository.get_latest_news(limit=10),
    }
