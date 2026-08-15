from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioPasswordRestablecer,
    UsuarioRespuesta,
)
from app.services.usuario_service import (
    actualizar_usuario,
    crear_usuario,
    desactivar_usuario,
    obtener_usuario,
    obtener_usuarios,
    reactivar_usuario,
    restablecer_password_usuario,
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
    limite: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
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
    return crear_usuario(
        db,
        datos,
    )


@router.patch(
    "/{usuario_id}/password",
    response_model=UsuarioRespuesta,
    summary=(
        "Restablecer contraseña de usuario "
        "como administrador"
    ),
)
def restablecer_password_usuario_endpoint(
    usuario_id: int,
    datos: UsuarioPasswordRestablecer,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return restablecer_password_usuario(
        db=db,
        usuario_id=usuario_id,
        datos=datos,
        usuario_actual_id=usuario_actual.id,
    )


@router.patch(
    "/{usuario_id}/reactivar",
    response_model=UsuarioRespuesta,
)
def reactivar_usuario_endpoint(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return reactivar_usuario(
        db=db,
        usuario_id=usuario_id,
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioRespuesta,
)
def obtener_usuario_por_id(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return obtener_usuario(
        db,
        usuario_id,
    )


@router.put(
    "/{usuario_id}",
    response_model=UsuarioRespuesta,
)
def actualizar_usuario_endpoint(
    usuario_id: int,
    datos: UsuarioActualizar,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return actualizar_usuario(
        db,
        usuario_id,
        datos,
    )


@router.delete(
    "/{usuario_id}",
    response_model=UsuarioRespuesta,
)
def desactivar_usuario_endpoint(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles("ADMINISTRADOR")
    ),
) -> UsuarioRespuesta:
    return desactivar_usuario(
        db=db,
        usuario_id=usuario_id,
        usuario_actual_id=usuario_actual.id,
    )
