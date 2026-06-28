"""ProviderOrchestrator — selección y fallback de providers por CatalogIndicator.

Adaptado de market-data-poc/services/orchestrator.py.
"""
from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass

from app.modules.market_intelligence.catalog.schemas import CatalogIndicator
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    ProviderMetadata,
)

logger = logging.getLogger("market_intelligence.orchestrator")


@dataclass
class CatalogFetchResult:
    indicator: CatalogIndicator
    adapter_result: AdapterResult
    provider_used: str
    fallback_used: bool
    catalog_id: str


class ProviderOrchestrator:
    def __init__(self, adapters: list[BaseAdapter]):
        self._adapters = adapters

    def _get_adapter(self, provider_id: str) -> BaseAdapter | None:
        return next(
            (
                a for a in self._adapters
                if (
                    getattr(a, "provider_id", None) == provider_id
                    or a.name.lower().replace(" ", "_") == provider_id
                    or getattr(a, "_provider_id", None) == provider_id
                )
            ),
            None,
        )

    def fetch_indicator(self, indicator: CatalogIndicator) -> CatalogFetchResult:
        chain = [
            indicator.provider_primary,
            indicator.provider_secondary,
            indicator.provider_fallback,
        ]
        for provider_id in [p for p in chain if p]:
            adapter = self._get_adapter(provider_id)
            if adapter is None:
                logger.debug("No adapter found for provider '%s'", provider_id)
                continue
            if not adapter.is_available():
                logger.info("Provider '%s' not available (API key missing?)", provider_id)
                continue
            if not adapter.supports(indicator.id):
                logger.debug("Provider '%s' does not support indicator '%s'", provider_id, indicator.id)
                continue
            try:
                signature = inspect.signature(adapter.fetch)
                result = adapter.fetch(indicator.id) if signature.parameters else adapter.fetch()
            except Exception as exc:
                logger.warning("Adapter '%s' raised exception: %s", provider_id, exc)
                continue
            logger.info(
                "fetch indicator=%s provider=%s success=%s fallback=%s latency=%.0fms",
                indicator.id, provider_id, result.success, provider_id != indicator.provider_primary,
                result.latency_ms,
            )
            if result.success:
                return CatalogFetchResult(
                    indicator=indicator,
                    adapter_result=result,
                    provider_used=provider_id,
                    fallback_used=(provider_id != indicator.provider_primary),
                    catalog_id=indicator.id,
                )

        _empty_meta = ProviderMetadata(
            name="Orchestrator", id="orchestrator", category="orchestration",
            region="Global", method="internal", base_url="",
            requires_api_key=False, declared_update_frequency="unknown",
            declared_historical_depth_years=0, license="internal",
        )
        return CatalogFetchResult(
            indicator=indicator,
            adapter_result=AdapterResult(
                provider="Orchestrator", success=False, records=[],
                error=f"No provider produced data for '{indicator.id}'",
                latency_ms=0.0, raw_sample=None, metadata=_empty_meta,
            ),
            provider_used="none",
            fallback_used=False,
            catalog_id=indicator.id,
        )

    def health(self) -> list:
        return [a.health_check() for a in self._adapters]
