import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_physio
from app.core.security import hash_password
from app.models.assigned_session import AssignedSession
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.assigned_session import AssignedSessionResponse
from app.schemas.user import CreatePatientRequest, PatientResponse

router = APIRouter(prefix="/patients", tags=["patients"])


def _patient_to_response(user: User, profile: PatientProfile | None) -> PatientResponse:
    physio_name = None
    if profile and profile.physio_id:
        physio = profile.physio
        if physio:
            physio_name = physio.name

    profile_data = None
    if profile:
        from app.schemas.user import PatientProfileResponse
        profile_data = PatientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            physio_id=profile.physio_id,
            physio_name=physio_name,
            dni=profile.dni,
            birth_date=profile.birth_date,
            weight=float(profile.weight) if profile.weight else None,
            height=float(profile.height) if profile.height else None,
            notes=profile.notes,
        )

    return PatientResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        profile_image_url=user.profile_image_url,
        profile=profile_data,
    )


@router.get("", response_model=list[PatientResponse])
def list_patients(physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    profiles = (
        db.query(PatientProfile)
        .filter(PatientProfile.physio_id == physio.id)
        .all()
    )
    result = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            result.append(_patient_to_response(user, p))
    return result


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(req: CreatePatientRequest, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        password_hash=hash_password(req.password),
        role="patient",
        name=req.name,
    )
    db.add(user)
    db.flush()

    profile = PatientProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        physio_id=physio.id,
        dni=req.dni,
        birth_date=req.birth_date,
        weight=req.weight,
        height=req.height,
        notes=req.notes,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return _patient_to_response(user, profile)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not user:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_id).first()
    return _patient_to_response(user, profile)


@router.get("/{patient_id}/assigned-sessions", response_model=list[AssignedSessionResponse])
def patient_sessions(patient_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    sessions = (
        db.query(AssignedSession)
        .filter(
            AssignedSession.patient_id == patient_id,
            AssignedSession.physio_id == physio.id,
        )
        .order_by(AssignedSession.scheduled_date.desc())
        .all()
    )
    return sessions
