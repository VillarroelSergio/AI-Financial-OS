"""Persistencia de insights descartados (D3: SQLite, antes JSON).

La firma pública (`dismiss`, `is_dismissed`, `get_dismissed_ids`) no cambia;
solo el almacén. El JSON heredado se migra una vez y se renombra a `.migrated`.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core import database as db_module
from app.core.config import settings
from app.models.insight_dismissal import InsightDismissal

_DB_URL = settings.DATABASE_URL
_DB_PATH = Path(_DB_URL.replace("sqlite:///", "").replace("sqlite://", ""))
_LEGACY_JSON = _DB_PATH.parent / "dismissed_insights.json"


def _migrate_legacy_json() -> None:
    """One-shot reversible: vuelca el JSON heredado a SQLite y lo aparta."""
    if not _LEGACY_JSON.exists():
        return
    try:
        data = json.loads(_LEGACY_JSON.read_text())
    except Exception:
        return
    db = db_module.SessionLocal()
    try:
        existing = {r[0] for r in db.query(InsightDismissal.insight_id).all()}
        for insight_id, iso in data.items():
            if insight_id in existing:
                continue
            try:
                when = datetime.fromisoformat(iso)
            except (TypeError, ValueError):
                when = datetime.now(timezone.utc)
            db.add(InsightDismissal(insight_id=insight_id, dismissed_at=when))
        db.commit()
    finally:
        db.close()
    _LEGACY_JSON.rename(_LEGACY_JSON.with_suffix(".json.migrated"))


def dismiss(insight_id: str) -> str:
    now = datetime.now(timezone.utc)
    db = db_module.SessionLocal()
    try:
        row = db.get(InsightDismissal, insight_id)
        if row is None:
            db.add(InsightDismissal(insight_id=insight_id, dismissed_at=now))
        else:
            row.dismissed_at = now
        db.commit()
    finally:
        db.close()
    return now.isoformat()


def restore(insight_id: str) -> None:
    """Deshace un descarte (INS-7: undo). Idempotente si ya no existe."""
    db = db_module.SessionLocal()
    try:
        row = db.get(InsightDismissal, insight_id)
        if row is not None:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def is_dismissed(insight_id: str) -> bool:
    db = db_module.SessionLocal()
    try:
        return db.get(InsightDismissal, insight_id) is not None
    finally:
        db.close()


def get_dismissed_ids() -> set[str]:
    db = db_module.SessionLocal()
    try:
        return {r[0] for r in db.query(InsightDismissal.insight_id).all()}
    finally:
        db.close()
