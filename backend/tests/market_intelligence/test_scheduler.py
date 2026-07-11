"""ECO-5: el scheduler solo marca vencido lo que su frequency indica."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.modules.market_intelligence.ingestion import scheduler

NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _ind(frequency):
    return SimpleNamespace(id="x", frequency=frequency, dashboard=True)


def test_due_when_never_ingested():
    assert scheduler.is_due(_ind("monthly"), None, NOW) is True
    assert scheduler.is_due(_ind("monthly"), {"last_success_at": None}, NOW) is True


def test_monthly_not_due_after_one_day():
    state = {"last_success_at": NOW - timedelta(days=1)}
    assert scheduler.is_due(_ind("monthly"), state, NOW) is False


def test_monthly_due_after_interval():
    state = {"last_success_at": NOW - timedelta(days=28)}
    assert scheduler.is_due(_ind("monthly"), state, NOW) is True


def test_daily_due_after_a_day_but_not_after_an_hour():
    assert scheduler.is_due(_ind("daily"), {"last_success_at": NOW - timedelta(hours=1)}, NOW) is False
    assert scheduler.is_due(_ind("daily"), {"last_success_at": NOW - timedelta(hours=21)}, NOW) is True


def test_quarterly_needs_months():
    assert scheduler.is_due(_ind("quarterly"), {"last_success_at": NOW - timedelta(days=30)}, NOW) is False
    assert scheduler.is_due(_ind("quarterly"), {"last_success_at": NOW - timedelta(days=89)}, NOW) is True


def test_naive_timestamp_is_treated_as_utc():
    # DuckDB puede devolver naive; no debe petar ni dar siempre due.
    state = {"last_success_at": (NOW - timedelta(days=1)).replace(tzinfo=None)}
    assert scheduler.is_due(_ind("monthly"), state, NOW) is False


def test_due_item_ids_filters_mixed_frequencies():
    inds = [_ind_id("ipc", "monthly"), _ind_id("eur_usd", "daily")]
    state = {
        "ipc": {"last_success_at": NOW - timedelta(days=1)},      # mensual, fresco → no
        "eur_usd": {"last_success_at": NOW - timedelta(days=1)},  # diario, vencido → sí
    }
    assert scheduler.due_item_ids(inds, state, NOW) == ["eur_usd"]


def _ind_id(id_, frequency):
    return SimpleNamespace(id=id_, frequency=frequency, dashboard=True)
