from abc import ABC, abstractmethod
from datetime import datetime
import time

from models.base import AdapterResult, ProviderHealth, ProviderMetadata, ProviderStatus
from config.settings import get_api_key


class BaseAdapter(ABC):
    name: str
    category: str
    region: str
    requires_api_key: bool = False
    api_key_names: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"

    @abstractmethod
    def fetch(self) -> AdapterResult:
        ...

    def is_available(self) -> bool:
        if self.requires_api_key:
            key_names = self.api_key_names or (self.name,)
            return any(get_api_key(name) is not None for name in key_names)
        return True

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
