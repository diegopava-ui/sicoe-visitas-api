from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.repositories.notificacion_repository import (
    buscar_notificacion_por_id,
    guardar_resultado_worker,
    tomar_notificacion_para_proceso,
)
from app.schemas.notificacion import NotificacionResultadoWorker


def iniciar_procesamiento_notificacion(
    db: Session, notificacion_id: int
) -> Notificacion:
    existente = buscar_notificacion_por_id(db, notificacion_id)
    if existente is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    if existente.estado != "PENDIENTE":
        raise HTTPException(
            status_code=409,
            detail=f"La notificación no está PENDIENTE. Estado actual: {existente.estado}.",
        )

    notificacion = tomar_notificacion_para_proceso(db, notificacion_id)
    if notificacion is None:
        raise HTTPException(
            status_code=409,
            detail="La notificación fue tomada por otro proceso o cambió de estado.",
        )
    return notificacion


def registrar_resultado_notificacion(
    db: Session,
    notificacion_id: int,
    datos: NotificacionResultadoWorker,
) -> Notificacion:
    notificacion = buscar_notificacion_por_id(db, notificacion_id)
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    if notificacion.estado != "PROCESANDO":
        raise HTTPException(
            status_code=409,
            detail=f"La notificación no está PROCESANDO. Estado actual: {notificacion.estado}.",
        )
    if datos.estado == "FALLIDA" and not datos.error:
        raise HTTPException(
            status_code=422,
            detail="El campo error es obligatorio cuando el estado es FALLIDA.",
        )

    return guardar_resultado_worker(
        db,
        notificacion,
        estado=datos.estado.value,
        proveedor=datos.proveedor,
        proveedor_message_id=datos.proveedor_message_id,
        error=datos.error,
        respuesta=datos.respuesta,
    )
