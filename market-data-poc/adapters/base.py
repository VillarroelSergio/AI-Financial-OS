from abc import ABC, abstractmethod
from models.base import AdapterResult, ProviderMetadata
from config.settings import get_api_key


class BaseAdapter(ABC):
    name: str
    category: str
    region: str
    requires_api_key: bool = False
    api_key_names: tuple[str, ...] = ()

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
        )
