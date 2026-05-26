import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_physio
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.exercise import CreateExerciseRequest, ExerciseResponse, UpdateExerciseRequest

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseResponse])
def list_exercises(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Exercise).order_by(Exercise.name).all()


@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(exercise_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return ex


@router.post("", response_model=ExerciseResponse, status_code=201)
def create_exercise(req: CreateExerciseRequest, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = Exercise(id=str(uuid.uuid4()), created_by=physio.id, **req.model_dump())
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


@router.put("/{exercise_id}", response_model=ExerciseResponse)
def update_exercise(exercise_id: str, req: UpdateExerciseRequest, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(ex, field, value)
    db.commit()
    db.refresh(ex)
    return ex


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    db.delete(ex)
    db.commit()
