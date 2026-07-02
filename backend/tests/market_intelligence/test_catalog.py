import pytest

from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.catalog.schemas import CatalogIndicator


@pytest.fixture
def loader():
    return CatalogLoader()


def test_load_all_returns_indicators(loader):
    items = loader.load_all()
    assert len(items) > 0
    assert all(isinstance(i, CatalogIndicator) for i in items)


def test_all_items_have_required_fields(loader):
    for item in loader.load_all():
        assert item.id, f"Missing id in {item}"
        assert item.name, f"Missing name in {item.id}"
        assert item.provider_primary, f"Missing provider_primary in {item.id}"


def test_validate_returns_no_errors(loader):
    errors = loader.validate()
    assert errors == [], f"Catalog validation errors: {errors}"


def test_get_by_category(loader):
    macro = loader.get_by_category("macro")
    assert len(macro) > 0
    assert all(i.category == "macro" for i in macro)


def test_get_by_priority(loader):
    critical = loader.get_by_priority("critical")
    assert len(critical) > 0
    assert all(i.priority == "critical" for i in critical)


def test_get_for_ai_returns_ai_items(loader):
    ai_items = loader.get_for_ai()
    assert len(ai_items) > 0
    assert all(i.ai for i in ai_items)


def test_get_by_id_returns_correct_item(loader):
    items = loader.load_all()
    first = items[0]
    found = loader.get_by_id(first.id)
    assert found is not None
    assert found.id == first.id


def test_loader_cache_is_consistent(loader):
    items1 = loader.load_all()
    items2 = loader.load_all()
    assert items1 is items2  # mismo objeto — cache funciona
