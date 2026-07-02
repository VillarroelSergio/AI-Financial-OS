"""Minimal persistence for dismissed insights only. All other insights are computed on-demand."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

_DB_URL = settings.DATABASE_URL
_DB_PATH = Path(_DB_URL.replace("sqlite:///", "").replace("sqlite://", ""))
_DISMISSALS_PATH = _DB_PATH.parent / "dismissed_insights.json"


def _load() -> dict[str, str]:
    if _DISMISSALS_PATH.exists():
        try:
            return json.loads(_DISMISSALS_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save(data: dict[str, str]) -> None:
    _DISMISSALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DISMISSALS_PATH.write_text(json.dumps(data, indent=2))


def dismiss(insight_id: str) -> str:
    data = _load()
    now = datetime.now(timezone.utc).isoformat()
    data[insight_id] = now
    _save(data)
    return now


def is_dismissed(insight_id: str) -> bool:
    return insight_id in _load()


def get_dismissed_ids() -> set[str]:
    return set(_load().keys())
