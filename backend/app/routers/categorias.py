from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user, require_physio
from app.models.user import User

router = APIRouter(prefix="/categorias", tags=["categorias"])


class CategoriaResponse(BaseModel):
    id: str
    nombre: str
    color: str


@router.get("", response_model=list[CategoriaResponse])
def list_categorias(current_user: User = Depends(get_current_user)):
    return []


@router.get("/{categoria_id}", response_model=CategoriaResponse)
def get_categoria(categoria_id: str, current_user: User = Depends(get_current_user)):
    return CategoriaResponse(id=categoria_id, nombre="", color="#000000")


@router.post("", response_model=CategoriaResponse, status_code=201)
def create_categoria(physio: User = Depends(require_physio)):
    return CategoriaResponse(id="stub", nombre="", color="#000000")


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria(categoria_id: str, physio: User = Depends(require_physio)):
    return CategoriaResponse(id=categoria_id, nombre="", color="#000000")


@router.delete("/{categoria_id}", status_code=204)
def delete_categoria(categoria_id: str, physio: User = Depends(require_physio)):
    return
