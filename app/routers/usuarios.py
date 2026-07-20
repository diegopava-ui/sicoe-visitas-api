from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCrear, UsuarioRespuesta

from app.services.usuario_service import crear_usuario, obtener_usuarios

from fastapi import APIRouter, Depends, Query, status

from app.services.usuario_service import (
    crear_usuario,
    obtener_usuarios,
    obtener_usuario,
    actualizar_usuario,
)

from app.schemas.usuario import (
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
)

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)

@router.get(
    "",
    response_model=list[UsuarioRespuesta],
)
def listar_usuarios(
    buscar: str | None = None,
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> list[UsuarioRespuesta]:
    return obtener_usuarios(
        db=db,
        buscar=buscar,
        limite=limite,
        offset=offset,
    )

@router.get(
    "/{usuario_id}",
    response_model=UsuarioRespuesta,
)

@router.put(
    "/{usuario_id}",
    response_model=UsuarioRespuesta,
)
def actualizar_usuario_endpoint(
    usuario_id: int,
    datos: UsuarioActualizar,
    db: Session = Depends(get_db),
    usuario_actual=Depends(
        require_roles(
            "ADMINISTRADOR",
        )
    ),
):
    return actualizar_usuario(
        db,
        usuario_id,
        datos,
    )

def obtener_usuario_por_id(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(
        require_roles(
            "ADMINISTRADOR",
            "SUPERVISOR",
        )
    ),
):
    return obtener_usuario(
        db,
        usuario_id,
    )

@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return crear_usuario(db, datos)