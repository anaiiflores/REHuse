import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_physio
from app.models.exercise import Exercise, ExerciseImage
from app.models.user import User

router = APIRouter(prefix="/imagenes-entrenamiento", tags=["imagenes-entrenamiento"])


class ImagenCreate(BaseModel):
    id_ejercicio: str
    base64: str
    orden: int = 0


class ImagenUpdate(BaseModel):
    base64: str | None = None
    orden: int | None = None


class ImagenResponse(BaseModel):
    id: str
    id_ejercicio: str
    base64: str
    orden: int

    model_config = {"from_attributes": True}


def _to_response(img: ExerciseImage) -> ImagenResponse:
    return ImagenResponse(id=img.id, id_ejercicio=img.exercise_id, base64=img.url, orden=img.order_index)


@router.get("/ejercicios/portadas/", response_model=list[ImagenResponse])
def get_portadas(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exercises = db.query(Exercise).all()
    result = []
    for ex in exercises:
        first = (
            db.query(ExerciseImage)
            .filter(ExerciseImage.exercise_id == ex.id)
            .order_by(ExerciseImage.order_index)
            .first()
        )
        if first:
            result.append(_to_response(first))
    return result


@router.get("/ejercicio/{ejercicio_id}/order_num/{orden}", response_model=ImagenResponse)
def get_by_order(ejercicio_id: str, orden: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    img = (
        db.query(ExerciseImage)
        .filter(ExerciseImage.exercise_id == ejercicio_id, ExerciseImage.order_index == orden)
        .first()
    )
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return _to_response(img)


@router.get("/ejercicio/{ejercicio_id}", response_model=list[ImagenResponse])
def get_by_ejercicio(ejercicio_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    imgs = (
        db.query(ExerciseImage)
        .filter(ExerciseImage.exercise_id == ejercicio_id)
        .order_by(ExerciseImage.order_index)
        .all()
    )
    return [_to_response(i) for i in imgs]


@router.post("/", response_model=ImagenResponse, status_code=201)
def create_imagen(req: ImagenCreate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    img = ExerciseImage(
        id=str(uuid.uuid4()),
        exercise_id=req.id_ejercicio,
        url=req.base64,
        order_index=req.orden,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return _to_response(img)


@router.put("/{imagen_id}", response_model=ImagenResponse)
def update_imagen(imagen_id: str, req: ImagenUpdate, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    img = db.query(ExerciseImage).filter(ExerciseImage.id == imagen_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    if req.base64 is not None:
        img.url = req.base64
    if req.orden is not None:
        img.order_index = req.orden
    db.commit()
    db.refresh(img)
    return _to_response(img)


@router.delete("/{imagen_id}", status_code=204)
def delete_imagen(imagen_id: str, physio: User = Depends(require_physio), db: Session = Depends(get_db)):
    img = db.query(ExerciseImage).filter(ExerciseImage.id == imagen_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    db.delete(img)
    db.commit()
