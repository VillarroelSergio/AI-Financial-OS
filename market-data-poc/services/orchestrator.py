import logging
from dataclasses import dataclass
from typing import Iterable

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderHealth, ProviderMetadata, ProviderPriority, ProviderStatus
from models.catalog import CatalogIndicator, CatalogFetchResult
from services.cache import LocalTTLCache

logger = logging.getLogger("market_data_poc")


@dataclass
class ProviderSelection:
    capability: str
    primary: BaseAdapter | None
    secondary: BaseAdapter | None
    fallback: BaseAdapter | None
    scraper: BaseAdapter | None


class ProviderSelector:
    def __init__(self, adapters: Iterable[BaseAdapter]):
        self.adapters = list(adapters)

    def select(self, capability: str) -> ProviderSelection:
        candidates = [a for a in self.adapters if capability in getattr(a, "capabilities", ())]
        ordered = {
            ProviderPriority.PRIMARY.value: None,
            ProviderPriority.SECONDARY.value: None,
            ProviderPriority.FALLBACK.value: None,
            ProviderPriority.SCRAPER.value: None,
        }
        for adapter in candidates:
            priority = getattr(adapter, "priority", ProviderPriority.FALLBACK.value)
            if ordered.get(priority) is None:
                ordered[priority] = adapter
        remaining = [a for a in candidates if a not in ordered.values()]
        for priority in ordered:
            if ordered[priority] is None and remaining:
                ordered[priority] = remaining.pop(0)
        return ProviderSelection(
            capability=capability,
            primary=ordered[ProviderPriority.PRIMARY.value],
            secondary=ordered[ProviderPriority.SECONDARY.value],
            fallback=ordered[ProviderPriority.FALLBACK.value],
            scraper=ordered[ProviderPriority.SCRAPER.value],
        )


class ProviderOrchestrator:
    def __init__(self, adapters: Iterable[BaseAdapter], cache: LocalTTLCache | None = None):
        self.adapters = list(adapters)
        self.selector = ProviderSelector(self.adapters)
        self.cache = cache

    def fetch(self, capability: str, use_cache: bool = True) -> AdapterResult:
        selection = self.selector.select(capability)
        chain = [selection.primary, selection.secondary, selection.fallback, selection.scraper]
        for adapter in [a for a in chain if a is not None]:
            if not adapter.is_available():
                logger.info("provider_unavailable", extra={"provider": adapter.name, "capability": capability})
                continue

            def _run(adapter=adapter):
                logger.info("provider_fetch_start", extra={"provider": adapter.name, "capability": capability})
                return adapter.fetch()

            result = (
                self.cache.get_or_set(f"{adapter.name}:{capability}", _run)
                if self.cache and use_cache
                else _run()
            )
            logger.info(
                "provider_fetch_done",
                extra={
                    "provider": adapter.name,
                    "capability": capability,
                    "success": result.success,
                    "latency_ms": result.latency_ms,
                    "fallback_used": adapter is not selection.primary,
                    "error": result.error,
                },
            )
            if result.success:
                return result
        return AdapterResult(
            provider="Provider Orchestrator",
            success=False,
            records=[],
            error=f"No provider produced data for capability '{capability}'",
            latency_ms=0.0,
            raw_sample=None,
            metadata=(
                self.adapters[0]._make_metadata()
                if self.adapters
                else ProviderMetadata(
                    name="Provider Orchestrator",
                    id="provider_orchestrator",
                    category="orchestration",
                    region="Global",
                    method="internal",
                    base_url="",
                    requires_api_key=False,
                    declared_update_frequency="unknown",
                    declared_historical_depth_years=0,
                    license="internal",
                )
            ),
        )

    def _get_adapter(self, provider_id: str) -> BaseAdapter | None:
        return next(
            (a for a in self.adapters if getattr(a, "_provider_id", None) == provider_id
             or a.name.lower().replace(" ", "_") == provider_id
             or getattr(a, "provider_id", None) == provider_id),
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
            if adapter is None or not adapter.supports(indicator.id):
                continue
            result = adapter.fetch(indicator.id)
            if result.success:
                return CatalogFetchResult(
                    indicator=indicator,
                    adapter_result=result,
                    provider_used=provider_id,
                    fallback_used=(provider_id != indicator.provider_primary),
                    catalog_id=indicator.id,
                )
        metadata = ProviderMetadata(
            name="Catalog Orchestrator", id="catalog_orchestrator",
            category="orchestration", region="Global", method="internal",
            base_url="", requires_api_key=False,
            declared_update_frequency="unknown",
            declared_historical_depth_years=0, license="internal",
        )
        return CatalogFetchResult(
            indicator=indicator,
            adapter_result=AdapterResult(
                provider="Catalog Orchestrator", success=False, records=[],
                error=f"No migrated provider supports '{indicator.id}'",
                latency_ms=0.0, raw_sample=None, metadata=metadata,
            ),
            provider_used="none",
            fallback_used=False,
            catalog_id=indicator.id,
        )

    def health(self) -> list[ProviderHealth]:
        checks = []
        for adapter in self.adapters:
            health = adapter.health_check()
            if health.status == ProviderStatus.ONLINE and not adapter.is_available():
                health.status = ProviderStatus.DEGRADED
            checks.append(health)
        return checks
