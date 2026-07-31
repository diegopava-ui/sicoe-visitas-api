from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from datetime import date

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.visita import (
    EstadoVisita,
    TipoVisita,
    VisitaListado,
    VisitaCrear,
    VisitaRespuesta,
    VisitaActualizar,
)
from app.services.visita_service import (
    actualizar_visita,
    crear_visita,
    desactivar_visita,
    obtener_visita,
    obtener_visitas,
    reactivar_visita,
)

from app.services.visita_pdf_service import generar_pdf_visita


from app.services.visita_service import (
    actualizar_visita,
    crear_visita,
    desactivar_visita,
    obtener_visita,
    obtener_visitas,
    reactivar_visita,
)

from app.services.visita_pdf_service import generar_pdf_visita

router = APIRouter(
    prefix="/api/v1/visitas",
    tags=["Visitas"],
)


@router.get(
    "",
    response_model=VisitaListado,
)
def listar_visitas(
    buscar: str | None = Query(default=None),
    asesor_id: int | None = Query(default=None, gt=0),
    estado: EstadoVisita | None = Query(default=None),
    tipo_visita: TipoVisita | None = Query(default=None),
    servicio: str | None = Query(default=None),
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    activo: bool | None = Query(default=None),
    tercero_id: int | None = Query(default=None, gt=0),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaListado:
    asesor_id_consulta = asesor_id

    # Un asesor solo puede consultar sus propias visitas.
    if usuario_actual.rol == "ASESOR":
        asesor_id_consulta = usuario_actual.asesor_id
    return obtener_visitas(
         db=db,
        buscar=buscar,
        asesor_id=asesor_id_consulta,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=activo,
        pagina=pagina,
        limite=limite,
    )

@router.get(
    "/{visita_id}/pdf",
    response_class=Response,
    summary="Descargar informe PDF de una visita",
)
def descargar_pdf_visita(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> Response:
    """
    Genera y descarga el informe corporativo
    correspondiente a una visita.
    """

    visita = obtener_visita(
        db=db,
        visita_id=visita_id,
    )

    if (
        usuario_actual.rol == "ASESOR"
        and visita.asesor_id != usuario_actual.asesor_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No tiene permiso para descargar "
                "el informe de esta visita."
            ),
        )

    contenido_pdf = generar_pdf_visita(
        db=db,
        visita_id=visita_id,
    )

    codigo_visita = f"VIS-{visita.id:06d}"
    nombre_archivo = (
        f"Informe_Visita_{codigo_visita}.pdf"
    )

    return Response(
        content=contenido_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nombre_archivo}"'
            ),
            "Cache-Control": "no-store",
        },
    )

@router.get(
    "/{visita_id}/pdf",
    response_class=Response,
)
def descargar_pdf_visita(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> Response:
    """
    Genera y descarga el informe corporativo
    asociado con una visita.
    """

    visita = obtener_visita(
        db=db,
        visita_id=visita_id,
    )

    if (
        usuario_actual.rol == "ASESOR"
        and visita.asesor_id != usuario_actual.asesor_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No tiene permiso para descargar "
                "el informe de esta visita."
            ),
        )

    contenido_pdf = generar_pdf_visita(
        db=db,
        visita_id=visita_id,
    )

    codigo_visita = f"VIS-{visita_id:06d}"
    nombre_archivo = (
        f"Informe_Visita_{codigo_visita}.pdf"
    )

    return Response(
        content=contenido_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nombre_archivo}"'
            ),
            "Cache-Control": "no-store",
        },
    )

@router.get("/{visita_id}")
def obtener_visita_por_id(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaRespuesta:
    visita = obtener_visita(
        db=db,
        visita_id=visita_id,
    )

    if (
        usuario_actual.rol == "ASESOR"
        and visita.asesor_id != usuario_actual.asesor_id
    ):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para consultar esta visita",
        )

    return visita


@router.post(
    "",
    response_model=VisitaRespuesta,
    status_code=201,
)
def registrar_visita(
    datos: VisitaCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaRespuesta:
    if usuario_actual.rol == "ASESOR":
        if usuario_actual.asesor_id is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario asesor no tiene un asesor asociado",
            )

        datos = datos.model_copy(
            update={
                "asesor_id": usuario_actual.asesor_id,
            }
        )

    return crear_visita(
        db=db,
        datos=datos,
        usuario_actual_id=usuario_actual.id,
    )
@router.patch(
    "/{visita_id}",
    response_model=VisitaRespuesta,
)
def actualizar_visita_endpoint(
    visita_id: int,
    datos: VisitaActualizar,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaRespuesta:
    visita = obtener_visita(
        db=db,
        visita_id=visita_id,
    )

    if usuario_actual.rol == "ASESOR":
        if visita.asesor_id != usuario_actual.asesor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para actualizar esta visita",
            )

        # Un asesor no puede reasignar la visita a otro asesor.
        if (
            datos.asesor_id is not None
            and datos.asesor_id != usuario_actual.asesor_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede reasignar la visita a otro asesor",
            )

    return actualizar_visita(
        db=db,
        visita_id=visita_id,
        datos=datos,
        usuario_actual_id=usuario_actual.id,
    )


@router.delete(
    "/{visita_id}",
    response_model=VisitaRespuesta,
)
def desactivar_visita_endpoint(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
        )
    ),
) -> VisitaRespuesta:
    return desactivar_visita(
        db=db,
        visita_id=visita_id,
        usuario_actual_id=usuario_actual.id,
    )


@router.patch(
    "/{visita_id}/reactivar",
    response_model=VisitaRespuesta,
)
def reactivar_visita_endpoint(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
        )
    ),
) -> VisitaRespuesta:
    return reactivar_visita(
        db=db,
        visita_id=visita_id,
        usuario_actual_id=usuario_actual.id,
    )