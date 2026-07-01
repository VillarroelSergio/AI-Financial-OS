"""Tests for Phase 8: Goals Simulation Service."""
from __future__ import annotations

from datetime import date

import pytest

from app.modules.goals.simulation_service import (
    DEFAULT_INFLATION,
    _monthly_balance,
    _months_to_target,
    simulate_goal,
)


# ── Unit: monthly balance formula ─────────────────────────────────────────────

def test_monthly_balance_zero_rate():
    """Zero growth: linear accumulation."""
    assert _monthly_balance(1000, 100, 0.0, 12) == pytest.approx(2200.0)


def test_monthly_balance_compound():
    """Compound growth increases faster than linear."""
    r_monthly = (1 + 0.06) ** (1 / 12) - 1
    balance = _monthly_balance(0, 100, r_monthly, 12)
    assert balance > 1200  # more than pure savings


def test_monthly_balance_no_contribution():
    """No contributions: pure compound growth."""
    r_monthly = (1 + 0.06) ** (1 / 12) - 1
    balance = _monthly_balance(10000, 0, r_monthly, 12)
    assert balance == pytest.approx(10000 * (1 + 0.06), rel=1e-3)


# ── Unit: months to target ────────────────────────────────────────────────────

def test_months_to_target_already_reached():
    assert _months_to_target(5000, 100, 0.0, 4000, 360) == 0


def test_months_to_target_zero_rate_pure_savings():
    # Need 1000 more, contributing 100/month → 10 months
    k = _months_to_target(0, 100, 0.0, 1000, 360)
    assert k == 10


def test_months_to_target_zero_contribution_no_growth():
    k = _months_to_target(500, 0, 0.0, 1000, 360)
    assert k is None


def test_months_to_target_with_growth():
    r_monthly = (1 + 0.06) ** (1 / 12) - 1
    k = _months_to_target(0, 500, r_monthly, 10000, 360)
    assert k is not None
    assert k < 360


def test_months_to_target_not_achievable():
    k = _months_to_target(0, 0, 0.0, 1000, 12)
    assert k is None


# ── Unit: simulate_goal ───────────────────────────────────────────────────────

def test_simulate_goal_returns_three_scenarios():
    result = simulate_goal("test-id", 0, 10000, 200)
    assert len(result.scenarios) == 3
    names = {s.scenario for s in result.scenarios}
    assert names == {"conservative", "base", "optimistic"}


def test_simulate_goal_optimistic_faster_than_conservative():
    result = simulate_goal("test-id", 0, 10000, 200)
    conservative = next(s for s in result.scenarios if s.scenario == "conservative")
    optimistic = next(s for s in result.scenarios if s.scenario == "optimistic")
    # optimistic reaches goal in fewer months
    if conservative.months_to_target and optimistic.months_to_target:
        assert optimistic.months_to_target <= conservative.months_to_target


def test_simulate_goal_monthly_data_starts_at_current():
    result = simulate_goal("test-id", 1000, 10000, 100)
    assert result.monthly_data[0].conservative == pytest.approx(1000, rel=1e-3)
    assert result.monthly_data[0].base == pytest.approx(1000, rel=1e-3)


def test_simulate_goal_monthly_data_grows():
    result = simulate_goal("test-id", 0, 5000, 200)
    # After several months, base scenario (6%) should exceed conservative (2%)
    assert result.monthly_data[6].conservative > 0
    assert result.monthly_data[6].base > result.monthly_data[6].conservative


def test_simulate_goal_inflation_adjusted_target():
    result = simulate_goal("test-id", 0, 10000, 500, inflation_rate=0.03)
    # With positive inflation and months > 0, adjusted target > original
    assert result.inflation_adjusted_target >= 10000


def test_simulate_goal_already_reached():
    result = simulate_goal("test-id", 10000, 10000, 0)
    for s in result.scenarios:
        assert s.months_to_target == 0


def test_simulate_goal_target_date_achievability():
    today = date.today()
    # Target 5 years away, generous contribution — should be achievable
    far_date = date(today.year + 5, today.month, 1)
    result = simulate_goal("test-id", 0, 10000, 300, target_date=far_date)
    base = next(s for s in result.scenarios if s.scenario == "base")
    assert base.achievable_by_target_date is not None


def test_simulate_goal_no_target_date_achievability_is_none():
    result = simulate_goal("test-id", 0, 10000, 200, target_date=None)
    for s in result.scenarios:
        assert s.achievable_by_target_date is None


def test_simulate_goal_max_months_cap():
    # Tiny contribution, huge target — should hit max_months cap
    result = simulate_goal("test-id", 0, 1_000_000, 1, max_months=120)
    conservative = next(s for s in result.scenarios if s.scenario == "conservative")
    assert conservative.months_to_target is None


def test_simulate_goal_chart_data_capped():
    """Monthly data should not exceed 121 points (0..120) for readability."""
    result = simulate_goal("test-id", 0, 100_000, 500, max_months=360)
    assert len(result.monthly_data) <= 122  # 0..120 + possible rounding


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_simulate_endpoint_requires_existing_goal(client):
    r = client.post(
        "/api/goals/nonexistent-id/simulate",
        json={"inflation_rate": 0.03, "max_months": 360},
    )
    assert r.status_code == 404


def test_simulate_endpoint_full_flow(client):
    # Create goal
    r = client.post(
        "/api/goals",
        json={
            "name": "Fondo de emergencia",
            "type": "emergency_fund",
            "target_amount": "10000",
            "current_amount": "2000",
            "monthly_contribution": "300",
            "priority": "high",
        },
    )
    assert r.status_code == 201
    goal_id = r.json()["id"]

    # Simulate
    r = client.post(
        f"/api/goals/{goal_id}/simulate",
        json={"inflation_rate": 0.03, "max_months": 360},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["goal_id"] == goal_id
    assert len(data["scenarios"]) == 3
    assert len(data["monthly_data"]) > 0
    assert data["inflation_adjusted_target"] >= 10000
    # Base scenario should find a target date
    base = next(s for s in data["scenarios"] if s["scenario"] == "base")
    assert base["projected_date"] is not None


def test_progress_endpoint(client):
    r = client.post(
        "/api/goals",
        json={
            "name": "Ahorro viaje",
            "type": "savings",
            "target_amount": "5000",
            "current_amount": "2500",
            "priority": "medium",
        },
    )
    assert r.status_code == 201
    goal_id = r.json()["id"]

    r = client.get(f"/api/goals/{goal_id}/progress")
    assert r.status_code == 200
    data = r.json()
    assert data["progress_pct"] == pytest.approx(50.0)
    assert data["remaining"] == pytest.approx(2500.0)


def test_simulate_default_inflation(client):
    r = client.post(
        "/api/goals",
        json={
            "name": "Test",
            "type": "custom",
            "target_amount": "1000",
            "current_amount": "0",
            "monthly_contribution": "100",
            "priority": "low",
        },
    )
    goal_id = r.json()["id"]
    r = client.post(f"/api/goals/{goal_id}/simulate", json={})
    assert r.status_code == 200
    assert r.json()["inflation_rate"] == pytest.approx(DEFAULT_INFLATION)


# ── Phase 10.6 validation cases ───────────────────────────────────────────────

from app.modules.goals.simulation_service import SimulationResult  # noqa: E402


def test_goal_zero_initial_capital():
    """Capital inicial 0, aportación positiva → debe alcanzar objetivo."""
    result = simulate_goal(
        goal_id="test-1",
        current_amount=0.0,
        target_amount=10000.0,
        monthly_contribution=200.0,
        target_date=None,
        inflation_rate=0.03,
    )
    assert isinstance(result, SimulationResult)
    base = next(s for s in result.scenarios if s.scenario == "base")
    assert base.months_to_target is not None
    assert base.months_to_target > 0


def test_goal_zero_contribution():
    """Aportación 0 con capital inicial — solo crece por rentabilidad."""
    result = simulate_goal(
        goal_id="test-2",
        current_amount=5000.0,
        target_amount=10000.0,
        monthly_contribution=0.0,
        target_date=None,
        inflation_rate=0.0,
    )
    conservative = next(s for s in result.scenarios if s.scenario == "conservative")
    # Con 2% anual y 0 aportación, desde 5000 a 10000 tarda ~35 años
    assert conservative.months_to_target is None or conservative.months_to_target > 300


def test_goal_unreachable_in_time_shows_required_contribution():
    """Objetivo no alcanzable debe calcular aportación necesaria."""
    from datetime import timedelta
    target = (date.today() + timedelta(days=365)).isoformat()  # 1 año
    result = simulate_goal(
        goal_id="test-3",
        current_amount=0.0,
        target_amount=50000.0,
        monthly_contribution=100.0,
        target_date=date.fromisoformat(target),
        inflation_rate=0.0,
    )
    # En 12 meses con 100€/mes no se llegan a 50.000€
    base = next(s for s in result.scenarios if s.scenario == "base")
    assert base.achievable_by_target_date is False
    assert result.monthly_contribution_needed is not None
    assert result.monthly_contribution_needed > 100.0


def test_scenarios_are_ordered_correctly():
    """Conservador ≤ Base ≤ Optimista en monto final."""
    result = simulate_goal(
        goal_id="test-4",
        current_amount=1000.0,
        target_amount=20000.0,
        monthly_contribution=200.0,
        target_date=None,
        inflation_rate=0.0,
    )
    amounts = {s.scenario: s.final_amount for s in result.scenarios}
    assert amounts["conservative"] <= amounts["base"] <= amounts["optimistic"]
