from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user, require_physio
from app.models.user import User

router = APIRouter(prefix="/etiquetas", tags=["etiquetas"])


class EtiquetaResponse(BaseModel):
    id: str
    nombre: str
    id_categoria: str


@router.get("", response_model=list[EtiquetaResponse])
def list_etiquetas(current_user: User = Depends(get_current_user)):
    return []


@router.get("/{etiqueta_id}", response_model=EtiquetaResponse)
def get_etiqueta(etiqueta_id: str, current_user: User = Depends(get_current_user)):
    return EtiquetaResponse(id=etiqueta_id, nombre="", id_categoria="")


@router.post("", response_model=EtiquetaResponse, status_code=201)
def create_etiqueta(physio: User = Depends(require_physio)):
    return EtiquetaResponse(id="stub", nombre="", id_categoria="")


@router.put("/{etiqueta_id}", response_model=EtiquetaResponse)
def update_etiqueta(etiqueta_id: str, physio: User = Depends(require_physio)):
    return EtiquetaResponse(id=etiqueta_id, nombre="", id_categoria="")


@router.delete("/{etiqueta_id}", status_code=204)
def delete_etiqueta(etiqueta_id: str, physio: User = Depends(require_physio)):
    return
