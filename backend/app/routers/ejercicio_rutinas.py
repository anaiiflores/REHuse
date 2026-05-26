import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_physio
from app.models.assigned_session import AssignedSessionExercise
from app.models.user import User

router = APIRouter(prefix="/ejercicios-rutinas", tags=["ejercicios-rutinas"])


class EjercicioRutinaResponse(BaseModel):
    id_rutina: str
    id_ejercicio: str
    orden: int
    series: int | None
    repeticiones: int | None

    model_config = {"from_attributes": True}


class EjercicioRutinaCreate(BaseModel):
    id_rutina: str
    id_ejercicio: str
    orden: int = 0
    series: int | None = None
    repeticiones: int | None = None


def _to_response(ase: AssignedSessionExercise) -> EjercicioRutinaResponse:
    return EjercicioRutinaResponse(
        id_rutina=ase.assigned_session_id,
        id_ejercicio=ase.exercise_id,
        orden=ase.order_index,
        series=ase.series,
        repeticiones=ase.reps,
    )


@router.get("/{id_rutina}", response_model=list[EjercicioRutinaResponse])
def get_ejercicios_rutina(
    id_rutina: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(AssignedSessionExercise)
        .filter(AssignedSessionExercise.assigned_session_id == id_rutina)
        .order_by(AssignedSessionExercise.order_index)
        .all()
    )
    return [_to_response(i) for i in items]


@router.post("/", response_model=EjercicioRutinaResponse, status_code=201)
def add_ejercicio_rutina(
    req: EjercicioRutinaCreate,
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    item = AssignedSessionExercise(
        id=str(uuid.uuid4()),
        assigned_session_id=req.id_rutina,
        exercise_id=req.id_ejercicio,
        order_index=req.orden,
        series=req.series,
        reps=req.repeticiones,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.delete("/{id_rutina}/{id_ejercicio}", status_code=204)
def remove_ejercicio_rutina(
    id_rutina: str,
    id_ejercicio: str,
    physio: User = Depends(require_physio),
    db: Session = Depends(get_db),
):
    item = (
        db.query(AssignedSessionExercise)
        .filter(
            AssignedSessionExercise.assigned_session_id == id_rutina,
            AssignedSessionExercise.exercise_id == id_ejercicio,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    db.delete(item)
    db.commit()
