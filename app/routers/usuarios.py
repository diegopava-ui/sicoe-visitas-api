from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.usuario import UsuarioCrear, UsuarioRespuesta
from app.services.usuario_service import crear_usuario

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(get_db),
) -> UsuarioRespuesta:
    return crear_usuario(db, datos)