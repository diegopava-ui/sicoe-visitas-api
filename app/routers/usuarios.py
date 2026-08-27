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

from datetime import date
#
from fastapi import File, Form, HTTPException, UploadFile

from app.schemas.usuario_certificado_arl import (
    UsuarioCertificadoArlListado,
    UsuarioCertificadoArlRespuesta,
)

from app.services.usuario_certificado_arl_service import (
    crear_certificado_arl,
    eliminar_certificado_arl,
    listar_certificados_arl,
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

def _validar_acceso_certificado(
    usuario_actual: Usuario,
    usuario_id: int,
) -> None:
    if (
        usuario_actual.rol != "ADMINISTRADOR"
        and usuario_actual.id != usuario_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No tiene permiso para gestionar el "
                "certificado ARL de este usuario."
            ),
        )


@router.post(
    "/{usuario_id}/certificado-arl",
    response_model=UsuarioCertificadoArlRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar certificado ARL de un usuario/asesor",
)
def subir_certificado_arl(
    usuario_id: int,
    archivo: UploadFile = File(...),
    fecha_vigencia: date | None = Form(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> UsuarioCertificadoArlRespuesta:
    _validar_acceso_certificado(
        usuario_actual=usuario_actual,
        usuario_id=usuario_id,
    )

    return crear_certificado_arl(
        db=db,
        usuario_id=usuario_id,
        archivo=archivo,
        fecha_vigencia=fecha_vigencia,
        usuario_actual_id=usuario_actual.id,
    )


@router.get(
    "/{usuario_id}/certificado-arl",
    response_model=UsuarioCertificadoArlListado,
    summary="Listar certificados ARL de un usuario/asesor",
)
def listar_certificado_arl_endpoint(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> UsuarioCertificadoArlListado:
    _validar_acceso_certificado(
        usuario_actual=usuario_actual,
        usuario_id=usuario_id,
    )

    resultados = listar_certificados_arl(
        db=db,
        usuario_id=usuario_id,
    )

    return UsuarioCertificadoArlListado(
        resultados=resultados,
        total=len(resultados),
    )


@router.delete(
    "/{usuario_id}/certificado-arl/{certificado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (soft-delete) un certificado ARL",
)
def eliminar_certificado_arl_endpoint(
    usuario_id: int,
    certificado_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> None:
    _validar_acceso_certificado(
        usuario_actual=usuario_actual,
        usuario_id=usuario_id,
    )

    eliminar_certificado_arl(
        db=db,
        usuario_id=usuario_id,
        certificado_id=certificado_id,
        usuario_actual_id=usuario_actual.id,
    )
