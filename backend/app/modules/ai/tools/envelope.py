"""Shared tool result envelope helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def quality_from_sources(sources: list[dict[str, Any]], default: float = 1.0) -> float:
    scores = [float(s["quality_score"]) for s in sources if s.get("quality_score") is not None]
    return round(sum(scores) / len(scores), 3) if scores else default


def ok(
    tool: str,
    data: dict[str, Any] | list[Any],
    sources: list[dict[str, Any]] | None = None,
    quality_score: float | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    source_list = sources or []
    return {
        "ok": True,
        "tool": tool,
        "data": data,
        "sources": source_list,
        "quality_score": quality_score if quality_score is not None else quality_from_sources(source_list),
        "warnings": warnings or [],
    }


def fail(tool: str, message: str, error: str | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool,
        "data": None,
        "sources": [],
        "quality_score": 0,
        "warnings": [message],
        "error": error or message,
    }


def source(
    *,
    source_type: str,
    provider: str | None = None,
    catalog_item_id: str | None = None,
    source_url: str | None = None,
    observed_at: str | None = None,
    retrieved_at: str | None = None,
    quality_score: float | None = None,
    model_type: str | None = None,
    source_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "type": source_type,
        "id": source_id or catalog_item_id,
        "provider": provider,
        "source_url": source_url,
        "observed_at": observed_at,
        "retrieved_at": retrieved_at or utc_now(),
        "quality_score": quality_score,
        "catalog_item_id": catalog_item_id,
        "model_type": model_type,
    }
    return {k: v for k, v in payload.items() if v is not None}
