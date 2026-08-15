from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.notificacion import Notificacion
from app.models.preferencia_notificacion import PreferenciaNotificacion
from app.models.visita import Visita
from app.repositories.notificacion_repository import (
    actualizar_notificacion,
    actualizar_preferencia,
    buscar_notificacion_por_clave,
    buscar_notificacion_por_id,
    buscar_preferencia_asesor,
    guardar_notificacion,
    guardar_preferencia,
    listar_notificaciones,
)
from app.schemas.notificacion import (
    NotificacionCrear,
    PreferenciaNotificacionActualizar,
    PreferenciaNotificacionCrear,
)
from app.services.whatsapp_service import WhatsAppService


def crear_preferencia(
    db: Session, datos: PreferenciaNotificacionCrear
) -> PreferenciaNotificacion:
    preferencia = PreferenciaNotificacion(**datos.model_dump())
    if preferencia.acepta_whatsapp:
        preferencia.fecha_consentimiento = datetime.now(timezone.utc)
    try:
        return guardar_preferencia(db, preferencia)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una preferencia equivalente para este destinatario.",
        ) from error


def modificar_preferencia(
    db: Session,
    preferencia: PreferenciaNotificacion,
    datos: PreferenciaNotificacionActualizar,
) -> PreferenciaNotificacion:
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(preferencia, campo, valor)

    ahora = datetime.now(timezone.utc)
    if cambios.get("acepta_whatsapp") is True:
        preferencia.fecha_consentimiento = ahora
        preferencia.fecha_retiro = None
        preferencia.motivo_retiro = None
    if cambios.get("acepta_whatsapp") is False:
        preferencia.fecha_retiro = ahora
    return actualizar_preferencia(db, preferencia)


def crear_notificacion(db: Session, datos: NotificacionCrear) -> Notificacion:
    existente = buscar_notificacion_por_clave(db, datos.clave_idempotencia)
    if existente:
        return existente
    notificacion = Notificacion(**datos.model_dump(mode="python"))
    try:
        return guardar_notificacion(db, notificacion)
    except IntegrityError as error:
        db.rollback()
        existente = buscar_notificacion_por_clave(db, datos.clave_idempotencia)
        if existente:
            return existente
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible registrar la notificación.",
        ) from error


def obtener_notificaciones(
    db: Session, estado: str | None = None, canal: str | None = None, limite: int = 100
) -> list[Notificacion]:
    return listar_notificaciones(db, estado=estado, canal=canal, limite=limite)


def renderizar_recordatorio_asesor(visita: Visita, asesor: Asesor) -> str:
    nombre = " ".join(
        parte for parte in [
            asesor.primer_nombre,
            asesor.segundo_nombre,
            asesor.primer_apellido,
            asesor.segundo_apellido,
        ] if parte
    )
    hora = visita.hora_inicio.strftime("%H:%M") if visita.hora_inicio else "Por confirmar"
    ubicacion = visita.direccion or "Dirección por confirmar"
    contacto = visita.contacto_nombre or "Contacto por confirmar"
    telefono = visita.telefono_contacto or "Teléfono por confirmar"
    return (
        f"Hola {nombre}.\n\n"
        "Tienes una visita programada en SICOE VISITAS.\n\n"
        f"Empresa: {visita.empresa}\n"
        f"Fecha: {visita.fecha_visita.strftime('%d/%m/%Y')}\n"
        f"Hora: {hora}\n"
        f"Servicio: {visita.servicio}\n"
        f"Dirección: {ubicacion}\n"
        f"Contacto: {contacto}\n"
        f"Teléfono: {telefono}\n\n"
        "Este mensaje corresponde a una simulación interna y todavía no fue enviado por WhatsApp."
    )


def simular_recordatorio_asesor(db: Session, visita_id: int) -> Notificacion:
    visita = db.get(Visita, visita_id)
    if visita is None or visita.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Visita no encontrada.")
    asesor = db.get(Asesor, visita.asesor_id)
    if asesor is None or asesor.deleted_at is not None or not asesor.activo:
        raise HTTPException(status_code=422, detail="La visita no tiene un asesor activo válido.")
    if not asesor.telefono:
        raise HTTPException(status_code=422, detail="El asesor no tiene teléfono registrado.")

    preferencia = buscar_preferencia_asesor(db, asesor.id, asesor.telefono)
    if preferencia is None or not preferencia.acepta_whatsapp or not preferencia.whatsapp_activo:
        raise HTTPException(
            status_code=422,
            detail="El asesor no tiene consentimiento activo para recibir WhatsApp.",
        )

    clave = f"WHATSAPP:ASESOR:VISITA:{visita.id}:24H"
    existente = buscar_notificacion_por_clave(db, clave)
    if existente:
        return existente

    mensaje = renderizar_recordatorio_asesor(visita, asesor)
    notificacion = crear_notificacion(
        db,
        NotificacionCrear(
            visita_id=visita.id,
            asesor_id=asesor.id,
            tercero_id=visita.tercero_id,
            canal="WHATSAPP",
            tipo_destinatario="ASESOR",
            telefono_destino=asesor.telefono,
            plantilla="recordatorio_visita_asesor_v1",
            datos_json={
                "visita_id": visita.id,
                "empresa": visita.empresa,
                "fecha": visita.fecha_visita.isoformat(),
                "hora": visita.hora_inicio.isoformat() if visita.hora_inicio else None,
                "servicio": visita.servicio,
            },
            mensaje_renderizado=mensaje,
            fecha_programada=datetime.now(timezone.utc),
            clave_idempotencia=clave,
        ),
    )

    resultado = WhatsAppService().enviar(asesor.telefono, mensaje)
    notificacion.intentos += 1
    notificacion.proveedor = resultado.proveedor
    notificacion.proveedor_message_id = resultado.proveedor_message_id
    notificacion.estado = resultado.estado
    notificacion.error = resultado.error
    if resultado.exitoso:
        notificacion.fecha_envio = datetime.now(timezone.utc)
    return actualizar_notificacion(db, notificacion)


def obtener_notificacion(db: Session, notificacion_id: int) -> Notificacion:
    notificacion = buscar_notificacion_por_id(db, notificacion_id)
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    return notificacion
