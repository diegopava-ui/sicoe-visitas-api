from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.visita_repository import (
    actualizar_visita as actualizar_visita_repository,
    buscar_visita_por_id,
)
from app.schemas.ubicacion import (
    UbicacionValidacionRespuesta,
    UbicacionValidar,
)


def validar_ubicacion_visita(
    db: Session,
    visita_id: int,
    datos: UbicacionValidar,
    usuario_actual: Usuario,
) -> UbicacionValidacionRespuesta:
    visita = buscar_visita_por_id(
        db,
        visita_id,
    )

    if visita is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada.",
        )

    if not visita.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede validar la ubicación "
                "de una visita inactiva."
            ),
        )

    if usuario_actual.rol == "ASESOR":
        if usuario_actual.asesor_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El usuario asesor no tiene "
                    "un asesor asociado."
                ),
            )

        if visita.asesor_id != usuario_actual.asesor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tiene permiso para validar "
                    "la ubicación de esta visita."
                ),
            )

    if visita.ubicacion_validada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La ubicación de esta visita ya fue validada. "
                "La revalidación se habilitará mediante "
                "un flujo de auditoría específico."
            ),
        )

    latitud_resultante = (
        datos.latitud
        if datos.latitud is not None
        else visita.latitud
    )

    longitud_resultante = (
        datos.longitud
        if datos.longitud is not None
        else visita.longitud
    )

    if (
        latitud_resultante is None
        or longitud_resultante is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La visita no tiene coordenadas completas. "
                "Envíe latitud y longitud para poder validarla."
            ),
        )

    fecha_validacion = datetime.now(timezone.utc)

    visita.latitud = latitud_resultante
    visita.longitud = longitud_resultante
    visita.fuente_ubicacion = datos.fuente_ubicacion
    visita.ubicacion_validada = True
    visita.ubicacion_validada_at = fecha_validacion
    visita.ubicacion_validada_by = usuario_actual.id

    # Mantener la auditoría general de la visita sincronizada.
    visita.updated_by = usuario_actual.id
    visita.updated_at = fecha_validacion

    try:
        visita_actualizada = actualizar_visita_repository(
            db,
            visita,
        )

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No fue posible validar la ubicación. "
                "Verifique los datos proporcionados."
            ),
        ) from exc

    return UbicacionValidacionRespuesta(
        visita_id=visita_actualizada.id,
        latitud=visita_actualizada.latitud,
        longitud=visita_actualizada.longitud,
        fuente_ubicacion=visita_actualizada.fuente_ubicacion,
        ubicacion_validada=visita_actualizada.ubicacion_validada,
        ubicacion_validada_at=visita_actualizada.ubicacion_validada_at,
        ubicacion_validada_by=visita_actualizada.ubicacion_validada_by,
        mensaje="Ubicación validada correctamente.",
    )
