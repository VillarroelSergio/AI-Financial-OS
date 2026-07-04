"""BaseAdapter para el Market Intelligence Layer.

Adaptado de market-data-poc/adapters/base.py con imports actualizados.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
import time

from app.modules.market_intelligence.ingestion.models import (
    AdapterResult, ProviderHealth, ProviderMetadata, ProviderStatus,
)
from app.modules.market_intelligence.ingestion.config import get_api_key


def redact_api_key(value: str, api_key: str | None) -> str:
    return value.replace(api_key, "***") if api_key else value


class BaseAdapter(ABC):
    name: str = ""
    category: str = ""
    region: str = ""
    requires_api_key: bool = False
    api_key_names: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"
    supported_indicators: dict[str, dict] = {}

    @abstractmethod
    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ...

    def is_available(self) -> bool:
        if self.requires_api_key:
            key_names = self.api_key_names or (self.name,)
            return any(get_api_key(name) is not None for name in key_names)
        return True

    def supports(self, indicator_id: str) -> bool:
        return not self.supported_indicators or indicator_id in self.supported_indicators

    def _make_metadata(self, **kwargs) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            id=kwargs.get("id", self.name.lower().replace(" ", "_")),
            category=self.category,
            region=self.region,
            method=kwargs.get("method", "api"),
            base_url=kwargs.get("base_url", ""),
            requires_api_key=self.requires_api_key,
            declared_update_frequency=kwargs.get("declared_update_frequency", "unknown"),
            declared_historical_depth_years=kwargs.get("declared_historical_depth_years", 0),
            license=kwargs.get("license", "unknown"),
            notes=kwargs.get("notes", ""),
            capabilities=kwargs.get("capabilities", self.capabilities),
            priority=kwargs.get("priority", self.priority),
        )

    def health_check(self, timeout: int = 10) -> ProviderHealth:
        t0 = time.perf_counter()
        try:
            if not self.is_available():
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.OFFLINE,
                    checked_at=datetime.utcnow(),
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    error="Provider unavailable or required API key missing",
                )
            result = self.fetch()
            status = ProviderStatus.ONLINE if result.success else ProviderStatus.DEGRADED
            return ProviderHealth(
                provider=self.name,
                status=status,
                checked_at=datetime.utcnow(),
                latency_ms=result.latency_ms,
                error=result.error,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.OFFLINE,
                checked_at=datetime.utcnow(),
                latency_ms=(time.perf_counter() - t0) * 1000,
                error=str(exc),
            )
