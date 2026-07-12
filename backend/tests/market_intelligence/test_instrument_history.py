"""MKT-6: stats, downsampling y rangos honestos de la ficha de instrumento.

Prueba la lógica financiera pura (sin DB ni red): monkeypatch de read_historical.
"""
from datetime import date, timedelta

from app.modules.market_intelligence.api import service


def _row(d: date, close: float, *, o=None, h=None, low=None, vol=None):
    return {"date": d, "open": o, "high": h, "low": low, "close": close,
            "volume": vol, "currency": "EUR", "provider_id": "stooq", "quality_score": 0.9}


def test_downsample_keeps_last_point_and_bound():
    rows = [_row(date(2020, 1, 1) + timedelta(days=i), i) for i in range(1000)]
    out = service._downsample(rows, 400)
    assert len(out) <= 400
    assert out[-1] is rows[-1]  # el último dato nunca se pierde


def test_stats_computed_from_series():
    rows = [
        _row(date(2026, 7, 8), 100.0),
        _row(date(2026, 7, 9), 110.0),
        _row(date(2026, 7, 10), 120.0, o=118.0, h=125.0, low=117.0, vol=999),
    ]
    stats = service._compute_stats(rows, rows)
    assert stats.previous_close == 110.0
    assert stats.open == 118.0 and stats.day_high == 125.0 and stats.day_low == 117.0
    assert stats.volume == 999
    # range_change_pct: (120-100)/100 = 20%
    assert stats.range_change_pct == 20.0
    # 52 semanas sobre low/high disponibles (fallback a close donde falten)
    assert stats.week52_high == 125.0


def test_available_ranges_honest_with_short_series(monkeypatch):
    # Serie de ~2 meses: solo cubre 1m (y max), nunca 1y/5y.
    base = date.today() - timedelta(days=60)
    rows = [_row(base + timedelta(days=i), 100.0 + i) for i in range(61)]
    monkeypatch.setattr(service.repository, "read_historical", lambda code: rows)
    out = service.get_instrument_history("ibex35", range_key="5y")
    assert out.available_ranges == ["1m", "max"]
    assert out.range == "max"  # 5y no disponible → cae a max, no finge
    assert out.currency == "EUR" and out.provider_id == "stooq"


def test_empty_series_returns_no_ranges(monkeypatch):
    monkeypatch.setattr(service.repository, "read_historical", lambda code: [])
    out = service.get_instrument_history("nope", range_key="1y")
    assert out.series == [] and out.available_ranges == []


if __name__ == "__main__":
    # ponytail: self-check ejecutable sin pytest.
    test_downsample_keeps_last_point_and_bound()
    test_stats_computed_from_series()
    print("OK (los tests con monkeypatch requieren pytest)")
