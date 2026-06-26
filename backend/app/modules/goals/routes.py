from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.goal import Goal
from app.modules.goals.schemas import GoalCreate, GoalOut, GoalUpdate

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
