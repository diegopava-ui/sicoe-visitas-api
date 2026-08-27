from fastapi import (
    APIRouter,
    Body,
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
from app.schemas.ubicacion import (
    UbicacionValidacionRespuesta,
    UbicacionValidar,
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
from app.services.visita_asistencia_pdf_service import generar_pdf_asistencia
from app.services.ubicacion_service import validar_ubicacion_visita

from fastapi import File, Form, UploadFile

from app.schemas.visita_evidencia import (
VisitaEvidenciaListado,
 VisitaEvidenciaRespuesta,
 )

from app.services.visita_evidencia_service import (
    crear_evidencia,
    eliminar_evidencia,
    listar_evidencias,
 )

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
    "/{visita_id}/asistencia-pdf",
    response_class=Response,
    summary="Descargar formato PDF de asistencia",
)
def descargar_pdf_asistencia(
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
    Genera un formato imprimible de asistencia
    asociado a una visita.

    Un usuario ASESOR solo puede descargar el
    formato de sus propias visitas.
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
                "la asistencia de esta visita."
            ),
        )

    contenido_pdf = generar_pdf_asistencia(
        db=db,
        visita_id=visita_id,
    )

    codigo_visita = f"VIS-{visita.id:06d}"
    nombre_archivo = (
        f"Formato_Asistencia_{codigo_visita}.pdf"
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


@router.patch(
    "/{visita_id}/ubicacion/validar",
    response_model=UbicacionValidacionRespuesta,
    summary="Validar ubicación de una visita",
)
def validar_ubicacion_visita_endpoint(
    visita_id: int,
    datos: UbicacionValidar = Body(
        ...,
        openapi_examples={
            "validar_coordenadas_existentes": {
                "summary": "Validar coordenadas existentes",
                "description": (
                    "Confirma las coordenadas ya guardadas "
                    "sin reemplazar latitud ni longitud."
                ),
                "value": {
                    "fuente_ubicacion": "MANUAL",
                },
            },
        },
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> UbicacionValidacionRespuesta:
    """
    Confirma la ubicación de una visita y registra
    de forma auditable la fuente, fecha y usuario
    que realizó la validación.

    Si el usuario es ASESOR, solo puede validar
    visitas asignadas a su propio asesor.
    """

    return validar_ubicacion_visita(
        db=db,
        visita_id=visita_id,
        datos=datos,
        usuario_actual=usuario_actual,
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

@router.post(
    "/{visita_id}/evidencias",
    response_model=VisitaEvidenciaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar acta/asistencia u otra evidencia a una visita",
)
def subir_evidencia_visita(
    visita_id: int,
    archivo: UploadFile = File(...),
    tipo_archivo: str = Form(default="PDF"),
    descripcion: str | None = Form(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaEvidenciaRespuesta:
    """
    Sube un archivo (acta firmada, formato de
    asistencia firmado, u otra evidencia) y lo
    asocia a la visita.

    Un usuario ASESOR solo puede adjuntar
    archivos a sus propias visitas.
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
                "No tiene permiso para adjuntar "
                "archivos a esta visita."
            ),
        )

    return crear_evidencia(
        db=db,
        visita_id=visita_id,
        archivo=archivo,
        tipo_archivo=tipo_archivo,
        descripcion=descripcion,
        usuario_actual_id=usuario_actual.id,
    )


@router.get(
    "/{visita_id}/evidencias",
    response_model=VisitaEvidenciaListado,
    summary="Listar adjuntos/evidencias de una visita",
)
def listar_evidencias_visita(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> VisitaEvidenciaListado:
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
                "No tiene permiso para consultar "
                "los adjuntos de esta visita."
            ),
        )

    resultados = listar_evidencias(
        db=db,
        visita_id=visita_id,
    )

    return VisitaEvidenciaListado(
        resultados=resultados,
        total=len(resultados),
    )


@router.delete(
    "/{visita_id}/evidencias/{evidencia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (soft-delete) un adjunto de una visita",
)
def eliminar_evidencia_visita(
    visita_id: int,
    evidencia_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
        )
    ),
) -> None:
    eliminar_evidencia(
        db=db,
        visita_id=visita_id,
        evidencia_id=evidencia_id,
        usuario_actual_id=usuario_actual.id,
    )
