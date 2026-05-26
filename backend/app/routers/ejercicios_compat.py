import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_physio
from app.models.exercise import Exercise
from app.models.user import User

router = APIRouter(prefix="/ejercicios", tags=["ejercicios"])


# ── Schemas ────────────────────────────────────────────────────────────────

class EjercicioResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str | None
    repeticiones: int | None
    tiempo_mantenimiento: int | None

    model_config = {"from_attributes": True}


class EjercicioCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    repeticiones: int | None = None
    tiempo_mantenimiento: int | None = None


class EjercicioUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    repeticiones: int | None = None
    tiempo_mantenimiento: int | None = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_response(ex: Exercise) -> EjercicioResponse:
    return EjercicioResponse(
        id=ex.id,
        nombre=ex.name,
        descripcion=ex.description,
        repeticiones=ex.reps,
        tiempo_mantenimiento=ex.total_duration_seconds,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/filtrar_ejercicios", response_model=list[EjercicioResponse])
def filtrar_ejercicios(
    nombre: str | None = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Exercise)
    if nombre:
        q = q.filter(Exercise.name.ilike(f"%{nombre}%"))
    exercises = q.order_by(Exercise.name).offset(skip).limit(limit).all()
    return [_to_response(ex) for ex in exercises]


@router.get("", response_model=list[EjercicioResponse])
def list_ejercicios(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_to_response(ex) for ex in db.query(Exercise).order_by(Exercise.name).all()]


@router.get("/{ejercicio_id}", response_model=EjercicioResponse)
def get_ejercicio(ejercicio_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ejercicio_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return _to_response(ex)


@router.post("", response_model=EjercicioResponse, status_code=201)
def create_ejercicio(req: EjercicioCreate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = Exercise(
        id=str(uuid.uuid4()),
        name=req.nombre,
        description=req.descripcion,
        reps=req.repeticiones,
        total_duration_seconds=req.tiempo_mantenimiento,
        created_by=physio.id,
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return _to_response(ex)


@router.put("/{ejercicio_id}", response_model=EjercicioResponse)
def update_ejercicio(ejercicio_id: str, req: EjercicioUpdate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ejercicio_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    if req.nombre is not None:
        ex.name = req.nombre
    if req.descripcion is not None:
        ex.description = req.descripcion
    if req.repeticiones is not None:
        ex.reps = req.repeticiones
    if req.tiempo_mantenimiento is not None:
        ex.total_duration_seconds = req.tiempo_mantenimiento
    db.commit()
    db.refresh(ex)
    return _to_response(ex)


@router.delete("/{ejercicio_id}", status_code=204)
def delete_ejercicio(ejercicio_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ejercicio_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    db.delete(ex)
    db.commit()
