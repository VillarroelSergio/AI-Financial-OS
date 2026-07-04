"""Bridge entre el sistema de API keys del POC y los settings del backend."""
from __future__ import annotations

from app.core.config import settings


def get_api_key(provider_name: str) -> str | None:
    """Devuelve la API key del provider o None si no está configurada.

    Convierte el nombre del provider al nombre de la variable en settings.
    Ejemplo: 'alpha_vantage' → settings.ALPHA_VANTAGE_API_KEY
    """
    env_var = f"{provider_name.upper().replace(' ', '_').replace('-', '_')}_API_KEY"
    value = getattr(settings, env_var, None)
    return value if value else None


def get_timeout() -> int:
    return 15


def get_workers() -> int:
    return 5
