from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.asesor import Asesor
from app.models.tercero import Tercero
from app.models.visita import Visita
from app.repositories.notificacion_repository import (
    actualizar_notificacion,
    buscar_preferencia_asesor,
    buscar_preferencia_cliente,
)
from app.schemas.notificacion import (
    NotificacionCrear,
    PreferenciaNotificacionActualizar,
    PreferenciaNotificacionCrear,
)
from app.services.notificacion_service import (
    crear_notificacion,
    crear_preferencia,
    modificar_preferencia,
)
from app.services.whatsapp_service import WhatsAppService


def _normalizar(numero: str | None) -> str | None:
    if not numero:
        return None
    limpio = "".join(c for c in numero if c.isdigit() or c == "+")
    if limpio.startswith("00"):
        limpio = "+" + limpio[2:]
    return limpio


def _enmascarar(numero: str | None) -> str | None:
    limpio = _normalizar(numero)
    if not limpio:
        return None
    return f"***{limpio[-4:]}"


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
        "[PRUEBA INTERNA SICOE VISITAS]\n\n"
        f"Hola {_nombre_asesor(asesor)}.\n\n"
        "Tienes una visita programada.\n\n"
        f"Empresa: {visita.empresa}\n"
        f"Fecha: {visita.fecha_visita.strftime('%d/%m/%Y')}\n"
        f"Hora: {hora}\n"
        f"Servicio: {visita.servicio}\n"
        f"Dirección: {visita.direccion or 'Por confirmar'}\n\n"
        "Este mensaje fue generado en modo simulación y no fue enviado a WhatsApp."
    )


def _mensaje_cliente(visita: Visita, asesor: Asesor) -> str:
    hora = visita.hora_inicio.strftime("%H:%M") if visita.hora_inicio else "Por confirmar"
    contacto = visita.contacto_nombre or "cliente"
    return (
        "[PRUEBA INTERNA SICOE VISITAS]\n\n"
        f"Hola {contacto}.\n\n"
        "SICOE le recuerda una visita programada.\n\n"
        f"Asesor: {_nombre_asesor(asesor)}\n"
        f"Fecha: {visita.fecha_visita.strftime('%d/%m/%Y')}\n"
        f"Hora: {hora}\n"
        f"Servicio: {visita.servicio}\n\n"
        "Este mensaje fue generado en modo simulación y no fue enviado a WhatsApp."
    )


def _asegurar_preferencia_asesor(db: Session, asesor_id: int, telefono: str):
    preferencia = buscar_preferencia_asesor(db, asesor_id, telefono)
    if preferencia:
        return modificar_preferencia(
            db,
            preferencia,
            PreferenciaNotificacionActualizar(
                acepta_whatsapp=True,
                whatsapp_activo=True,
                origen_consentimiento="PILOTO_INTERNO_AUTORIZADO",
            ),
        )
    return crear_preferencia(
        db,
        PreferenciaNotificacionCrear(
            tipo_destinatario="ASESOR",
            asesor_id=asesor_id,
            telefono_whatsapp=telefono,
            acepta_whatsapp=True,
            whatsapp_activo=True,
            origen_consentimiento="PILOTO_INTERNO_AUTORIZADO",
        ),
    )


def _asegurar_preferencia_cliente(db: Session, tercero_id: int, telefono: str):
    preferencia = buscar_preferencia_cliente(db, tercero_id, telefono)
    if preferencia:
        return modificar_preferencia(
            db,
            preferencia,
            PreferenciaNotificacionActualizar(
                acepta_whatsapp=True,
                whatsapp_activo=True,
                origen_consentimiento="PILOTO_INTERNO_AUTORIZADO",
            ),
        )
    return crear_preferencia(
        db,
        PreferenciaNotificacionCrear(
            tipo_destinatario="CLIENTE",
            tercero_id=tercero_id,
            telefono_whatsapp=telefono,
            acepta_whatsapp=True,
            whatsapp_activo=True,
            origen_consentimiento="PILOTO_INTERNO_AUTORIZADO",
        ),
    )


def _simular(db: Session, datos: NotificacionCrear):
    notificacion = crear_notificacion(db, datos)
    if notificacion.estado != "PENDIENTE":
        return notificacion
    resultado = WhatsAppService().enviar(
        datos.telefono_destino or "", datos.mensaje_renderizado or ""
    )
    notificacion.intentos += 1
    notificacion.proveedor = resultado.proveedor
    notificacion.proveedor_message_id = resultado.proveedor_message_id
    notificacion.estado = resultado.estado
    notificacion.error = resultado.error
    if resultado.exitoso:
        notificacion.fecha_envio = datetime.now(timezone.utc)
    return actualizar_notificacion(db, notificacion)


def ejecutar_piloto_simulado(db: Session, visita_id: int) -> dict:
    settings = get_settings()
    if not settings.whatsapp_pilot_mode:
        raise HTTPException(
            status_code=409,
            detail="WHATSAPP_PILOT_MODE no está habilitado en el archivo .env.",
        )

    telefono_asesor = _normalizar(settings.whatsapp_pilot_asesor_number)
    telefono_cliente = _normalizar(settings.whatsapp_pilot_cliente_number)
    if not telefono_asesor or not telefono_cliente:
        raise HTTPException(
            status_code=422,
            detail="Los dos números del piloto deben estar configurados en .env.",
        )

    visita = db.get(Visita, visita_id)
    if visita is None or visita.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Visita no encontrada.")

    asesor = db.get(Asesor, visita.asesor_id)
    if asesor is None or asesor.deleted_at is not None or not asesor.activo:
        raise HTTPException(status_code=422, detail="La visita no tiene asesor activo.")
    if visita.tercero_id is None:
        raise HTTPException(status_code=422, detail="La visita no tiene tercero asociado.")
    tercero = db.get(Tercero, visita.tercero_id)
    if tercero is None or tercero.deleted_at is not None:
        raise HTTPException(status_code=422, detail="La visita no tiene tercero válido.")

    pref_asesor = _asegurar_preferencia_asesor(db, asesor.id, telefono_asesor)
    pref_cliente = _asegurar_preferencia_cliente(db, tercero.id, telefono_cliente)
    ahora = datetime.now(timezone.utc)
    marca = ahora.strftime("%Y%m%d%H%M%S")

    n_asesor = _simular(
        db,
        NotificacionCrear(
            visita_id=visita.id,
            asesor_id=asesor.id,
            tercero_id=tercero.id,
            canal="WHATSAPP",
            tipo_destinatario="ASESOR",
            telefono_destino=telefono_asesor,
            plantilla="piloto_recordatorio_asesor_v1",
            datos_json={
                "visita_id": visita.id,
                "modo_piloto": True,
                "destino_enmascarado": _enmascarar(telefono_asesor),
            },
            mensaje_renderizado=_mensaje_asesor(visita, asesor),
            fecha_programada=ahora,
            clave_idempotencia=f"PILOTO:WHATSAPP:ASESOR:VISITA:{visita.id}:{marca}",
        ),
    )

    n_cliente = _simular(
        db,
        NotificacionCrear(
            visita_id=visita.id,
            asesor_id=asesor.id,
            tercero_id=tercero.id,
            canal="WHATSAPP",
            tipo_destinatario="CLIENTE",
            telefono_destino=telefono_cliente,
            plantilla="piloto_recordatorio_cliente_v1",
            datos_json={
                "visita_id": visita.id,
                "modo_piloto": True,
                "destino_enmascarado": _enmascarar(telefono_cliente),
            },
            mensaje_renderizado=_mensaje_cliente(visita, asesor),
            fecha_programada=ahora,
            clave_idempotencia=f"PILOTO:WHATSAPP:CLIENTE:VISITA:{visita.id}:{marca}",
        ),
    )

    return {
        "modo_piloto": True,
        "envio_real": False,
        "visita_id": visita.id,
        "preferencias": {
            "asesor_id": pref_asesor.id,
            "cliente_id": pref_cliente.id,
        },
        "notificaciones": [
            {
                "id": n_asesor.id,
                "destinatario": "ASESOR",
                "telefono": _enmascarar(telefono_asesor),
                "estado": n_asesor.estado,
            },
            {
                "id": n_cliente.id,
                "destinatario": "CLIENTE",
                "telefono": _enmascarar(telefono_cliente),
                "estado": n_cliente.estado,
            },
        ],
        "mensaje": "Piloto simulado registrado. No se enviaron mensajes reales.",
    }


def encolar_piloto_n8n(db: Session, visita_id: int) -> dict:
    settings = get_settings()
    if not settings.whatsapp_pilot_mode:
        raise HTTPException(
            status_code=409,
            detail="WHATSAPP_PILOT_MODE no está habilitado en el archivo .env.",
        )

    telefono_asesor = _normalizar(settings.whatsapp_pilot_asesor_number)
    telefono_cliente = _normalizar(settings.whatsapp_pilot_cliente_number)
    if not telefono_asesor or not telefono_cliente:
        raise HTTPException(
            status_code=422,
            detail="Los dos números del piloto deben estar configurados en .env.",
        )

    visita = db.get(Visita, visita_id)
    if visita is None or visita.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Visita no encontrada.")

    asesor = db.get(Asesor, visita.asesor_id)
    if asesor is None or asesor.deleted_at is not None or not asesor.activo:
        raise HTTPException(status_code=422, detail="La visita no tiene asesor activo.")
    if visita.tercero_id is None:
        raise HTTPException(status_code=422, detail="La visita no tiene tercero asociado.")
    tercero = db.get(Tercero, visita.tercero_id)
    if tercero is None or tercero.deleted_at is not None:
        raise HTTPException(status_code=422, detail="La visita no tiene tercero válido.")

    pref_asesor = _asegurar_preferencia_asesor(db, asesor.id, telefono_asesor)
    pref_cliente = _asegurar_preferencia_cliente(db, tercero.id, telefono_cliente)
    ahora = datetime.now(timezone.utc)
    marca = ahora.strftime("%Y%m%d%H%M%S%f")

    n_asesor = crear_notificacion(
        db,
        NotificacionCrear(
            visita_id=visita.id,
            asesor_id=asesor.id,
            tercero_id=tercero.id,
            canal="WHATSAPP",
            tipo_destinatario="ASESOR",
            telefono_destino=telefono_asesor,
            plantilla="piloto_n8n_recordatorio_asesor_v1",
            datos_json={
                "visita_id": visita.id,
                "modo_piloto": True,
                "worker": "n8n",
                "destino_enmascarado": _enmascarar(telefono_asesor),
            },
            mensaje_renderizado=_mensaje_asesor(visita, asesor),
            fecha_programada=ahora,
            clave_idempotencia=f"PILOTO:N8N:WHATSAPP:ASESOR:VISITA:{visita.id}:{marca}",
        ),
    )

    n_cliente = crear_notificacion(
        db,
        NotificacionCrear(
            visita_id=visita.id,
            asesor_id=asesor.id,
            tercero_id=tercero.id,
            canal="WHATSAPP",
            tipo_destinatario="CLIENTE",
            telefono_destino=telefono_cliente,
            plantilla="piloto_n8n_recordatorio_cliente_v1",
            datos_json={
                "visita_id": visita.id,
                "modo_piloto": True,
                "worker": "n8n",
                "destino_enmascarado": _enmascarar(telefono_cliente),
            },
            mensaje_renderizado=_mensaje_cliente(visita, asesor),
            fecha_programada=ahora,
            clave_idempotencia=f"PILOTO:N8N:WHATSAPP:CLIENTE:VISITA:{visita.id}:{marca}",
        ),
    )

    return {
        "modo_piloto": True,
        "envio_real": False,
        "worker": "n8n",
        "visita_id": visita.id,
        "preferencias": {
            "asesor_id": pref_asesor.id,
            "cliente_id": pref_cliente.id,
        },
        "notificaciones": [
            {
                "id": n_asesor.id,
                "destinatario": "ASESOR",
                "telefono": _enmascarar(telefono_asesor),
                "estado": n_asesor.estado,
            },
            {
                "id": n_cliente.id,
                "destinatario": "CLIENTE",
                "telefono": _enmascarar(telefono_cliente),
                "estado": n_cliente.estado,
            },
        ],
        "mensaje": "Órdenes PENDIENTES creadas para que n8n las procese en modo simulación.",
    }
