import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_physio
from app.models.assigned_session import AssignedSession
from app.models.user import User

router = APIRouter(prefix="/rutinas", tags=["rutinas"])


class RutinaResponse(BaseModel):
    id: str
    id_paciente: str
    nombre: str
    descripcion: str | None
    fecha_inicio: str | None
    fecha_fin: str | None
    series_por_defecto: int | None
    repeticiones_por_defecto: int | None
    notas: str | None
    id_usuario: str | None
    nombre_usuario: str | None

    model_config = {"from_attributes": True}


class RutinaCreate(BaseModel):
    id_paciente: str
    nombre: str
    descripcion: str | None = None
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    series_por_defecto: int | None = None
    repeticiones_por_defecto: int | None = None
    notas: str | None = None


class RutinaUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    series_por_defecto: int | None = None
    repeticiones_por_defecto: int | None = None
    notas: str | None = None


def _to_response(session: AssignedSession, physio: User) -> RutinaResponse:
    return RutinaResponse(
        id=session.id,
        id_paciente=session.patient_id,
        nombre=session.title,
        descripcion=session.notes,
        fecha_inicio=str(session.scheduled_date) if session.scheduled_date else None,
        fecha_fin=None,
        series_por_defecto=None,
        repeticiones_por_defecto=None,
        notas=session.notes,
        id_usuario=physio.id,
        nombre_usuario=physio.name,
    )


@router.get("/filtrar_rutinas", response_model=list[RutinaResponse])
def filtrar_rutinas(
    nombre: str | None = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    q = db.query(AssignedSession).filter(AssignedSession.physio_id == physio.id)
    if nombre:
        q = q.filter(AssignedSession.title.ilike(f"%{nombre}%"))
    sessions = q.order_by(AssignedSession.created_at.desc()).offset(skip).limit(limit).all()
    return [_to_response(s, physio) for s in sessions]


@router.get("/by-id/{rutina_id}", response_model=RutinaResponse)
def get_rutina_by_id(rutina_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == rutina_id,
        AssignedSession.physio_id == physio.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    return _to_response(session, physio)


@router.get("", response_model=list[RutinaResponse])
def list_rutinas(physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    sessions = (
        db.query(AssignedSession)
        .filter(AssignedSession.physio_id == physio.id)
        .order_by(AssignedSession.created_at.desc())
        .all()
    )
    return [_to_response(s, physio) for s in sessions]


@router.post("", response_model=RutinaResponse, status_code=201)
def create_rutina(req: RutinaCreate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    from datetime import date as date_type
    scheduled_date = None
    if req.fecha_inicio:
        try:
            scheduled_date = date_type.fromisoformat(req.fecha_inicio)
        except ValueError:
            pass

    session = AssignedSession(
        id=str(uuid.uuid4()),
        physio_id=physio.id,
        patient_id=req.id_paciente,
        title=req.nombre,
        notes=req.notas or req.descripcion,
        scheduled_date=scheduled_date,
        difficulty="MEDIA",
        status="PENDING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_response(session, physio)


@router.put("/{rutina_id}", response_model=RutinaResponse)
def update_rutina(rutina_id: str, req: RutinaUpdate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == rutina_id,
        AssignedSession.physio_id == physio.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    if req.nombre is not None:
        session.title = req.nombre
    if req.notas is not None:
        session.notes = req.notas
    if req.fecha_inicio is not None:
        from datetime import date as date_type
        try:
            session.scheduled_date = date_type.fromisoformat(req.fecha_inicio)
        except ValueError:
            pass
    db.commit()
    db.refresh(session)
    return _to_response(session, physio)


@router.delete("/{rutina_id}", status_code=204)
def delete_rutina(rutina_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    session = db.query(AssignedSession).filter(
        AssignedSession.id == rutina_id,
        AssignedSession.physio_id == physio.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    db.delete(session)
    db.commit()
