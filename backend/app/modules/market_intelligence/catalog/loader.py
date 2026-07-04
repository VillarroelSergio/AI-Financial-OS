"""CatalogLoader — carga y valida los indicadores del catálogo YAML."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator

_CATALOG_DIR = Path(__file__).parent / "yaml"
_VALID_PRIORITIES = {"critical", "high", "medium", "low"}
_VALID_FREQUENCIES = {"realtime", "daily", "weekly", "monthly", "quarterly", "yearly"}


class CatalogLoader:
    def __init__(self, catalog_dir: Path | None = None):
        self._dir = catalog_dir or _CATALOG_DIR
        self._cache: list[CatalogIndicator] | None = None

    def load_all(self) -> list[CatalogIndicator]:
        if self._cache is not None:
            return self._cache
        indicators: list[CatalogIndicator] = []
        for yaml_file in sorted(self._dir.glob("*.yaml")):
            raw: list[dict[str, Any]] = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or []
            for entry in raw:
                indicators.append(self._parse(entry))
        self._cache = indicators
        return indicators

    def get_by_id(self, indicator_id: str) -> CatalogIndicator | None:
        return next((i for i in self.load_all() if i.id == indicator_id), None)

    def get_by_priority(self, *priorities: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.priority in priorities]

    def get_by_provider(self, provider_id: str) -> list[CatalogIndicator]:
        return [
            i for i in self.load_all()
            if provider_id in (i.provider_primary, i.provider_secondary, i.provider_fallback)
        ]

    def get_by_category(self, category: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.category == category]

    def get_for_ai(self) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.ai]

    def get_for_dashboard(self) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.dashboard]

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen_ids: set[str] = set()
        for ind in self.load_all():
            if not ind.id:
                errors.append("Indicator missing id")
            elif ind.id in seen_ids:
                errors.append(f"Duplicate id: {ind.id}")
            else:
                seen_ids.add(ind.id)
            if not ind.name:
                errors.append(f"{ind.id}: missing name")
            if not ind.provider_primary:
                errors.append(f"{ind.id}: missing provider_primary")
            if ind.priority not in _VALID_PRIORITIES:
                errors.append(f"{ind.id}: invalid priority '{ind.priority}'")
            if ind.frequency not in _VALID_FREQUENCIES:
                errors.append(f"{ind.id}: invalid frequency '{ind.frequency}'")
        return errors

    @staticmethod
    def _parse(entry: dict[str, Any]) -> CatalogIndicator:
        return CatalogIndicator(
            id=entry["id"],
            name=entry["name"],
            category=entry.get("category", ""),
            subcategory=entry.get("subcategory", ""),
            country=entry.get("country", "GLOBAL"),
            region=entry.get("region", "Global"),
            frequency=entry.get("frequency", "monthly"),
            priority=entry.get("priority", "medium"),
            dashboard=bool(entry.get("dashboard", False)),
            ai=bool(entry.get("ai", False)),
            historical=entry.get("historical", "1y"),
            retention=entry.get("retention", "1y"),
            unit=entry.get("unit", ""),
            description=entry.get("description", ""),
            provider_primary=entry.get("provider_primary", ""),
            provider_secondary=entry.get("provider_secondary"),
            provider_fallback=entry.get("provider_fallback"),
        )
