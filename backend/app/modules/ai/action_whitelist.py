"""AI-4: lista blanca de rutas enlazables por las acciones del asistente.

Las `actions` que llegan al frontend (`{label, target, params}`) NO las inventa
el LLM: salen de `InsightActionOut` en las reglas de insights. Aun así validamos
el `target` contra las rutas reales del router (apps/desktop/src/App.tsx) para que
una regla con un typo (`/investment`) no produzca un botón que navega a una
pantalla inexistente. Guardia de defensa en profundidad, no de seguridad.

Fuente de verdad: rutas declaradas en App.tsx. Manténla en sync si se añaden.
"""
from __future__ import annotations

# Rutas base válidas del router (con leading slash, sin query).
_ALLOWED_ROUTES = frozenset({
    "/",
    "/finances",
    "/accounts",
    "/transactions",
    "/spending",
    "/planificacion",
    "/imports",
    "/investments",
    "/investments/tracking",
    "/investments/import",
    "/economy",
    "/markets",
    "/goals",
    "/insights",
    "/assistant",
    "/settings",
})

# Prefijos con segmento dinámico (p. ej. /markets/:indicatorCode).
_ALLOWED_PREFIXES = ("/markets/",)


def is_allowed_action(target: object) -> bool:
    """True si `target` es una ruta conocida del frontend. Los params van aparte
    (query/estado), así que se ignora todo lo que siga a '?' o '#'."""
    if not isinstance(target, str) or not target.startswith("/"):
        return False
    path = target.split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"
    if path in _ALLOWED_ROUTES:
        return True
    return any(path.startswith(p) and len(path) > len(p) for p in _ALLOWED_PREFIXES)


if __name__ == "__main__":
    # Self-check: python -m app.modules.ai.action_whitelist
    assert is_allowed_action("/transactions")
    assert is_allowed_action("/investments/tracking")
    assert is_allowed_action("/markets/SP500")          # segmento dinámico
    assert is_allowed_action("/transactions?category=3")  # query se ignora
    assert is_allowed_action("/finances/")              # trailing slash
    assert is_allowed_action("/markets/")               # normaliza a /markets (válido)
    assert not is_allowed_action("/investment")         # typo → fuera
    assert not is_allowed_action("/nope")               # ruta inexistente
    assert not is_allowed_action("https://x.com")       # sin leading slash
    assert not is_allowed_action(None)
    assert not is_allowed_action("")
    print("action_whitelist self-check ok")
