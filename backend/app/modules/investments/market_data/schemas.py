from typing import Literal, Optional

from pydantic import BaseModel

FreshnessStatusT = Literal[
    "live", "fresh", "delayed", "eod", "closed", "stale", "error", "unknown"
]


class QuoteOut(BaseModel):
    # ── Campos originales (backward compat) ───────────────────────────────────
    symbol: str
    name: str
    category: str
    price: Optional[float]
    change_pct: Optional[float]
    currency: str
    sparkline: list[float]
    last_updated: str
    market_open: bool

    # ── Campos nuevos (Fase 4.5) ──────────────────────────────────────────────
    change_absolute: Optional[float] = None
    freshness_status: FreshnessStatusT = "unknown"
    source: str = "unknown"
    is_fallback: bool = False
    is_stale: bool = False
    warning: Optional[str] = None
    confidence_score: float = 0.0
