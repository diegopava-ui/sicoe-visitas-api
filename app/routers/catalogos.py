from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.catalogo import (
    DepartamentoRespuesta,
    MunicipioRespuesta,
)
from app.services.catalogo_service import (
    listar_departamentos,
    listar_municipios,
)


router = APIRouter(
    prefix="/api/v1/catalogos",
    tags=["Catálogos"],
)


@router.get(
    "/departamentos",
    response_model=list[DepartamentoRespuesta],
    summary="Listar departamentos de Colombia (DIVIPOLA)",
)
def obtener_departamentos(
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> list[DepartamentoRespuesta]:
    return listar_departamentos()


@router.get(
    "/municipios",
    response_model=list[MunicipioRespuesta],
    summary="Listar municipios de Colombia (DIVIPOLA), opcionalmente filtrados por departamento",
)
def obtener_municipios(
    departamento_codigo: str | None = Query(
        default=None,
        description="Código DANE del departamento (ej. '76' para Valle del Cauca)",
    ),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> list[MunicipioRespuesta]:
    return listar_municipios(
        departamento_codigo=departamento_codigo,
    )
