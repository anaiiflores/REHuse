from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user, require_physio
from app.models.user import User

router = APIRouter(prefix="/plantillas", tags=["plantillas"])


class PlantillaResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str
    series_por_defecto: int
    repeticiones_por_defecto: int


@router.get("", response_model=list[PlantillaResponse])
def list_plantillas(current_user: User = Depends(get_current_user)):
    return []


@router.get("/filtrar_plantillas/", response_model=list[PlantillaResponse])
def filtrar_plantillas(current_user: User = Depends(get_current_user)):
    return []


@router.get("/{plantilla_id}", response_model=PlantillaResponse)
def get_plantilla(plantilla_id: str, current_user: User = Depends(get_current_user)):
    return PlantillaResponse(id=plantilla_id, nombre="", descripcion="", series_por_defecto=3, repeticiones_por_defecto=10)


@router.post("", response_model=PlantillaResponse, status_code=201)
def create_plantilla(physio: User = Depends(require_physio)):
    return PlantillaResponse(id="stub", nombre="", descripcion="", series_por_defecto=3, repeticiones_por_defecto=10)


@router.put("/{plantilla_id}", response_model=PlantillaResponse)
def update_plantilla(plantilla_id: str, physio: User = Depends(require_physio)):
    return PlantillaResponse(id=plantilla_id, nombre="", descripcion="", series_por_defecto=3, repeticiones_por_defecto=10)


@router.delete("/{plantilla_id}", status_code=204)
def delete_plantilla(plantilla_id: str, physio: User = Depends(require_physio)):
    return
