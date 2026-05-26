import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_patient
from app.models.assigned_session import AssignedSession
from app.models.exercise import Exercise
from app.models.user import User
from app.models.workout import ExerciseLog, WorkoutLog
from app.schemas.workout import (
    CompleteExerciseRequest,
    CompleteWorkoutRequest,
    StartWorkoutRequest,
    WorkoutLogResponse,
)

router = APIRouter(prefix="/workout-sessions", tags=["workout"])


@router.post("", response_model=WorkoutLogResponse, status_code=201)
def start_workout(
    req: StartWorkoutRequest,
    patient: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == req.assigned_session_id,
        AssignedSession.patient_id == patient.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión asignada no encontrada")

    log = WorkoutLog(
        id=str(uuid.uuid4()),
        assigned_session_id=req.assigned_session_id,
        patient_id=patient.id,
        started_at=datetime.now(timezone.utc),
        status="in_progress",
    )
    db.add(log)
    session.status = "IN_PROGRESS"
    db.commit()
    db.refresh(log)
    return log


@router.get("/{workout_id}", response_model=WorkoutLogResponse)
def get_workout(workout_id: str, patient: User = Depends(require_patient), db: Session = Depends(get_db)):
    log = db.query(WorkoutLog).filter(WorkoutLog.id == workout_id, WorkoutLog.patient_id == patient.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Workout no encontrado")
    return log


@router.patch("/{workout_id}/exercises/{exercise_id}/complete", response_model=WorkoutLogResponse)
def complete_exercise(
    workout_id: str,
    exercise_id: str,
    req: CompleteExerciseRequest,
    patient: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    log = db.query(WorkoutLog).filter(WorkoutLog.id == workout_id, WorkoutLog.patient_id == patient.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Workout no encontrado")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    ex_log = db.query(ExerciseLog).filter(
        ExerciseLog.workout_log_id == workout_id,
        ExerciseLog.exercise_id == exercise_id,
    ).first()

    now = datetime.now(timezone.utc)
    if ex_log:
        ex_log.completed_at = req.completed_at or now
        ex_log.skipped = req.skipped
        ex_log.skip_reason = req.skip_reason
    else:
        db.add(ExerciseLog(
            id=str(uuid.uuid4()),
            workout_log_id=workout_id,
            exercise_id=exercise_id,
            started_at=req.started_at or now,
            completed_at=req.completed_at or now,
            skipped=req.skipped,
            skip_reason=req.skip_reason,
        ))

    db.commit()
    db.refresh(log)
    return log


@router.patch("/{workout_id}/complete", response_model=WorkoutLogResponse)
def complete_workout(
    workout_id: str,
    req: CompleteWorkoutRequest,
    patient: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    log = db.query(WorkoutLog).filter(WorkoutLog.id == workout_id, WorkoutLog.patient_id == patient.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Workout no encontrado")

    now = datetime.now(timezone.utc)
    log.status = req.status
    log.completed_at = req.completed_at or now

    if req.status == "completed":
        session = db.query(AssignedSession).filter(AssignedSession.id == log.assigned_session_id).first()
        if session:
            session.status = "COMPLETED"

    db.commit()
    db.refresh(log)
    return log
