import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_physio
from app.core.security import hash_password
from app.models.assigned_session import AssignedSession
from app.models.patient_profile import PatientProfile
from app.models.user import User

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


# ── Schemas ────────────────────────────────────────────────────────────────

class PacienteResponse(BaseModel):
    id: str
    nombre: str
    apellidos: str
    correo: str | None
    telefono: str | None
    dni: str | None
    fecha_nacimiento: str | None
    notas: str | None
    historia_clinica: str | None

    model_config = {"from_attributes": True}


class PacienteCreate(BaseModel):
    nombre: str
    apellidos: str = ""
    correo: str
    contrasena: str = "1234"
    telefono: str | None = None
    dni: str | None = None
    fecha_nacimiento: str | None = None
    notas: str | None = None
    historia_clinica: str | None = None


class PacienteUpdate(BaseModel):
    nombre: str | None = None
    apellidos: str | None = None
    correo: str | None = None
    telefono: str | None = None
    dni: str | None = None
    fecha_nacimiento: str | None = None
    notas: str | None = None
    historia_clinica: str | None = None


class PacienteConRutinas(PacienteResponse):
    num_rutinas: int = 0


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_response(user: User, profile: PatientProfile | None) -> PacienteResponse:
    name_parts = (user.name or "").split(" ", 1)
    nombre = name_parts[0]
    apellidos = name_parts[1] if len(name_parts) > 1 else ""
    return PacienteResponse(
        id=user.id,
        nombre=nombre,
        apellidos=apellidos,
        correo=user.email,
        telefono=user.phone,
        dni=profile.dni if profile else None,
        fecha_nacimiento=str(profile.birth_date) if profile and profile.birth_date else None,
        notas=profile.notes if profile else None,
        historia_clinica=None,
    )


def _get_my_patients(physio: User, db: Session):
    # Return all patients — physios in this clinic share all patients
    profiles = db.query(PatientProfile).all()
    result = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            result.append((user, p))
    return result


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/filtrar_pacientes/con_rutinas", response_model=list[PacienteConRutinas])
def filtrar_con_rutinas(
    nombre: str | None = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    pairs = _get_my_patients(physio, db)
    result = []
    for user, profile in pairs:
        if nombre and nombre.lower() not in user.name.lower():
            continue
        count = db.query(AssignedSession).filter(AssignedSession.patient_id == user.id).count()
        resp = _to_response(user, profile)
        result.append(PacienteConRutinas(**resp.model_dump(), num_rutinas=count))
    return result[skip: skip + limit]


@router.get("/filtrar_pacientes", response_model=list[PacienteResponse])
def filtrar_pacientes(
    nombre: str | None = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    pairs = _get_my_patients(physio, db)
    result = [_to_response(u, p) for u, p in pairs if not nombre or nombre.lower() in u.name.lower()]
    return result[skip: skip + limit]


@router.get("", response_model=list[PacienteResponse])
def list_pacientes(physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    return [_to_response(u, p) for u, p in _get_my_patients(physio, db)]


@router.post("", response_model=PacienteResponse, status_code=201)
def create_paciente(req: PacienteCreate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.correo).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    full_name = f"{req.nombre} {req.apellidos}".strip()
    user = User(
        id=str(uuid.uuid4()),
        email=req.correo,
        password_hash=hash_password(req.contrasena),
        role="patient",
        name=full_name,
        phone=req.telefono,
    )
    db.add(user)
    db.flush()

    from datetime import date as date_type
    birth = None
    if req.fecha_nacimiento:
        try:
            birth = date_type.fromisoformat(req.fecha_nacimiento)
        except ValueError:
            pass

    profile = PatientProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        physio_id=physio.id,
        dni=req.dni,
        birth_date=birth,
        notes=req.notas,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return _to_response(user, profile)


@router.get("/{paciente_id}", response_model=PacienteResponse)
def get_paciente(paciente_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == paciente_id, User.role == "patient").first()
    if not user:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == paciente_id).first()
    return _to_response(user, profile)


@router.put("/{paciente_id}", response_model=PacienteResponse)
def update_paciente(paciente_id: str, req: PacienteUpdate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == paciente_id, User.role == "patient").first()
    if not user:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if req.nombre is not None or req.apellidos is not None:
        nombre = req.nombre if req.nombre is not None else user.name.split(" ", 1)[0]
        apellidos = req.apellidos if req.apellidos is not None else (user.name.split(" ", 1)[1] if " " in user.name else "")
        user.name = f"{nombre} {apellidos}".strip()
    if req.correo is not None:
        user.email = req.correo
    if req.telefono is not None:
        user.phone = req.telefono

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == paciente_id).first()
    if profile:
        if req.dni is not None:
            profile.dni = req.dni
        if req.notas is not None:
            profile.notes = req.notas
        if req.fecha_nacimiento is not None:
            from datetime import date as date_type
            try:
                profile.birth_date = date_type.fromisoformat(req.fecha_nacimiento)
            except ValueError:
                pass

    db.commit()
    db.refresh(user)
    return _to_response(user, profile)


@router.delete("/{paciente_id}", status_code=204)
def delete_paciente(paciente_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == paciente_id, User.role == "patient").first()
    if not user:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    db.delete(user)
    db.commit()
