from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.calendario import CalendarioEvento
from app.schemas.visita import EstadoVisita, TipoVisita
from app.services.calendario_service import listar_eventos


router = APIRouter(
    prefix="/api/v1/calendario",
    tags=["Agenda Inteligente"],
)


@router.get(
    "/eventos",
    response_model=list[CalendarioEvento],
    summary="Consultar eventos de la Agenda Inteligente",
)
def obtener_eventos_calendario(
    desde: date = Query(
        ...,
        description="Fecha inicial del período",
    ),
    hasta: date = Query(
        ...,
        description="Fecha final del período",
    ),
    asesor_id: int | None = Query(
        default=None,
        gt=0,
    ),
    tercero_id: int | None = Query(
        default=None,
        gt=0,
    ),
    estado: EstadoVisita | None = Query(
        default=None,
    ),
    tipo_visita: TipoVisita | None = Query(
        default=None,
    ),
    servicio: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> list[CalendarioEvento]:

    if hasta < desde:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La fecha final no puede ser "
                "anterior a la fecha inicial."
            ),
        )

    asesor_id_consulta = asesor_id

    # El asesor únicamente puede consultar
    # su propia agenda.
    if usuario_actual.rol == "ASESOR":
        if usuario_actual.asesor_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El usuario asesor no tiene "
                    "un asesor asociado."
                ),
            )

        asesor_id_consulta = usuario_actual.asesor_id

    return listar_eventos(
        db=db,
        desde=desde,
        hasta=hasta,
        asesor_id=asesor_id_consulta,
        tercero_id=tercero_id,
        estado=estado.value if estado else None,
        tipo_visita=(
            tipo_visita.value
            if tipo_visita
            else None
        ),
        servicio=servicio,
    )