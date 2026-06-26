import pytest
from catalog import CatalogLoader


def test_load_all_returns_all_indicators():
    loader = CatalogLoader()
    indicators = loader.load_all()
    assert len(indicators) >= 52


def test_get_by_id_found():
    loader = CatalogLoader()
    ind = loader.get_by_id("euribor_3m")
    assert ind is not None
    assert ind.id == "euribor_3m"
    assert ind.provider_primary == "bde"


def test_get_by_id_not_found():
    loader = CatalogLoader()
    assert loader.get_by_id("nonexistent_indicator") is None


def test_get_by_priority_critical():
    loader = CatalogLoader()
    critical = loader.get_by_priority("critical")
    assert len(critical) >= 10
    assert all(i.priority == "critical" for i in critical)


def test_get_by_priority_multiple():
    loader = CatalogLoader()
    high_and_critical = loader.get_by_priority("critical", "high")
    assert len(high_and_critical) >= 25
    assert all(i.priority in ("critical", "high") for i in high_and_critical)


def test_get_by_provider():
    loader = CatalogLoader()
    bde_indicators = loader.get_by_provider("bde")
    assert len(bde_indicators) >= 2
    ids = [i.id for i in bde_indicators]
    assert "euribor_3m" in ids


def test_get_by_category():
    loader = CatalogLoader()
    forex = loader.get_by_category("forex")
    assert len(forex) == 8
    assert all(i.category == "forex" for i in forex)


def test_validate_no_errors():
    loader = CatalogLoader()
    errors = loader.validate()
    assert errors == [], f"Validation errors: {errors}"


def test_all_have_required_fields():
    loader = CatalogLoader()
    for ind in loader.load_all():
        assert ind.id, f"Missing id in {ind}"
        assert ind.name, f"Missing name in {ind}"
        assert ind.provider_primary, f"Missing provider_primary in {ind.id}"
        assert ind.priority in ("critical", "high", "medium", "low"), \
            f"Invalid priority '{ind.priority}' in {ind.id}"
        assert ind.frequency in ("realtime", "daily", "weekly", "monthly", "quarterly", "yearly"), \
            f"Invalid frequency '{ind.frequency}' in {ind.id}"
