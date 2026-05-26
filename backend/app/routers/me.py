from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_patient
from app.models.assigned_session import AssignedSession
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.assigned_session import AssignedSessionResponse
from app.schemas.user import MeResponse
from app.schemas.workout import DashboardResponse
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    physio_name = None
    birth_date = None
    weight = None
    height = None
    if profile:
        birth_date = profile.birth_date
        weight = float(profile.weight) if profile.weight else None
        height = float(profile.height) if profile.height else None
        if profile.physio_id:
            physio = db.query(User).filter(User.id == profile.physio_id).first()
            if physio:
                physio_name = physio.name

    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        profile_image_url=current_user.profile_image_url,
        physio_name=physio_name,
        birth_date=birth_date,
        weight=weight,
        height=height,
        notifications_enabled=current_user.notifications_enabled,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user: User = Depends(require_patient), db: Session = Depends(get_db)):
    return get_dashboard(current_user, db)


@router.get("/today-session", response_model=AssignedSessionResponse | None)
def today_session(current_user: User = Depends(require_patient), db: Session = Depends(get_db)):
    today = date.today()
    session = (
        db.query(AssignedSession)
        .filter(
            AssignedSession.patient_id == current_user.id,
            AssignedSession.scheduled_date == today,
            AssignedSession.status.in_(["PENDING", "IN_PROGRESS"]),
        )
        .first()
    )
    if not session:
        # Fallback: most recent pending session
        session = (
            db.query(AssignedSession)
            .filter(
                AssignedSession.patient_id == current_user.id,
                AssignedSession.status.in_(["PENDING", "IN_PROGRESS"]),
            )
            .order_by(AssignedSession.scheduled_date)
            .first()
        )
    return session


@router.get("/calendar-sessions", response_model=list[AssignedSessionResponse])
def calendar_sessions(current_user: User = Depends(require_patient), db: Session = Depends(get_db)):
    sessions = (
        db.query(AssignedSession)
        .filter(AssignedSession.patient_id == current_user.id)
        .order_by(AssignedSession.scheduled_date.desc())
        .limit(20)
        .all()
    )
    return sessions
