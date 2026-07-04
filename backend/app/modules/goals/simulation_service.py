"""Goal simulation service — Phase 8: Goals & Simulations.

Calculates compound-growth projections for a financial goal under three
scenarios (conservative / base / optimistic) with optional inflation adjustment.

All computation is deterministic and local — no external API calls.

Scenario annual nominal growth rates (defaults):
  Conservative : 2 %   (pure savings/deposit, low-yield)
  Base         : 6 %   (balanced portfolio)
  Optimistic   : 10 %  (equity-heavy portfolio)

Inflation default: 3 % per year (European historical average).

Formula (per month k, with monthly rate rₘ = (1+r)^(1/12) − 1):
  S_k = S₀ · (1+rₘ)^k  +  C · [(1+rₘ)^k − 1] / rₘ    when rₘ > 0
  S_k = S₀ + C · k                                       when rₘ = 0

Months to target: first k where S_k ≥ T.
Inflation-adjusted target: T · (1 + inflation)^(months/12) expressed in
  future euros — this tells the user how much they'll need nominally to
  preserve the purchasing power of today's target.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

# ── Scenario definitions ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScenarioConfig:
    name: str                  # "conservative" | "base" | "optimistic"
    label: str                 # Human-readable label
    annual_growth_rate: float  # Nominal annual rate (0.02 = 2 %)
    color: str                 # UI color hint


SCENARIOS: list[ScenarioConfig] = [
    ScenarioConfig("conservative", "Conservador", 0.02, "#94a3b8"),  # stone
    ScenarioConfig("base",         "Base",        0.06, "#10b981"),  # emerald
    ScenarioConfig("optimistic",   "Optimista",   0.10, "#f59e0b"),  # amber
]

DEFAULT_INFLATION = 0.03  # 3 % per year
MAX_MONTHS = 360          # 30 years hard cap


# ── Output types ──────────────────────────────────────────────────────────────

@dataclass
class MonthlyDataPoint:
    month: int          # 0 = today
    label: str          # e.g. "Ene 2026"
    conservative: float
    base: float
    optimistic: float


@dataclass
class ScenarioProjection:
    scenario: str
    label: str
    color: str
    annual_growth_rate: float
    months_to_target: Optional[int]   # None if not reached within MAX_MONTHS
    projected_date: Optional[str]     # ISO date string, or None
    achievable_by_target_date: Optional[bool]   # None when no target_date given
    final_amount: float               # amount at max horizon or when target hit


@dataclass
class SimulationResult:
    goal_id: str
    current_amount: float
    target_amount: float
    monthly_contribution: float
    monthly_contribution_needed: Optional[float]  # Required monthly contribution to reach target by target_date (base scenario), or None
    inflation_rate: float
    inflation_adjusted_target: float  # target in future euros (at base horizon)
    monthly_data: list[MonthlyDataPoint]
    scenarios: list[ScenarioProjection]
    target_date: Optional[str]
    generated_at: str


# ── Core calculation ──────────────────────────────────────────────────────────

def _monthly_balance(
    start: float,
    contribution: float,
    monthly_rate: float,
    months: int,
) -> float:
    """Balance after `months` with compound growth and monthly contributions."""
    if monthly_rate == 0.0:
        return start + contribution * months
    return (
        start * (1 + monthly_rate) ** months
        + contribution * ((1 + monthly_rate) ** months - 1) / monthly_rate
    )


def _months_to_target(
    start: float,
    contribution: float,
    monthly_rate: float,
    target: float,
    max_months: int,
) -> Optional[int]:
    """First month k where balance ≥ target, or None if not reached."""
    if start >= target:
        return 0
    if contribution <= 0 and monthly_rate == 0.0:
        return None  # no growth, can never reach

    for k in range(1, max_months + 1):
        if _monthly_balance(start, contribution, monthly_rate, k) >= target:
            return k
    return None


def _add_months(d: date, months: int) -> date:
    """Add a given number of months to a date, clamping to end-of-month."""
    import calendar
    y, m = divmod(d.month - 1 + months, 12)
    new_year = d.year + y
    new_month = m + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    return d.replace(year=new_year, month=new_month, day=min(d.day, max_day))


def _month_label(d: date) -> str:
    MONTHS_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    return f"{MONTHS_ES[d.month - 1]} {d.year}"


def _months_between(d1: date, d2: date) -> int:
    """Approximate number of months between two dates (d2 - d1)."""
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


# ── Public API ────────────────────────────────────────────────────────────────

def simulate_goal(
    goal_id: str,
    current_amount: float,
    target_amount: float,
    monthly_contribution: float,
    target_date: Optional[date] = None,
    inflation_rate: float = DEFAULT_INFLATION,
    max_months: int = MAX_MONTHS,
    scenarios: Optional[list[ScenarioConfig]] = None,
) -> SimulationResult:
    """Run a three-scenario compound-growth simulation for a goal.

    Parameters
    ----------
    goal_id            : Identifier passed through to the result.
    current_amount     : Current savings toward the goal (EUR).
    target_amount      : Goal target (EUR).
    monthly_contribution: Fixed monthly deposit (EUR). 0 if none.
    target_date        : Optional deadline; used only to flag achievability.
    inflation_rate     : Annual inflation rate (default 3 %).
    max_months         : Simulation horizon cap (default 360 = 30 years).
    scenarios          : Override scenario list (defaults to SCENARIOS).
    """
    if scenarios is None:
        scenarios = SCENARIOS

    today = date.today()

    # Determine months to target_date (for achievability check)
    months_to_deadline: Optional[int] = None
    if target_date and target_date > today:
        delta = (target_date.year - today.year) * 12 + (target_date.month - today.month)
        months_to_deadline = max(0, delta)

    # Compute horizon: furthest scenario projection or deadline, capped
    scenario_projections: list[ScenarioProjection] = []
    max_scenario_months = 0

    for sc in scenarios:
        rₘ = (1 + sc.annual_growth_rate) ** (1 / 12) - 1
        k = _months_to_target(current_amount, monthly_contribution, rₘ, target_amount, max_months)
        proj_date_str: Optional[str] = None
        achievable: Optional[bool] = None

        if k is not None:
            proj_date = _add_months(today, k)
            proj_date_str = proj_date.isoformat()
            if months_to_deadline is not None:
                achievable = k <= months_to_deadline
            final = target_amount
            max_scenario_months = max(max_scenario_months, k)
        else:
            final = _monthly_balance(current_amount, monthly_contribution, rₘ, max_months)
            max_scenario_months = max(max_scenario_months, max_months)
            if months_to_deadline is not None:
                achievable = False

        scenario_projections.append(
            ScenarioProjection(
                scenario=sc.name,
                label=sc.label,
                color=sc.color,
                annual_growth_rate=sc.annual_growth_rate,
                months_to_target=k,
                projected_date=proj_date_str,
                achievable_by_target_date=achievable,
                final_amount=round(final, 2),
            )
        )

    # Chart horizon: up to optimistic target or deadline (whichever is shorter),
    # but at least 12 months and at most 120 months for readability.
    chart_months = min(max(max_scenario_months, 12), 120)

    # Monthly data points (sampled every month up to chart_months)
    monthly_data: list[MonthlyDataPoint] = []
    rates = [(1 + sc.annual_growth_rate) ** (1 / 12) - 1 for sc in scenarios]

    for k in range(0, chart_months + 1):
        pt_date = _add_months(today, k)
        values = [
            round(min(_monthly_balance(current_amount, monthly_contribution, rₘ, k), target_amount * 1.05), 2)
            for rₘ in rates
        ]
        monthly_data.append(
            MonthlyDataPoint(
                month=k,
                label=_month_label(pt_date),
                conservative=values[0],
                base=values[1],
                optimistic=values[2],
            )
        )

    # Inflation-adjusted target at base scenario horizon (or deadline)
    base_months = scenario_projections[1].months_to_target or max_months
    inflation_adjusted_target = round(
        target_amount * (1 + inflation_rate) ** (base_months / 12), 2
    )

    # Monthly contribution needed to reach target by target_date (base scenario, 6% annual)
    monthly_contribution_needed: Optional[float] = None
    if target_date:
        base_scenario = next((s for s in scenario_projections if s.scenario == "base"), None)
        if base_scenario and base_scenario.achievable_by_target_date is False:
            months_remaining = _months_between(today, target_date)
            if months_remaining > 0:
                r_m = (1 + 0.06) ** (1 / 12) - 1  # base monthly rate
                if r_m > 0:
                    future_value_of_current = current_amount * (1 + r_m) ** months_remaining
                    remaining = target_amount - future_value_of_current
                    monthly_contribution_needed = remaining * r_m / ((1 + r_m) ** months_remaining - 1)
                else:
                    monthly_contribution_needed = (target_amount - current_amount) / months_remaining
                monthly_contribution_needed = max(0.0, round(monthly_contribution_needed, 2))

    from datetime import datetime, timezone
    return SimulationResult(
        goal_id=goal_id,
        current_amount=current_amount,
        target_amount=target_amount,
        monthly_contribution=monthly_contribution,
        monthly_contribution_needed=monthly_contribution_needed,
        inflation_rate=inflation_rate,
        inflation_adjusted_target=inflation_adjusted_target,
        monthly_data=monthly_data,
        scenarios=scenario_projections,
        target_date=target_date.isoformat() if target_date else None,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
