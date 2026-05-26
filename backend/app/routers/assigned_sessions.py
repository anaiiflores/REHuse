import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_physio, require_patient
from app.models.assigned_session import AssignedSession, AssignedSessionExercise
from app.models.exercise import Exercise
from app.models.notification import Notification
from app.models.user import User
from app.schemas.assigned_session import AssignedSessionResponse, CreateAssignedSessionRequest

router = APIRouter(tags=["assigned-sessions"])


@router.post("/patients/{patient_id}/assigned-sessions", response_model=AssignedSessionResponse, status_code=201)
def assign_session(
    patient_id: str,
    req: CreateAssignedSessionRequest,
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    session = AssignedSession(
        id=str(uuid.uuid4()),
        physio_id=physio.id,
        patient_id=patient_id,
        title=req.title,
        scheduled_date=req.scheduled_date,
        scheduled_time=req.scheduled_time,
        notes=req.notes,
        difficulty=req.difficulty,
        status="PENDING",
        seen_by_patient=False,
    )
    db.add(session)
    db.flush()

    for ex_in in req.exercises:
        exercise = db.query(Exercise).filter(Exercise.id == ex_in.exercise_id).first()
        if not exercise:
            raise HTTPException(status_code=404, detail=f"Ejercicio {ex_in.exercise_id} no encontrado")
        db.add(AssignedSessionExercise(
            id=str(uuid.uuid4()),
            assigned_session_id=session.id,
            exercise_id=ex_in.exercise_id,
            order_index=ex_in.order_index,
            series=ex_in.series,
            reps=ex_in.reps,
            rest_seconds=ex_in.rest_seconds,
            duration_seconds=ex_in.duration_seconds,
            notes=ex_in.notes,
        ))

    # Notify patient
    db.add(Notification(
        id=str(uuid.uuid4()),
        user_id=patient_id,
        type="newAssignment",
        title="Nueva sesión asignada",
        body=f"{physio.name} te ha asignado: {req.title}",
        is_read=False,
        has_action=True,
        action_label="Ver sesión",
    ))

    db.commit()
    db.refresh(session)
    return session


@router.get("/assigned-sessions/{session_id}", response_model=AssignedSessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(AssignedSession).filter(AssignedSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Patient can only see their own sessions; physio can see their assigned sessions
    if current_user.role == "patient" and session.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if current_user.role == "physio" and session.physio_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # Mark as seen when patient opens it
    if current_user.role == "patient" and not session.seen_by_patient:
        session.seen_by_patient = True
        db.commit()
        db.refresh(session)

    return session


@router.post("/assigned-sessions/{session_id}/start", response_model=AssignedSessionResponse)
def start_session(
    session_id: str,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == session_id,
        AssignedSession.patient_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    session.status = "IN_PROGRESS"
    session.seen_by_patient = True
    db.commit()
    db.refresh(session)
    return session


@router.patch("/assigned-sessions/{session_id}/complete", response_model=AssignedSessionResponse)
def complete_session(
    session_id: str,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == session_id,
        AssignedSession.patient_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    session.status = "COMPLETED"
    db.commit()
    db.refresh(session)
    return session
