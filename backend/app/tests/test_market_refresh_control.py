from types import SimpleNamespace

from app.modules.investments.market_data import router as market_router


class _Cache:
    def get_all_quotes(self, category=None):
        return []


class _Router:
    def __init__(self):
        self.catalog = [SimpleNamespace(category="indices_eu")]
        self._cache = _Cache()
        self.calls = []

    def get_quote(self, asset, *, force_refresh=False):
        self.calls.append((asset, force_refresh))


def test_get_quotes_never_calls_external_providers(monkeypatch):
    fake = _Router()
    monkeypatch.setattr(market_router, "get_router", lambda: fake)

    assert market_router.get_quotes() == []
    assert fake.calls == []


def test_manual_refresh_forces_one_provider_round(monkeypatch):
    fake = _Router()
    monkeypatch.setattr(market_router, "get_router", lambda: fake)

    assert market_router.refresh_quotes() == []
    assert len(fake.calls) == 1
    assert fake.calls[0][1] is True
