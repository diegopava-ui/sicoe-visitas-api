from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.tercero import Tercero
from app.models.visita import Visita
from app.repositories.notificacion_repository import (
    buscar_preferencia_asesor,
    buscar_preferencia_cliente,
    cancelar_notificaciones_pendientes_visita,
)
from app.schemas.notificacion import NotificacionCrear
from app.services.notificacion_service import crear_notificacion

ZONA_COLOMBIA = ZoneInfo("America/Bogota")


@dataclass
class ResultadoProgramacion:
    visita_id: int
    creadas: list[int] = field(default_factory=list)
    omitidas: list[str] = field(default_factory=list)
    canceladas: int = 0


def _fecha_hora_visita_utc(visita: Visita) -> datetime | None:
    if visita.hora_inicio is None:
        return None

    local = datetime.combine(visita.fecha_visita, visita.hora_inicio).replace(
        tzinfo=ZONA_COLOMBIA
    )
    return local.astimezone(timezone.utc)


def _nombre_asesor(asesor: Asesor) -> str:
    return " ".join(
        parte
        for parte in (
            asesor.primer_nombre,
            asesor.segundo_nombre,
            asesor.primer_apellido,
            asesor.segundo_apellido,
        )
        if parte
    )


def _mensaje_asesor(visita: Visita, asesor: Asesor) -> str:
    hora = visita.hora_inicio.strftime("%H:%M") if visita.hora_inicio else "Por confirmar"
    return (
        f"Hola {_nombre_asesor(asesor)}.\n\n"
        "Tienes una visita programada en SICOE VISITAS.\n\n"
        f"Empresa: {visita.empresa}\n"
        f"Fecha: {visita.fecha_visita.strftime('%d/%m/%Y')}\n"
        f"Hora: {hora}\n"
        f"Servicio: {visita.servicio}\n"
        f"Dirección: {visita.direccion or 'Por confirmar'}\n"
        f"Contacto: {visita.contacto_nombre or 'Por confirmar'}\n"
        f"Teléfono: {visita.telefono_contacto or 'Por confirmar'}"
    )


def _mensaje_cliente(visita: Visita, asesor: Asesor) -> str:
    hora = visita.hora_inicio.strftime("%H:%M") if visita.hora_inicio else "Por confirmar"
    contacto = visita.contacto_nombre or "señor(a) cliente"
    return (
        f"Hola {contacto}.\n\n"
        "SICOE le recuerda una visita programada.\n\n"
        f"Asesor: {_nombre_asesor(asesor)}\n"
        f"Fecha: {visita.fecha_visita.strftime('%d/%m/%Y')}\n"
        f"Hora: {hora}\n"
        f"Servicio: {visita.servicio}\n"
        f"Duración estimada: {visita.duracion_minutos or 'Por confirmar'} minutos"
    )


def programar_notificaciones_visita(
    db: Session,
    visita: Visita,
    *,
    reemplazar_pendientes: bool = False,
) -> ResultadoProgramacion:
    resultado = ResultadoProgramacion(visita_id=visita.id)

    if reemplazar_pendientes:
        resultado.canceladas = cancelar_notificaciones_pendientes_visita(db, visita.id)

    if visita.deleted_at is not None or not visita.activo:
        resultado.omitidas.append("La visita está inactiva o eliminada.")
        return resultado

    if visita.estado != "PROGRAMADA":
        resultado.omitidas.append("La visita no está en estado PROGRAMADA.")
        return resultado

    fecha_hora_utc = _fecha_hora_visita_utc(visita)
    if fecha_hora_utc is None:
        resultado.omitidas.append("La visita no tiene hora de inicio.")
        return resultado

    fecha_programada = fecha_hora_utc - timedelta(hours=24)
    if fecha_programada <= datetime.now(timezone.utc):
        resultado.omitidas.append("El recordatorio de 24 horas ya quedó en el pasado.")
        return resultado

    asesor = db.get(Asesor, visita.asesor_id)
    if asesor is None or asesor.deleted_at is not None or not asesor.activo:
        resultado.omitidas.append("La visita no tiene un asesor activo válido.")
        return resultado

    # Recordatorio al asesor
    if asesor.telefono:
        preferencia_asesor = buscar_preferencia_asesor(db, asesor.id, asesor.telefono)
        if (
            preferencia_asesor is not None
            and preferencia_asesor.acepta_whatsapp
            and preferencia_asesor.whatsapp_activo
        ):
            notificacion = crear_notificacion(
                db,
                NotificacionCrear(
                    visita_id=visita.id,
                    asesor_id=asesor.id,
                    tercero_id=visita.tercero_id,
                    canal="WHATSAPP",
                    tipo_destinatario="ASESOR",
                    telefono_destino=asesor.telefono,
                    plantilla="recordatorio_visita_asesor_24h_v1",
                    datos_json={
                        "visita_id": visita.id,
                        "empresa": visita.empresa,
                        "fecha": visita.fecha_visita.isoformat(),
                        "hora": visita.hora_inicio.isoformat(),
                        "servicio": visita.servicio,
                        "anticipacion_horas": 24,
                    },
                    mensaje_renderizado=_mensaje_asesor(visita, asesor),
                    fecha_programada=fecha_programada,
                    clave_idempotencia=(
                        f"WHATSAPP:ASESOR:VISITA:{visita.id}:24H:"
                        f"{visita.fecha_visita.isoformat()}:{visita.hora_inicio.isoformat()}"
                    ),
                ),
            )
            resultado.creadas.append(notificacion.id)
        else:
            resultado.omitidas.append(
                "El asesor no tiene consentimiento WhatsApp activo."
            )
    else:
        resultado.omitidas.append("El asesor no tiene teléfono registrado.")

    # Recordatorio al cliente
    tercero = db.get(Tercero, visita.tercero_id) if visita.tercero_id else None
    telefono_cliente = visita.telefono_contacto or (
        tercero.contacto_telefono if tercero else None
    )
    if tercero is not None and telefono_cliente:
        preferencia_cliente = buscar_preferencia_cliente(
            db, tercero.id, telefono_cliente
        )
        if (
            preferencia_cliente is not None
            and preferencia_cliente.acepta_whatsapp
            and preferencia_cliente.whatsapp_activo
        ):
            notificacion = crear_notificacion(
                db,
                NotificacionCrear(
                    visita_id=visita.id,
                    asesor_id=asesor.id,
                    tercero_id=tercero.id,
                    canal="WHATSAPP",
                    tipo_destinatario="CLIENTE",
                    telefono_destino=telefono_cliente,
                    plantilla="recordatorio_visita_cliente_24h_v1",
                    datos_json={
                        "visita_id": visita.id,
                        "empresa": visita.empresa,
                        "fecha": visita.fecha_visita.isoformat(),
                        "hora": visita.hora_inicio.isoformat(),
                        "servicio": visita.servicio,
                        "anticipacion_horas": 24,
                    },
                    mensaje_renderizado=_mensaje_cliente(visita, asesor),
                    fecha_programada=fecha_programada,
                    clave_idempotencia=(
                        f"WHATSAPP:CLIENTE:VISITA:{visita.id}:24H:"
                        f"{visita.fecha_visita.isoformat()}:{visita.hora_inicio.isoformat()}"
                    ),
                ),
            )
            resultado.creadas.append(notificacion.id)
        else:
            resultado.omitidas.append(
                "El cliente no tiene consentimiento WhatsApp activo."
            )
    else:
        resultado.omitidas.append("El cliente no tiene teléfono válido.")

    return resultado
