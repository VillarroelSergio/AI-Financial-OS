from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from datetime import date

from app.core.database import get_db
from app.models.goal import Goal
from app.modules.goals.schemas import (
    GoalCreate, GoalOut, GoalProgressOut, GoalUpdate,
    SimulationRequest, SimulationResultOut,
    MonthlyDataPointOut, ScenarioProjectionOut,
)
from app.modules.goals.simulation_service import simulate_goal, DEFAULT_INFLATION

router = APIRouter()


def _goal_or_404(goal_id: str, db: Session) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Objetivo no encontrado"}},
        )
    return goal


@router.get("", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db)) -> list[Goal]:
    return db.query(Goal).order_by(Goal.created_at.desc()).all()


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)) -> Goal:
    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: str, payload: GoalUpdate, db: Session = Depends(get_db)) -> Goal:
    goal = _goal_or_404(goal_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: str, db: Session = Depends(get_db)) -> Response:
    goal = _goal_or_404(goal_id, db)
    db.delete(goal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Simulation endpoints ──────────────────────────────────────────────────────

@router.post("/{goal_id}/simulate", response_model=SimulationResultOut)
def simulate(
    goal_id: str,
    payload: SimulationRequest,
    db: Session = Depends(get_db),
) -> SimulationResultOut:
    """Run a 3-scenario compound-growth simulation for a goal."""
    goal = _goal_or_404(goal_id, db)
    result = simulate_goal(
        goal_id=goal_id,
        current_amount=float(goal.current_amount),
        target_amount=float(goal.target_amount),
        monthly_contribution=float(goal.monthly_contribution or 0),
        target_date=goal.target_date,
        inflation_rate=payload.inflation_rate,
        max_months=payload.max_months,
    )
    return SimulationResultOut(
        goal_id=result.goal_id,
        current_amount=result.current_amount,
        target_amount=result.target_amount,
        monthly_contribution=result.monthly_contribution,
        inflation_rate=result.inflation_rate,
        inflation_adjusted_target=result.inflation_adjusted_target,
        monthly_data=[
            MonthlyDataPointOut(
                month=p.month, label=p.label,
                conservative=p.conservative, base=p.base, optimistic=p.optimistic,
            )
            for p in result.monthly_data
        ],
        scenarios=[
            ScenarioProjectionOut(
                scenario=s.scenario, label=s.label, color=s.color,
                annual_growth_rate=s.annual_growth_rate,
                months_to_target=s.months_to_target,
                projected_date=s.projected_date,
                achievable_by_target_date=s.achievable_by_target_date,
                final_amount=s.final_amount,
            )
            for s in result.scenarios
        ],
        target_date=result.target_date,
        generated_at=result.generated_at,
    )


@router.get("/{goal_id}/progress", response_model=GoalProgressOut)
def goal_progress(goal_id: str, db: Session = Depends(get_db)) -> GoalProgressOut:
    """Return progress percentage and base-scenario estimated completion."""
    goal = _goal_or_404(goal_id, db)
    current = float(goal.current_amount)
    target = float(goal.target_amount)
    progress_pct = min(100.0, current / max(target, 0.01) * 100)
    remaining = max(0.0, target - current)

    # Quick base-scenario projection
    result = simulate_goal(
        goal_id=goal_id,
        current_amount=current,
        target_amount=target,
        monthly_contribution=float(goal.monthly_contribution or 0),
        target_date=goal.target_date,
        inflation_rate=DEFAULT_INFLATION,
        max_months=360,
    )
    base = next((s for s in result.scenarios if s.scenario == "base"), None)
    return GoalProgressOut(
        goal_id=goal_id,
        progress_pct=round(progress_pct, 2),
        remaining=round(remaining, 2),
        on_track=base.achievable_by_target_date if base else None,
        base_months_to_target=base.months_to_target if base else None,
        base_projected_date=base.projected_date if base else None,
    )
